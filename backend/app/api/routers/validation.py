import json
import os
import queue
import threading
from typing import Literal, cast
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, Response, StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db, get_session_factory
from app.core.security import get_current_user_id
from app.schemas.validation import (
    CriterionRunOut,
    ValidationJobCreatedOut,
    ValidationJobStatusOut,
    ValidationUploadResponse,
)
from app.services.file_ingest import read_uploaded_table
from app.services.validation_jobs import get_job, spawn_validation_job, try_register_job
from app.services.validation_runner import (
    build_creadores_output_zip_bytes,
    dataframe_preview_json,
    iter_validation_sse_events,
    run_validation,
)

router = APIRouter(prefix="/validation", tags=["validation"])


def _safe_unlink(path: str) -> None:
    try:
        if path and os.path.isfile(path):
            os.unlink(path)
    except OSError:
        pass


def _sse_line(payload: dict) -> str:
    return f"data: {json.dumps(payload, default=str)}\n\n"


_SSE_DONE = object()


@router.post(
    "/upload-stream",
    summary="Validación con progreso (SSE): criterio y paso en tiempo casi real",
)
def upload_and_validate_stream(
    program_id: UUID = Form(..., description="ID del programa / oportunidad en BD"),
    file: UploadFile = File(..., description="Archivo .csv, .xlsx o .xls"),
    _user_id: str = Depends(get_current_user_id),
) -> StreamingResponse:
    """
    La validación corre en un hilo con su propia sesión SQLAlchemy; el generador principal
    envía comentarios SSE (: keepalive) mientras espera, para que proxies (Railway, etc.)
    no cierren la conexión por inactividad durante pasos largos (Apify, YouTube, …).
    """

    def event_gen():
        try:
            df = read_uploaded_table(file)
        except ValueError as e:
            yield _sse_line({"type": "error", "message": str(e)})
            return

        q: queue.Queue[object] = queue.Queue(maxsize=128)

        def worker() -> None:
            try:
                SessionLocal = get_session_factory()
                db_worker = SessionLocal()
                try:
                    for ev in iter_validation_sse_events(db_worker, program_id, df):
                        q.put(ev)
                finally:
                    db_worker.close()
            except Exception as e:  # noqa: BLE001
                q.put({"type": "error", "message": str(e)})
            finally:
                q.put(_SSE_DONE)

        threading.Thread(target=worker, name="validation-sse", daemon=True).start()

        timeout = max(1.0, float(settings.validation_sse_keepalive_seconds))
        while True:
            try:
                item = q.get(timeout=timeout)
            except queue.Empty:
                # Línea de comentario SSE: no dispara JSON en el cliente, mantiene el chunk stream vivo.
                yield ": keepalive\n\n"
                continue
            if item is _SSE_DONE:
                break
            ev = item
            assert isinstance(ev, dict)
            yield _sse_line(ev)
            if ev.get("type") == "error":
                break

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/jobs",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Encolar validación (JSON o ZIP): ideal para corridas de muchas horas",
)
def enqueue_validation_job(
    program_id: UUID = Form(..., description="ID del programa / oportunidad en BD"),
    file: UploadFile = File(..., description="Archivo .csv, .xlsx o .xls"),
    response_mode: str = Form(
        "json",
        description='Salida: "json" (preview en GET status) o "zip" (descarga vía GET .../download).',
    ),
    _user_id: str = Depends(get_current_user_id),
) -> ValidationJobCreatedOut:
    """
    Devuelve al instante un `job_id`. El cliente consulta GET /validation/jobs/{job_id}
    cada `poll_interval_seconds` hasta `status=complete|error`, sin mantener una conexión
    larga (evita timeouts de proxy ~1 h).
    """
    mode = (response_mode or "json").strip().lower()
    if mode not in ("json", "zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='response_mode debe ser "json" o "zip".',
        )
    mode_typed = cast(Literal["json", "zip"], mode)
    try:
        df = read_uploaded_table(file)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    job = try_register_job(program_id, mode_typed)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Hay demasiadas validaciones en ejecución en este servidor. "
                "Reintenta en unos minutos o sube el límite VALIDATION_ASYNC_MAX_CONCURRENT."
            ),
        )
    spawn_validation_job(job, df.copy())
    return ValidationJobCreatedOut(
        job_id=job.job_id,
        poll_interval_seconds=float(settings.validation_job_poll_interval_seconds),
    )


