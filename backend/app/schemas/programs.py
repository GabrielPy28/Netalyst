from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


CREATOR_FAST_TRACK_DESCRIPTION = (
    "Programa de aceleración para creadores elegibles de Meta. "
    "Permite al equipo aplicar criterios de validación y limpieza de datos "
    "sobre listados de creadores según las reglas definidas para esta oportunidad."
)


class ProgramCreate(BaseModel):
    """Alta de cabecera de programa / oportunidad (sin criterios: los carga el equipo técnico en BD)."""

    nombre: str = Field(min_length=1, max_length=500)
    descripcion: str | None = None
    brand: str | None = Field(None, max_length=500)
    image_brand_url: str | None = Field(None, max_length=2000)
    is_active: bool = True

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "nombre": "Creator Fast Track Program",
                    "descripcion": CREATOR_FAST_TRACK_DESCRIPTION,
                    "brand": "Meta",
                    "image_brand_url": "https://img.logo.dev/name/Meta.com?token=pk_KRXikYhlQQ-D2W-TJmOjlQ&format=png&retina=true",
                    "is_active": True,
                }
            ]
        }
    )


class ProgramUpdate(BaseModel):
    """
    Actualización parcial de la cabecera del programa.
    Criterios (`criteria`) y pasos (`criterion_steps`) no se modifican aquí; los gestiona el backend vía BD.
    """

    nombre: str | None = Field(None, min_length=1, max_length=500)
    descripcion: str | None = None
    brand: str | None = Field(None, max_length=500)
    image_brand_url: str | None = Field(None, max_length=2000)
    is_active: bool | None = None


class CriterionStepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    paso_num: int
    nombre: str
    definicion: str | None
    funcion_a_ejecutar: str


class CriterionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    objetivo: str | None = None
    template_slug: str | None = None
    orden: int
    steps: list[CriterionStepOut] = Field(default_factory=list)


class ProgramOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    brand: str | None = None
    image_brand_url: str | None = None
    descripcion: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    criteria: list[CriterionOut] = Field(default_factory=list)


class ProgramListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    brand: str | None = None
    image_brand_url: str | None = None
    descripcion: str | None = None
    is_active: bool = True
    criterios_count: int = Field(
        default=0,
        description="Número de criterios enlazados al programa.",
    )


class CriterionCatalogStepOut(BaseModel):
    paso_num: int
    nombre: str
    definicion: str
    funcion_a_ejecutar: str


class CriterionCatalogItemOut(BaseModel):
    slug: str
    nombre: str
    objetivo: str
    entrega_usuario: str
    salida_esperada: str
    steps: list[CriterionCatalogStepOut] = Field(default_factory=list)


class ProgramReplaceFlow(BaseModel):
    """Reemplaza todos los criterios del programa por plantillas del catálogo (mismo orden que la lista)."""

    criterio_slugs: list[str] = Field(
        ...,
        min_length=1,
        description="Plantillas del catálogo en orden de ejecución.",
    )


class ProgramCreateFromFlow(BaseModel):
    """Alta de programa eligiendo plantillas de criterio del catálogo (orden = orden de la lista)."""

    nombre: str = Field(min_length=1, max_length=500)
    descripcion: str | None = None
    brand: str | None = Field(None, max_length=500)
    image_brand_url: str | None = Field(None, max_length=2000)
    is_active: bool = True
    criterio_slugs: list[str] = Field(
        ...,
        min_length=1,
        description="IDs de plantilla del catálogo, en el orden de ejecución deseado.",
    )
