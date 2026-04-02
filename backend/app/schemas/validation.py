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
        description="Todas las filas de creadores válidos (post-validación), para vista y export en cliente."
    )
    excluded_preview: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Todas las filas excluidas (si hay), con exclusion_stage / exclusion_reason.",
    )