@router.get(
    "/jobs/{job_id}",
    summary="Estado de validación asíncrona (progreso y resultado)",
)
def get_validation_job_status(
    job_id: UUID,
    _user_id: str = Depends(get_current_user_id),
) -> ValidationJobStatusOut:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job no encontrado o expirado.")

    result: ValidationUploadResponse | None = None
    if job.status == "complete" and job.response_mode == "json" and job.result is not None:
        result = ValidationUploadResponse.model_validate(job.result)

    download_ready = bool(
        job.status == "complete" and job.response_mode == "zip" and job.zip_path and os.path.isfile(job.zip_path)
    )

    return ValidationJobStatusOut(
        job_id=job.job_id,
        status=job.status,
        response_mode=job.response_mode,
        events_tail=job.snapshot_tail(),
        result=result,
        summary=job.summary,
        download_ready=download_ready,
        error_message=job.error_message,
    )


@router.get(
    "/jobs/{job_id}/download",
    summary="Descargar ZIP cuando el job (response_mode=zip) haya terminado",
)
def download_validation_job_zip(
    job_id: UUID,
    background_tasks: BackgroundTasks,
    _user_id: str = Depends(get_current_user_id),
) -> FileResponse:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job no encontrado o expirado.")
    if job.response_mode != "zip":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este job no es de tipo zip.",
        )
    if job.status != "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La validación aún no ha terminado.",
        )
    path = job.zip_path
    if not path or not os.path.isfile(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El archivo ya no está disponible (descargado o expirado).",
        )
    job.zip_path = None
    background_tasks.add_task(_safe_unlink, path)
    return FileResponse(
        path,
        filename="creadores_resultado.zip",
        media_type="application/zip",
    )


@router.post(
    "/upload",
    response_model=None,
    summary="Subir CSV/Excel y ejecutar validación según programa",
)
def upload_and_validate(
    program_id: UUID = Form(..., description="ID del programa / oportunidad en BD"),
    file: UploadFile = File(..., description="Archivo .csv, .xlsx o .xls"),
    response_mode: str = Form(
        "json",
        description='Salida: "json" (preview API) o "zip" (creadores_validos.xlsx + creadores_excluidos.xlsx).',
    ),
    db: Session = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
) -> ValidationUploadResponse | Response:
    try:
        df = read_uploaded_table(file)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    try:
        out_df, ex_df, blocks, program_nombre = run_validation(db, program_id, df)
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e

    mode = (response_mode or "json").strip().lower()
    if mode == "zip":
        payload = build_creadores_output_zip_bytes(out_df, ex_df)
        return Response(
            content=payload,
            media_type="application/zip",
            headers={
                "Content-Disposition": 'attachment; filename="creadores_resultado.zip"',
            },
        )

    n_ex = len(ex_df) if ex_df is not None else 0
    criteria = [CriterionRunOut.model_validate(b) for b in blocks]
    return ValidationUploadResponse(
        program_id=program_id,
        program_nombre=program_nombre,
        rows=len(out_df),
        excluded_rows=n_ex,
        columns=list(out_df.columns.astype(str)),
        criteria=criteria,
        preview=dataframe_preview_json(out_df, max_rows=settings.validation_preview_max_rows),
        excluded_preview=dataframe_preview_json(ex_df, max_rows=settings.validation_preview_max_rows)
        if ex_df is not None and n_ex
        else [],
        preview_truncated=len(out_df) > settings.validation_preview_max_rows,
        excluded_preview_truncated=n_ex > settings.validation_preview_max_rows,
    )
