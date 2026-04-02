"""
Funciones invocadas por `criterion_steps.funcion_a_ejecutar`.
Deben estar registradas en `app.utils.step_registry`.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.constants.creator_file_columns import CREATOR_FILE_COLUMNS, CREATOR_NAME_STEP_COLUMNS
from app.services.validation_context import ValidationContext
from app.utils.name_cleaning import normalize_creator_names


def _log(ctx: ValidationContext, step_key: str, message: str, **extra: Any) -> None:
    ctx.logs.append({"funcion": step_key, "message": message, **extra})


def load_creator_columns(ctx: ValidationContext) -> ValidationContext:
    """Paso 1 típico: validar que existen las columnas estándar del archivo."""
    key = "load_creator_columns"
    missing = [c for c in CREATOR_FILE_COLUMNS if c not in ctx.df.columns]
    if missing:
        _log(ctx, key, "Faltan columnas obligatorias en el archivo.", missing=missing)
        raise ValueError(
            f"El archivo no incluye todas las columnas requeridas. Faltan: {missing}"
        )
    _log(ctx, key, "Todas las columnas estándar están presentes.", ok=True)
    return ctx


def extract_best_name_source(ctx: ValidationContext) -> ValidationContext:
    """Paso 2: comprobar columnas mínimas para limpieza de nombre."""
    key = "extract_best_name_source"
    miss = [c for c in CREATOR_NAME_STEP_COLUMNS if c not in ctx.df.columns]
    if miss:
        _log(ctx, key, "Faltan columnas para extracción de nombre.", missing=miss)
        raise ValueError(f"Faltan columnas para el criterio de nombre: {miss}")
    _log(ctx, key, "Fuentes de nombre disponibles (full_name, email, username, bio).", ok=True)
    return ctx


def apply_name_parser(ctx: ValidationContext) -> ValidationContext:
    """
    Paso 3: normaliza full_name y first_name (python-nameparser + pandas).
    Añade la columna name_cleaning_source (full_name | email_local | instagram_bio | ...).
    """
    key = "apply_name_parser"
    df, stats = normalize_creator_names(ctx.df)
    _log(
        ctx,
        key,
        "Nombres normalizados con nameparser y reglas de limpieza.",
        ok=True,
        **stats,
    )
    ctx.df = df
    return ctx


def process_full_dataframe(ctx: ValidationContext) -> ValidationContext:
    """Paso 4: cierre del criterio sobre el DataFrame completo."""
    key = "process_full_dataframe"
    _log(
        ctx,
        key,
        f"Procesamiento de lista completa ({len(ctx.df)} filas).",
        rows=int(len(ctx.df)),
        ok=True,
    )
    return ctx
