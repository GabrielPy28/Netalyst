# Columnas esperadas en CSV/Excel de creadores.

CREATOR_FILE_COLUMNS: tuple[str, ...] = (
    "email",
    "first_name",
    "last_name",
    "full_name",
    "picture",
    "username",
    "instagram_url",
    "tiktok_url",
    "youtube_channel_url",
    "instagram_username",
    "tiktok_username",
    "youtube_channel",
    "category",
    "facebook_page",
    "personalized_paragraph",
    "max_followers",
    "main_platform",
    "status",
    "instagram_followers",
    "instagram_post_count",
    "instagram_picture",
    "instagram_bio",
    "instagram_category",
    "instagram_verified",
    "tiktok_followers",
    "tiktok_post_count",
    "tiktok_picture",
    "tiktok_bio",
    "tiktok_category",
    "tiktok_verified",
    "youtube_followers",
    "youtube_post_count",
    "youtube_picture",
    "youtube_bio",
    "youtube_category",
    "youtube_verified",
)

# Mínimo para pasos de nombre (se puede ampliar por criterio en el futuro).
CREATOR_NAME_STEP_COLUMNS: frozenset[str] = frozenset(
    {"full_name", "first_name", "email", "username", "instagram_bio"}
)
