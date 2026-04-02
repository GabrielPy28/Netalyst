from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth, health, programs, validation
from app.core.config import settings
from app.core.db import init_db_schema


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db_schema()
    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        f"{settings.product_name} — {settings.product_tagline}. "
        "Plataforma La Neta para limpieza y validación de creadores."
    ),
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    """Evita 404 en la raíz del dominio (p. ej. Railway) y documenta rutas útiles."""
    return {
        "service": settings.app_name,
        "health": "/health",
        "docs": "/docs",
        "api_prefix": settings.api_v1_prefix,
    }


app.include_router(health.router)
app.include_router(auth.auth_router, prefix=settings.api_v1_prefix)
app.include_router(programs.router, prefix=settings.api_v1_prefix)
app.include_router(validation.router, prefix=settings.api_v1_prefix)
