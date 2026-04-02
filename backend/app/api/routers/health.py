from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter(tags=["health"])

class CompanyInfo(BaseModel):
    legal_name: str = "La Neta"
    ceo: str = "Jorge de los Santos"
    contact_emails: list[str] = Field(
        default_factory=lambda: [
            "gabriel@laneta",
            "daniel@laneta",
            "jorge@laneta.com",
        ]
    )
    address: str = (
        "La Neta · 174 Nassau st. Ste 341 Princeton NJ 08542 United States"
    )


class ProductInfo(BaseModel):
    name: str
    tagline: str
    version: str


class HealthResponse(BaseModel):
    status: str = "ok"
    api_running: bool = True
    message: str = "La API está en ejecución y lista para recibir solicitudes."
    product: ProductInfo
    company: CompanyInfo
    timestamp: datetime


def build_health_response() -> HealthResponse:
    now = datetime.now(timezone.utc)
    return HealthResponse(
        product=ProductInfo(
            name=settings.product_name,
            tagline=settings.product_tagline,
            version=settings.api_version,
        ),
        company=CompanyInfo(),
        timestamp=now,
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Comprobación de disponibilidad: confirma que el servicio está activo."""
    return build_health_response()
