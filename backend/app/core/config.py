from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _env_files() -> tuple[str, ...] | None:
    here = Path(__file__).resolve()
    backend_root = here.parents[2]
    repo_root = here.parents[3]
    candidates = (repo_root / ".env", backend_root / ".env")
    existing = tuple(str(p) for p in candidates if p.is_file())
    return existing if existing else None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files(),
        # utf-8-sig evita que un BOM al inicio del .env rompa la primera variable.
        env_file_encoding="utf-8-sig",
        extra="ignore",
    )

    product_name: str = "Netalyst"
    product_tagline: str = "Creator validation & data integrity"
    api_version: str = "0.1.0"

    app_name: str = "Netalyst API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    supabase_url: str = ""
    supabase_secret_key: str = ""
    supabase_public_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "SUPABASE_PUBLISHABLE_KEY",
            "SUPABASE_PUBLIC_KEY",
        ),
    )

    database_url: str = ""

    # Solo desarrollo: borra y recrea tablas ORM al iniciar (pérdida de datos).
    db_reset_schema: bool = False

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # Hunter.io Email Verifier (criterio email / último paso del pipeline).
    hunter_api_key: str = ""
    hunter_max_calls_per_run: int = 500
    hunter_min_score: int = 88
    hunter_request_delay_seconds: float = 0.2

    # Apify — Instagram Scraper (actor por defecto documentación del uso de cliente de Apify).
    apify_api_token: str = ""
    apify_instagram_actor_id: str = "shu8hvrXbJbY3Eb9W"
    apify_instagram_delay_seconds: float = 1.0

    # Apify — TikTok Scraper (actor por defecto documentación del uso de cliente de Apify).
    apify_tiktok_actor_id: str = "0FXVyOXXEmdGcV88a"
    apify_tiktok_delay_seconds: float = 1.0
    tiktok_engagement_post_sample_max: int = 5
    tiktok_max_profiles_per_run: int = 100

    # Instaloader (fallback si no hay token Apify). NO commitear credenciales.
    instagram_login_user: str = ""
    instagram_login_password: str = ""
    instagram_engagement_post_sample_max: int = 1
    instagram_max_profiles_per_run: int = 100

    # YouTube Data API v3. Acepta YOUTUBE_DATA_API_KEY o YOUTUBE_API_KEY.
    youtube_data_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("YOUTUBE_DATA_API_KEY", "YOUTUBE_API_KEY"),
    )
    youtube_request_delay_seconds: float = 0.2
    youtube_max_channels_per_run: int = 100

    # Facebook Page + Reels (Apify facebook-pages-scraper; excluir si reel reciente).
    apify_facebook_pages_actor_id: str = "apify/facebook-pages-scraper"
    apify_facebook_delay_seconds: float = 2.0
    facebook_max_pages_per_run: int = 100
    facebook_reel_lookback_months: int = 6

    # Umbral de aprobación del score 0–16 y mínimo de seguidores (criterio redes).
    creator_min_approval_score: float = 8.0
    creator_min_followers_for_approval: int = 100_000
    # Límite de filas serializadas en respuestas JSON/SSE para evitar payloads gigantes.
    validation_preview_max_rows: int = 4000

    @field_validator(
        "supabase_url",
        "supabase_secret_key",
        "supabase_public_key",
        "database_url",
        "jwt_secret",
        "hunter_api_key",
        "apify_api_token",
        "apify_tiktok_actor_id",
        "instagram_login_user",
        "instagram_login_password",
        "youtube_data_api_key",
        mode="before",
    )
    @classmethod
    def strip_optional_str(cls, v: object) -> str:
        if v is None:
            return ""
        s = str(v).strip().replace("\ufeff", "").strip()
        if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
            s = s[1:-1].strip()
        return s

    @field_validator("supabase_url")
    @classmethod
    def supabase_url_must_be_http_api(cls, v: str) -> str:
        if not v:
            return v
        lower = v.lower()
        if lower.startswith("postgresql") or lower.startswith("postgres://"):
            raise ValueError(
                "SUPABASE_URL no debe ser la URL de PostgreSQL (DATABASE_URL). "
                "Debe ser la URL HTTPS del proyecto Supabase, p. ej. "
                "https://xxxx.supabase.co"
            )
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
