"""Cliente Supabase para Auth (sign_in_with_password)."""
from supabase import Client, SupabaseException, create_client

from app.core.config import get_settings

_client: Client | None = None


def _normalize_supabase_url(url: str) -> str:
    u = url.replace("\ufeff", "").strip().rstrip("/")
    if not u:
        return u
    if not u.startswith(("http://", "https://")):
        u = f"https://{u}"
    return u


def get_supabase_client() -> Client:
    """Cliente con SUPABASE_SECRET_KEY (preferido) o SUPABASE_PUBLIC_KEY."""
    global _client
    if _client is not None:
        return _client

    settings = get_settings()
    url = _normalize_supabase_url(settings.supabase_url)
    key = (settings.supabase_secret_key or settings.supabase_public_key).strip()

    if not url or not key:
        raise ValueError(
            "Configure SUPABASE_URL y SUPABASE_SECRET_KEY o SUPABASE_PUBLIC_KEY en .env"
        )

    try:
        _client = create_client(url, key)
    except SupabaseException as e:
        if "invalid url" in str(e).lower():
            raise ValueError(
                "SUPABASE_URL inválida (p. ej. BOM o formato incorrecto). "
                "Debe ser https://<proyecto>.supabase.co"
            ) from e
        raise
    return _client
