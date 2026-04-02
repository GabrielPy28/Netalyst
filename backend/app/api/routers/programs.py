from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.constants.criterion_catalog import CRITERION_CATALOG, catalog_by_slug
from app.core.db import get_db
from app.core.security import get_current_user_id
from app.models.db_models import Criterion, CriterionStep, Program
from app.schemas.programs import (
    CriterionCatalogItemOut,
    ProgramCreate,
    ProgramCreateFromFlow,
    ProgramListItemOut,
    ProgramOut,
    ProgramReplaceFlow,
    ProgramUpdate,
)
from app.services.validation_runner import load_program_with_tree
from app.utils.step_registry import STEP_REGISTRY

router = APIRouter(prefix="/programs", tags=["programs"])


def _validate_criterio_slugs(criterio_slugs: list[str]) -> None:
    catalog = catalog_by_slug()
    seen: set[str] = set()
    for slug in criterio_slugs:
        if slug not in catalog:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plantilla de criterio desconocida: {slug!r}.",
            )
        if slug in seen:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El slug {slug!r} está repetido en criterio_slugs.",
            )
        seen.add(slug)
        for st in catalog[slug]["steps"]:
            fn = st["funcion_a_ejecutar"]
            if fn not in STEP_REGISTRY:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Paso no registrado en el backend: {fn!r}.",
                )


def _insert_criteria_from_slugs(
    db: Session,
    program_id: UUID,
    criterio_slugs: list[str],
) -> None:
    catalog = catalog_by_slug()
    for orden, slug in enumerate(criterio_slugs, start=1):
        tpl = catalog[slug]
        criterion = Criterion(
            program_id=program_id,
            nombre=tpl["nombre"],
            objetivo=tpl["objetivo"],
            template_slug=slug,
            orden=orden,
        )
        db.add(criterion)
        db.flush()
        for st in tpl["steps"]:
            db.add(
                CriterionStep(
                    criterion_id=criterion.id,
                    paso_num=st["paso_num"],
                    nombre=st["nombre"],
                    definicion=st["definicion"],
                    funcion_a_ejecutar=st["funcion_a_ejecutar"],
                )
            )


@router.get(
    "/criterion-catalog",
    response_model=list[CriterionCatalogItemOut],
    summary="Plantillas de criterios para armar el flujo de un programa",
)
def list_criterion_catalog(
    _user_id: str = Depends(get_current_user_id),
) -> list[dict]:
    return list(CRITERION_CATALOG)


@router.post(
    "/from-flow",
    response_model=ProgramOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear programa con criterios desde el catálogo (orden = orden de ejecución)",
)
def create_program_from_flow(
    payload: ProgramCreateFromFlow,
    db: Session = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
) -> Program:
    _validate_criterio_slugs(payload.criterio_slugs)

    program = Program(
        nombre=payload.nombre,
        descripcion=payload.descripcion,
        brand=payload.brand,
        image_brand_url=payload.image_brand_url,
        is_active=payload.is_active,
    )
    db.add(program)
    db.flush()
    _insert_criteria_from_slugs(db, program.id, payload.criterio_slugs)

    db.commit()
    full = load_program_with_tree(db, program.id, require_active=False)
    assert full is not None
    return full


@router.post(
    "",
    response_model=ProgramOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar programa / oportunidad",
)
def create_program(
    payload: ProgramCreate,
    db: Session = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
) -> Program:
    program = Program(**payload.model_dump())
    db.add(program)
    db.commit()
    db.refresh(program)
    full = load_program_with_tree(db, program.id, require_active=False)
    assert full is not None
    return full


@router.get("", response_model=list[ProgramListItemOut])
def list_programs(
    db: Session = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
) -> list[ProgramListItemOut]:
    stmt = (
        select(Program)
        .options(selectinload(Program.criteria))
        .where(Program.is_active.is_(True))
        .order_by(Program.nombre)
    )
    rows = list(db.execute(stmt).scalars().all())
    return [
        ProgramListItemOut(
            id=p.id,
            nombre=p.nombre,
            brand=p.brand,
            image_brand_url=p.image_brand_url,
            descripcion=p.descripcion,
            is_active=p.is_active,
            criterios_count=len(p.criteria),
        )
        for p in rows
    ]


@router.put(
    "/{program_id}/flow",
    response_model=ProgramOut,
    summary="Reemplazar criterios del programa desde el catálogo",
)
def replace_program_flow(
    program_id: UUID,
    payload: ProgramReplaceFlow,
    db: Session = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
) -> Program:
    program = db.get(Program, program_id)
    if program is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programa no encontrado.",
        )
    _validate_criterio_slugs(payload.criterio_slugs)
    db.execute(delete(Criterion).where(Criterion.program_id == program_id))
    db.flush()
    _insert_criteria_from_slugs(db, program_id, payload.criterio_slugs)
    db.commit()
    full = load_program_with_tree(db, program_id, require_active=False)
    assert full is not None
    return full


@router.get("/{program_id}", response_model=ProgramOut)
def get_program(
    program_id: UUID,
    db: Session = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
) -> Program:
    program = load_program_with_tree(db, program_id, require_active=False)
    if program is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programa no encontrado.",
        )
    return program


@router.patch(
    "/{program_id}",
    response_model=ProgramOut,
    summary="Actualizar cabecera del programa",
)
def update_program(
    program_id: UUID,
    payload: ProgramUpdate,
    db: Session = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
) -> Program:
    program = db.get(Program, program_id)
    if program is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programa no encontrado.",
        )
    data = payload.model_dump(exclude_unset=True)
    if not data:
        full = load_program_with_tree(db, program_id, require_active=False)
        assert full is not None
        return full
    for key, value in data.items():
        setattr(program, key, value)
    db.commit()
    full = load_program_with_tree(db, program_id, require_active=False)
    assert full is not None
    return full


@router.delete(
    "/{program_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar programa de forma permanente",
)
def delete_program(
    program_id: UUID,
    db: Session = Depends(get_db),
    _user_id: str = Depends(get_current_user_id),
) -> None:
    program = db.get(Program, program_id)
    if program is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programa no encontrado.",
        )
    db.delete(program)
    db.commit()
