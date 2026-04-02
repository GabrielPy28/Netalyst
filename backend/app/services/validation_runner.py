"""Ejecuta criterios y pasos de un programa sobre un DataFrame."""

from __future__ import annotations

import io
import json
import zipfile
from collections.abc import Iterator
from typing import Any
from uuid import UUID

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.db_models import Criterion, CriterionStep, Program
from app.services.validation_context import ValidationContext
from app.utils.step_registry import get_step_function


def load_program_with_tree(
    db: Session,
    program_id: UUID,
    *,
    require_active: bool = True,
) -> Program | None:
    stmt = select(Program).where(Program.id == program_id)
    if require_active:
        stmt = stmt.where(Program.is_active.is_(True))
    stmt = stmt.options(
        selectinload(Program.criteria).selectinload(Criterion.steps),
    )
    return db.execute(stmt).scalar_one_or_none()


def _step_log_tail(logs: list[dict[str, Any]], *, max_items: int = 8) -> list[dict[str, Any]]:
    if not logs:
        return []
    return list(logs[-max_items:])


def _run_pipeline_events(
    ctx: ValidationContext,
    program: Program,
) -> Iterator[dict[str, Any]]:
    """
    Ejecuta criterios y pasos; emite eventos para SSE.
    Termina con {"type": "_internal_done", "criteria_results": [...]} (no enviar al cliente).
    """
    criteria_results: list[dict[str, Any]] = []
    criteria_sorted = sorted(program.criteria, key=lambda c: c.orden)

    for criterion in criteria_sorted:
        yield {
            "type": "criterion_start",
            "criterion_id": str(criterion.id),
            "criterion_nombre": criterion.nombre,
            "orden": criterion.orden,
        }

        ctx.criterion_id = str(criterion.id)
        ctx.criterion_nombre = criterion.nombre
        ctx.logs = []
        ctx.pipeline_cache = {}

        steps_sorted: list[CriterionStep] = sorted(
            criterion.steps, key=lambda s: s.paso_num
        )
        for step in steps_sorted:
            yield {
                "type": "step_start",
                "criterion_nombre": criterion.nombre,
                "criterion_orden": criterion.orden,
                "paso_num": step.paso_num,
                "step_nombre": step.nombre,
                "funcion_a_ejecutar": step.funcion_a_ejecutar,
            }
            fn = get_step_function(step.funcion_a_ejecutar)
            ctx = fn(ctx)
            tail = _step_log_tail(ctx.logs)
            last_ok = all(x.get("ok", True) for x in tail) if tail else True
            yield {
                "type": "step_done",
                "criterion_nombre": criterion.nombre,
                "criterion_orden": criterion.orden,
                "paso_num": step.paso_num,
                "step_nombre": step.nombre,
                "funcion_a_ejecutar": step.funcion_a_ejecutar,
                "ok": last_ok,
                "logs_tail": tail,
            }

        criteria_results.append(
            {
                "criterion_id": str(criterion.id),
                "criterion_nombre": criterion.nombre,
                "objetivo": criterion.objetivo,
                "orden": criterion.orden,
                "pasos_ejecutados": [
                    {
                        "paso_num": s.paso_num,
                        "nombre": s.nombre,
                        "funcion_a_ejecutar": s.funcion_a_ejecutar,
                    }
                    for s in steps_sorted
                ],
                "logs": list(ctx.logs),
            }
        )

    yield {"type": "_internal_done", "criteria_results": criteria_results}


def run_validation(
    db: Session,
    program_id: UUID,
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame | None, list[dict[str, Any]], str]:
    program = load_program_with_tree(db, program_id)
    if program is None:
        raise LookupError("Programa no encontrado o inactivo.")

    ctx = ValidationContext(df=df.copy(), program_id=str(program.id), df_excluded=None)
    criteria_results: list[dict[str, Any]] = []

    for ev in _run_pipeline_events(ctx, program):
        if ev.get("type") == "_internal_done":
            criteria_results = ev["criteria_results"]

    return ctx.df, ctx.df_excluded, criteria_results, program.nombre


def iter_validation_sse_events(
    db: Session,
    program_id: UUID,
    df: pd.DataFrame,
) -> Iterator[dict[str, Any]]:
    """
    Mismo pipeline que run_validation, pero emite eventos públicos y al final un type=complete
    con el mismo contenido que la respuesta JSON de /validation/upload (serializable).
    """
    program = load_program_with_tree(db, program_id)
    if program is None:
        yield {"type": "error", "message": "Programa no encontrado o inactivo."}
        return

    ctx = ValidationContext(df=df.copy(), program_id=str(program.id), df_excluded=None)
    criteria_results: list[dict[str, Any]] = []

    try:
        for ev in _run_pipeline_events(ctx, program):
            if ev.get("type") == "_internal_done":
                criteria_results = ev["criteria_results"]
                continue
            yield ev
    except LookupError as e:
        yield {"type": "error", "message": str(e)}
        return
    except ValueError as e:
        yield {"type": "error", "message": str(e)}
        return
    except KeyError as e:
        yield {"type": "error", "message": f"Paso no registrado en el backend: {e!r}"}
        return
    except Exception as e:  # noqa: BLE001
        yield {"type": "error", "message": str(e)}
        return

    n_ex = len(ctx.df_excluded) if ctx.df_excluded is not None else 0
    yield {
        "type": "complete",
        "program_id": str(program_id),
        "program_nombre": program.nombre,
        "rows": len(ctx.df),
        "excluded_rows": n_ex,
        "columns": list(ctx.df.columns.astype(str)),
        "criteria": criteria_results,
        "preview": dataframe_preview_json(ctx.df),
        "excluded_preview": dataframe_preview_json(ctx.df_excluded)
        if ctx.df_excluded is not None and n_ex
        else [],
    }


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Datos", index=False)
    return buf.getvalue()


def build_creadores_output_zip_bytes(
    valid_df: pd.DataFrame,
    excluded_df: pd.DataFrame | None,
) -> bytes:
    """ZIP con creadores_validos.xlsx y creadores_excluidos.xlsx."""
    if excluded_df is None or len(excluded_df) == 0:
        cols = list(valid_df.columns) + ["exclusion_stage", "exclusion_reason"]
        excluded_df = pd.DataFrame(columns=cols)
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("creadores_validos.xlsx", dataframe_to_excel_bytes(valid_df))
        zf.writestr("creadores_excluidos.xlsx", dataframe_to_excel_bytes(excluded_df))
    return zip_buf.getvalue()


def dataframe_preview_json(
    df: pd.DataFrame,
    max_rows: int | None = None,
) -> list[dict[str, Any]]:
    """
    Serializa filas a JSON-friendly dicts.
    max_rows=None incluye todas las filas (p. ej. para UI + descarga sin re-ejecutar validación).
    """
    if df.empty:
        return []
    chunk = df if max_rows is None else df.head(max_rows)
    return json.loads(chunk.to_json(orient="records", date_format="iso"))
