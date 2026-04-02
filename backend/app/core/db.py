from collections.abc import Generator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import HTTPException, status
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

_engine = None
_SessionLocal: sessionmaker[Session] | None = None

# psycopg2 no acepta en el DSN opciones que Supabase añade para PgBouncer u otros clientes.
_PSQL_QUERY_PARAMS_SKIP = frozenset(
    {
        "pgbouncer",
        "statement_cache_size",
    }
)


def _strip_psycopg2_unsupported_query_params(url: str) -> str:
    parts = urlsplit(url)
    if not parts.query:
        return url
    pairs = parse_qsl(parts.query, keep_blank_values=True)
    filtered = [
        (k, v)
        for k, v in pairs
        if k.lower() not in _PSQL_QUERY_PARAMS_SKIP
    ]
    new_query = urlencode(filtered)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def _normalize_database_url(url: str) -> str:
    u = url.strip()
    if u.startswith("postgresql+psycopg2://"):
        pass
    elif u.startswith("postgres://"):
        u = u.replace("postgres://", "postgresql+psycopg2://", 1)
    elif u.startswith("postgresql://") and "+psycopg2" not in u:
        u = u.replace("postgresql://", "postgresql+psycopg2://", 1)
    else:
        return _strip_psycopg2_unsupported_query_params(u)
    return _strip_psycopg2_unsupported_query_params(u)


def get_engine():
    global _engine
    if not settings.database_url:
        raise ValueError("DATABASE_URL no está configurada.")
    if _engine is None:
        _engine = create_engine(
            _normalize_database_url(settings.database_url),
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    try:
        SessionLocal = get_session_factory()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db_schema() -> None:
    """
    Crea en DATABASE_URL las tablas definidas en los modelos SQLAlchemy
    (programs, criteria, criterion_steps) si no existen.

    Si DB_RESET_SCHEMA=true, ejecuta drop_all + create_all (solo entornos de prueba).
    """
    if not settings.database_url:
        return

    from app.models.db_models import Base

    engine = get_engine()
    if settings.db_reset_schema:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    # create_all no altera tablas ya creadas: columnas nuevas del ORM requieren DDL explícito.
    with engine.begin() as conn:
        conn.execute(
            text("ALTER TABLE criteria ADD COLUMN IF NOT EXISTS template_slug TEXT")
        )
