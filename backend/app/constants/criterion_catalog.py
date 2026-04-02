"""
Plantillas de criterios reutilizables al crear un programa desde el front.
Cada plantilla define nombre, objetivo, pasos (funcion_a_ejecutar debe existir en STEP_REGISTRY).
"""

from __future__ import annotations

from typing import Any, TypedDict


class StepDef(TypedDict):
    paso_num: int
    nombre: str
    definicion: str
    funcion_a_ejecutar: str


class CriterionTemplate(TypedDict):
    slug: str
    nombre: str
    objetivo: str
    entrega_usuario: str
    salida_esperada: str
    steps: list[StepDef]


CRITERION_CATALOG: list[CriterionTemplate] = [
    {
        "slug": "redes_puntaje_y_filtros",
        "nombre": "Redes, score 0–16 y aprobación",
        "objetivo": (
            "Actualizar datos de Instagram, TikTok y YouTube; calcular el score total; "
            "filtrar por mínimo de seguidores y puntaje de aprobación."
        ),
        "entrega_usuario": (
            "Archivo CSV o Excel con columnas de creador (email, nombres, category, etc.) "
            "y columnas sociales: tiktok_username, instagram_url, youtube_channel_url."
        ),
        "salida_esperada": (
            "Columnas instagram_* / tiktok_* / youtube_* con datos frescos; username, main_platform, "
            "picture y vertical según la red predominante; score creator_score_total_0_16; "
            "tras el score, username/picture/max_followers/vertical/category alineados con "
            "creator_main_platform; filas que no aprueban pasan a excluidos en etapa 1."
        ),
        "steps": [
            {
                "paso_num": 1,
                "nombre": "Validar columnas de creador",
                "definicion": "Comprueba columnas estándar del archivo de lista.",
                "funcion_a_ejecutar": "load_creator_columns",
            },
            {
                "paso_num": 2,
                "nombre": "Columnas de verificación social",
                "definicion": "Exige tiktok_username, instagram_url, youtube_channel_url.",
                "funcion_a_ejecutar": "load_social_verification_columns",
            },
            {
                "paso_num": 3,
                "nombre": "Perfiles Instagram",
                "definicion": "Apify / Instaloader: actualiza ig_* e instagram_* (seguidores, posts, foto, bio, categoría, verificado).",
                "funcion_a_ejecutar": "fetch_instagram_profiles",
            },
            {
                "paso_num": 4,
                "nombre": "Perfiles TikTok",
                "definicion": "Apify: actualiza tt_* y tiktok_* (avatar, bio, categoría, etc.).",
                "funcion_a_ejecutar": "fetch_tiktok_profiles",
            },
            {
                "paso_num": 5,
                "nombre": "Canales YouTube",
                "definicion": "YouTube Data API v3: actualiza yt_* y youtube_* (thumbnail medium, descripción, topics).",
                "funcion_a_ejecutar": "fetch_youtube_channels",
            },
            {
                "paso_num": 6,
                "nombre": "Plataforma principal e identidad",
                "definicion": (
                    "Por mayor número de seguidores: fija username, main_platform (Instagram / Tiktok / Youtube), "
                    "picture y vertical (categorías en minúsculas; hasta 3 términos con reglas de redacción)."
                ),
                "funcion_a_ejecutar": "apply_main_platform_identity",
            },
            {
                "paso_num": 7,
                "nombre": "Score creador 0–16",
                "definicion": "Engagement, tier, plataformas, completitud, actividad 30 días.",
                "funcion_a_ejecutar": "compute_creator_social_score",
            },
            {
                "paso_num": 8,
                "nombre": "Identidad según plataforma del score",
                "definicion": (
                    "Actualiza username, picture, max_followers y vertical (y category) según "
                    "creator_main_platform: Instagram → instagram_*; TikTok → tiktok_*; "
                    "YouTube → yt_custom_url / youtube_*."
                ),
                "funcion_a_ejecutar": "sync_identity_columns_from_creator_main_platform",
            },
            {
                "paso_num": 9,
                "nombre": "Filtro seguidores y puntaje",
                "definicion": "Excluye filas bajo umbral (p. ej. 100k y score mínimo).",
                "funcion_a_ejecutar": "gate_social_followers_and_min_score",
            },
        ],
    },
    {
        "slug": "facebook_reels",
        "nombre": "Facebook — actividad reciente (Reels)",
        "objetivo": (
            "Detectar Reels recientes en la página de Facebook y excluir creadores con actividad "
            "en el periodo configurado."
        ),
        "entrega_usuario": (
            "Columna facebook_page y/o instagram_url / instagram_username para resolver la URL "
            "de la página."
        ),
        "salida_esperada": (
            "Columnas fb_*; exclusiones en etapa 2 si aplica la regla de Reels recientes."
        ),
        "steps": [
            {
                "paso_num": 1,
                "nombre": "Consultar página y Reels",
                "definicion": "Apify facebook-pages-scraper.",
                "funcion_a_ejecutar": "fetch_facebook_recent_reel_activity",
            },
            {
                "paso_num": 2,
                "nombre": "Excluir por Reel reciente",
                "definicion": "Mueve filas a excluidos si fb_exclude_per_recent_reel_rule.",
                "funcion_a_ejecutar": "gate_facebook_recent_reel_exclusions",
            },
        ],
    },
    {
        "slug": "limpieza_nombres",
        "nombre": "Limpieza de nombres",
        "objetivo": "Normalizar full_name y first_name con nameparser y reglas La Neta.",
        "entrega_usuario": "Columnas full_name, first_name, email, username, instagram_bio (mínimo según pasos).",
        "salida_esperada": "DataFrame con nombres normalizados y name_cleaning_source.",
        "steps": [
            {
                "paso_num": 1,
                "nombre": "Fuentes de nombre",
                "definicion": "Valida columnas para extracción de nombre.",
                "funcion_a_ejecutar": "extract_best_name_source",
            },
            {
                "paso_num": 2,
                "nombre": "Aplicar nameparser",
                "definicion": "Normaliza first_name / full_name.",
                "funcion_a_ejecutar": "apply_name_parser",
            },
            {
                "paso_num": 3,
                "nombre": "Procesar DataFrame",
                "definicion": "Cierre del criterio sobre la lista.",
                "funcion_a_ejecutar": "process_full_dataframe",
            },
        ],
    },
    {
        "slug": "email_hunter",
        "nombre": "Email — patrones y Hunter",
        "objetivo": "Filtrar patrones de email y verificar con Hunter.io; excluir no válidos.",
        "entrega_usuario": "Columna email con direcciones a verificar.",
        "salida_esperada": "Columnas hunter_*; exclusiones en etapa 4 si no pasan reglas.",
        "steps": [
            {
                "paso_num": 1,
                "nombre": "Patrones de email",
                "definicion": "Marca emails institucionales / patrones de negocio.",
                "funcion_a_ejecutar": "screen_email_patterns",
            },
            {
                "paso_num": 2,
                "nombre": "Verificación Hunter",
                "definicion": "Llamadas a Hunter.io según límites configurados.",
                "funcion_a_ejecutar": "hunter_verify_emails",
            },
            {
                "paso_num": 3,
                "nombre": "Excluir emails no válidos",
                "definicion": "Mueve filas que no superan Hunter al archivo de excluidos.",
                "funcion_a_ejecutar": "gate_email_hunter_failures",
            },
        ],
    },
]


def catalog_by_slug() -> dict[str, CriterionTemplate]:
    return {t["slug"]: t for t in CRITERION_CATALOG}


def validate_functions_registered() -> list[str]:
    """Devuelve funciones del catálogo que no estén en STEP_REGISTRY (para tests)."""
    from app.utils.step_registry import STEP_REGISTRY

    missing: list[str] = []
    for t in CRITERION_CATALOG:
        for s in t["steps"]:
            fn = s["funcion_a_ejecutar"]
            if fn not in STEP_REGISTRY:
                missing.append(fn)
    return missing
