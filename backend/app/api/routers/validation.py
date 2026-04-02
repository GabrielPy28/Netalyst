import json
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user_id
from app.schemas.validation import CriterionRunOut, ValidationUploadResponse
from app.services.file_ingest import read_uploaded_table
from app.services.validation_runner import (
    build_creadores_output_zip_bytes,
    dataframe_preview_json,
    iter_validation_sse_events,
    run_validation,
)

router = APIRouter(prefix="/validation", tags=["validation"])


def _sse_line(payload: dict) -> str:
    return f"data: {json.dumps(payload, default=str)}\n\n"


@router.post(
    "/upload-stream",
    summary="Validación con progreso (SSE): criterio y paso en tiempo casi real",
)
def upload_and_validate_stream(
    program_id: UUID = Form(..., description="ID del programa / oportunidad en BD"),
    file: UploadFile = File(..., description="Archivo .csv, .xlsx o .xls"),
    db: Session = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
) -> StreamingResponse:
    def event_gen():
        try:
            df = read_uploaded_table(file)
        except ValueError as e:
            yield _sse_line({"type": "error", "message": str(e)})
            return
        try:
            for ev in iter_validation_sse_events(db, program_id, df):
                yield _sse_line(ev)
                if ev.get("type") in ("error",):
                    return
        except Exception as e:  # noqa: BLE001
            yield _sse_line({"type": "error", "message": str(e)})

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
        preview=dataframe_preview_json(out_df),
        excluded_preview=dataframe_preview_json(ex_df) if ex_df is not None and n_ex else [],
    )
