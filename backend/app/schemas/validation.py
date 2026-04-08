from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PasoEjecutadoOut(BaseModel):
    paso_num: int
    nombre: str
    funcion_a_ejecutar: str


class CriterionRunOut(BaseModel):
    criterion_id: UUID
    criterion_nombre: str
    objetivo: str | None
    orden: int
    pasos_ejecutados: list[PasoEjecutadoOut]
    logs: list[dict[str, Any]]


class ValidationUploadResponse(BaseModel):
    program_id: UUID
    program_nombre: str
    rows: int
    excluded_rows: int = Field(
        default=0,
        description="Filas movidas a creadores_excluidos con exclusion_stage / exclusion_reason.",
    )
    columns: list[str]
    criteria: list[CriterionRunOut]
    preview: list[dict[str, Any]] = Field(
        description="Preview de filas válidas (puede truncarse para evitar payloads excesivos)."
    )
    excluded_preview: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Preview de filas excluidas (puede truncarse para evitar payloads excesivos).",
    )
    preview_truncated: bool = Field(
        default=False,
        description="True si preview no incluye todas las filas válidas.",
    )
    excluded_preview_truncated: bool = Field(
        default=False,
        description="True si excluded_preview no incluye todas las filas excluidas.",
    )
