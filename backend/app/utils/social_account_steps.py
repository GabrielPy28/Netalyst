"""
Criterio: verificación de cuentas (IG, TikTok, YouTube), score 0–16, Facebook Reels.
Instagram: Apify + Instaloader. TikTok: Apify. YouTube: Data API v3. Facebook: Apify (reels recientes).
"""

from __future__ import annotations

import re
import time
from typing import Any

import pandas as pd

from app.constants.social_columns import SOCIAL_VERIFICATION_COLUMNS
from app.core.config import settings
from app.services.validation_context import ValidationContext
from app.utils.instagram_profile import (
    empty_ig_row,
    fetch_instagram_apify,
    fetch_instagram_instaloader,
    flatten_instagram_item,
    normalize_instagram_profile_url,
    parse_instagram_handle_from_url,
)
from app.utils.name_cleaning import maybe_refresh_names_from_instagram_fetch
from app.utils.tiktok_profile import (
    empty_tt_row,
    fetch_tiktok_apify,
    flatten_tiktok_item,
    infer_tiktok_vertical_category,
    normalize_tiktok_username,
)
from app.utils.youtube_channel import (
    empty_yt_row,
    fetch_youtube_channel_bundle,
    flatten_youtube_row,
    parse_youtube_channel_reference,
)
from app.utils.facebook_reels import (
    any_reel_within_months,
    empty_fb_reel_row,
    fetch_facebook_page_bundle_apify,
    flatten_facebook_reel_row,
    resolve_facebook_page_url,
)
from app.utils.social_creator_scoring import row_creator_score
from app.utils.social_vertical_format import (
    format_vertical_phrase,
    normalize_youtube_topics_for_vertical,
    split_category_segments,
)


def _log(ctx: ValidationContext, step_key: str, message: str, **extra: Any) -> None:
    ctx.logs.append({"funcion": step_key, "message": message, **extra})


def _clean_vertical_for_display(val: Any) -> str:
    """Quita vacíos, None literal y la palabra 'None' en el texto."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    if not s or s.lower() in ("none", "nan", "null", "—"):
        return ""
    s = re.sub(r"\b[Nn]one\b", " ", s)
    s = re.sub(r"\b[Nn][Aa][Nn]\b", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" ,;")
    return s


_INSTAGRAM_VERTICAL_DEFAULT = "digital creator"


def _cell_ok(val: Any) -> bool:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    s = str(val).strip()
    return bool(s) and s.lower() not in {"nan", "none"}


def load_social_verification_columns(ctx: ValidationContext) -> ValidationContext:
    """Paso 1: exige tiktok_username, instagram_url, youtube_channel_url (pueden ir vacías por fila)."""
    key = "load_social_verification_columns"
    missing = [c for c in SOCIAL_VERIFICATION_COLUMNS if c not in ctx.df.columns]
    if missing:
        _log(ctx, key, "Faltan columnas sociales.", missing=missing, ok=False)
        raise ValueError(
            f"Faltan columnas para verificación de cuentas: {missing}. "
            f"Se requieren: {list(SOCIAL_VERIFICATION_COLUMNS)}."
        )
    _log(ctx, key, "Columnas sociales presentes.", ok=True, columns=list(SOCIAL_VERIFICATION_COLUMNS))
    return ctx


def _row_profile_url(row: pd.Series) -> str | None:
    url = row.get("instagram_url")
    if pd.notna(url) and str(url).strip():
        return normalize_instagram_profile_url(str(url).strip())
    un = row.get("instagram_username")
    if un is not None and pd.notna(un) and str(un).strip():
        return normalize_instagram_profile_url(str(un).strip())
    return None


def fetch_instagram_profiles(ctx: ValidationContext) -> ValidationContext:
    """
    Paso 2: por cada fila con URL/handle Instagram, obtiene perfil vía Apify (prioridad)
    o Instaloader si hay credenciales y no hay token Apify / falla Apify.
    """
    key = "fetch_instagram_profiles"
    df = ctx.df.copy()
    max_posts = settings.instagram_engagement_post_sample_max
    max_rows = settings.instagram_max_profiles_per_run
    token = (settings.apify_api_token or "").strip()
    actor = (settings.apify_instagram_actor_id or "shu8hvrXbJbY3Eb9W").strip()
    ig_user = (settings.instagram_login_user or "").strip()
    ig_pass = (settings.instagram_login_password or "").strip()

    apify_cache: dict[str, Any] = ctx.pipeline_cache.setdefault("ig_apify_url_cache", {})
    loader_key = "instaloader_loader"
    loader: Any = ctx.pipeline_cache.get(loader_key)

    if not token and (not ig_user or not ig_pass):
        _log(
            ctx,
            key,
            "Sin APIFY_API_TOKEN ni INSTAGRAM_LOGIN_USER/PASSWORD; no se consulta Instagram.",
            skipped=True,
        )
        empty = empty_ig_row(source="skipped", error="no_credentials")
        for col, val in empty.items():
            df[col] = val
        ctx.df = df
        return ctx

    def _ensure_instaloader() -> Any:
        nonlocal loader
        if loader is not None:
            return loader
        if not ig_user or not ig_pass:
            return None
        try:
            from instaloader import Instaloader

            il = Instaloader(
                download_pictures=False,
                download_videos=False,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
            )
            il.login(ig_user, ig_pass)
            loader = il
            ctx.pipeline_cache[loader_key] = loader
            return loader
        except Exception as e:  # noqa: BLE001
            _log(ctx, key, f"Instaloader login falló: {e}", ok=False)
            return None

    if not token:
        loader = _ensure_instaloader()

    rows_out: list[dict[str, Any]] = []
    n_apify = n_il = n_skip = n_err = 0
    processed = 0

    for _, row in df.iterrows():
        if processed >= max_rows:
            rows_out.append(empty_ig_row(source="skipped", error="max_profiles_per_run"))
            n_skip += 1
            continue
        processed += 1

        profile_url = _row_profile_url(row)
        if not profile_url:
            rows_out.append(empty_ig_row(source="skipped", error="no_instagram_url"))
            n_skip += 1
            continue

        handle = parse_instagram_handle_from_url(profile_url) or ""
        item: dict[str, Any] | None = None
        source_used = ""

        if token:
            cache_key = profile_url.lower().split("?")[0]
            cached = apify_cache.get(cache_key)
            if cached is not None:
                item = cached
                source_used = "apify"
            else:
                item = fetch_instagram_apify(
                    profile_url,
                    token=token,
                    actor_id=actor,
                    max_posts=max_posts,
                )
                if item is not None:
                    apify_cache[cache_key] = item
                source_used = "apify"
                time.sleep(settings.apify_instagram_delay_seconds)

        if item is None and handle:
            il = loader or _ensure_instaloader()
            if il is not None:
                item = fetch_instagram_instaloader(handle, loader=il, max_posts=max_posts)
                if item:
                    source_used = "instaloader"

        if item is None:
            rows_out.append(
                empty_ig_row(
                    source="error",
                    error="fetch_failed",
                )
            )
            n_err += 1
            continue

        if source_used == "apify":
            n_apify += 1
        elif source_used == "instaloader":
            n_il += 1

        flat = flatten_instagram_item(item, source=source_used, max_posts=max_posts)
        rows_out.append(flat)

    ig_df = pd.DataFrame(rows_out)
    for c in ig_df.columns:
        df[c] = ig_df[c].values

    df = maybe_refresh_names_from_instagram_fetch(df)

    _log(
        ctx,
        key,
        "Instagram: perfiles obtenidos.",
        ok=True,
        apify_or_instagram_rows=len(rows_out),
        count_apify=n_apify,
        count_instaloader=n_il,
        skipped=n_skip,
        errors=n_err,
        max_profiles_per_run=max_rows,
        engagement_post_sample=max_posts,
    )
    ctx.df = df
    return ctx


def fetch_tiktok_profiles(ctx: ValidationContext) -> ValidationContext:
    """
    Por cada fila con tiktok_username (o URL de perfil), obtiene posts vía Apify
    y calcula engagement: ((likes + comentarios + shares) / seguidores) × 100.
    """
    key = "fetch_tiktok_profiles"
    df = ctx.df.copy()
    max_posts = settings.tiktok_engagement_post_sample_max
    max_rows = settings.tiktok_max_profiles_per_run
    token = (settings.apify_api_token or "").strip()
    actor = (settings.apify_tiktok_actor_id or "0FXVyOXXEmdGcV88a").strip()

    cache: dict[str, Any] = ctx.pipeline_cache.setdefault("tt_apify_username_cache", {})

    if not token:
        _log(ctx, key, "Sin APIFY_API_TOKEN; no se consulta TikTok.", skipped=True)
        empty = empty_tt_row(source="skipped", error="no_credentials")
        for col, val in empty.items():
            df[col] = val
        ctx.df = df
        return ctx

    rows_out: list[dict[str, Any]] = []
    n_ok = n_skip = n_err = 0
    processed = 0

    for _, row in df.iterrows():
        if processed >= max_rows:
            rows_out.append(empty_tt_row(source="skipped", error="max_profiles_per_run"))
            n_skip += 1
            continue
        processed += 1

        raw = row.get("tiktok_username")
        if raw is None or (isinstance(raw, float) and pd.isna(raw)) or not str(raw).strip():
            rows_out.append(empty_tt_row(source="skipped", error="no_tiktok_username"))
            n_skip += 1
            continue

        handle = normalize_tiktok_username(str(raw).strip())
        if not handle:
            rows_out.append(empty_tt_row(source="skipped", error="invalid_tiktok_username"))
            n_skip += 1
            continue

        cache_key = handle.lower()
        cached = cache.get(cache_key)
        if cached is not None:
            item = cached
        else:
            item = fetch_tiktok_apify(
                handle,
                token=token,
                actor_id=actor,
                max_posts=max_posts,
            )
            if item is not None:
                cache[cache_key] = item
            time.sleep(settings.apify_tiktok_delay_seconds)

        if item is None:
            rows_out.append(empty_tt_row(source="error", error="fetch_failed"))
            n_err += 1
            continue

        n_ok += 1
        rows_out.append(flatten_tiktok_item(item, source="apify"))

    tt_df = pd.DataFrame(rows_out)
    for c in tt_df.columns:
        df[c] = tt_df[c].values

    _log(
        ctx,
        key,
        "TikTok: perfiles obtenidos (Apify).",
        ok=True,
        rows=len(rows_out),
        count_ok=n_ok,
        skipped=n_skip,
        errors=n_err,
        max_profiles_per_run=max_rows,
        engagement_post_sample=max_posts,
    )
    ctx.df = df
    return ctx


def _yt_cache_key(lookup_kind: str, lookup_value: str) -> str:
    v = lookup_value.strip()
    if lookup_kind == "handle":
        return f"h:{v.lower()}"
    if lookup_kind == "username":
        return f"u:{v.lower()}"
    return f"id:{v}"


def fetch_youtube_channels(ctx: ValidationContext) -> ValidationContext:
    """
    Por cada fila con youtube_channel_url (ID UC…, URL /channel/…, /@handle, /user/, /c/),
    consulta YouTube Data API v3 y calcula engagement del último video subido.
    """
    key = "fetch_youtube_channels"
    df = ctx.df.copy()
    max_rows = settings.youtube_max_channels_per_run
    api_key = (settings.youtube_data_api_key or "").strip()
    delay = settings.youtube_request_delay_seconds

    cache: dict[str, Any] = ctx.pipeline_cache.setdefault("yt_api_cache", {})

    if not api_key:
        _log(
            ctx,
            key,
            "Sin clave YouTube Data API (YOUTUBE_API_KEY o YOUTUBE_DATA_API_KEY); no se consulta YouTube.",
            skipped=True,
        )
        empty = empty_yt_row(source="skipped", error="no_credentials")
        for col, val in empty.items():
            df[col] = val
        ctx.df = df
        return ctx

    rows_out: list[dict[str, Any]] = []
    n_ok = n_skip = n_err = 0
    processed = 0

    for _, row in df.iterrows():
        if processed >= max_rows:
            rows_out.append(empty_yt_row(source="skipped", error="max_channels_per_run"))
            n_skip += 1
            continue
        processed += 1

        raw = row.get("youtube_channel_url")
        if raw is None or (isinstance(raw, float) and pd.isna(raw)) or not str(raw).strip():
            rows_out.append(empty_yt_row(source="skipped", error="no_youtube_channel_url"))
            n_skip += 1
            continue

        parsed = parse_youtube_channel_reference(str(raw).strip())
        if not parsed:
            rows_out.append(empty_yt_row(source="skipped", error="invalid_youtube_reference"))
            n_skip += 1
            continue

        lk, lv = parsed
        ck = _yt_cache_key(lk, lv)
        cached_flat = cache.get(ck)
        if cached_flat is None:
            payload, err = fetch_youtube_channel_bundle(
                api_key,
                lookup_kind=lk,
                lookup_value=lv,
                request_delay=delay,
            )
            if payload is None:
                rows_out.append(empty_yt_row(source="error", error=err or "fetch_failed"))
                n_err += 1
                continue
            flat = flatten_youtube_row(payload, source="youtube_data_api_v3")
            cid = flat.get("yt_channel_id") or ""
            cache[ck] = flat
            if cid:
                cache[_yt_cache_key("id", cid)] = flat
            cached_flat = flat
        n_ok += 1
        rows_out.append(cached_flat)

    yt_df = pd.DataFrame(rows_out)
    for c in yt_df.columns:
        df[c] = yt_df[c].values

    _log(
        ctx,
        key,
        "YouTube: canales obtenidos (Data API v3).",
        ok=True,
        rows=len(rows_out),
        count_ok=n_ok,
        skipped=n_skip,
        errors=n_err,
        max_channels_per_run=max_rows,
    )
    ctx.df = df
    return ctx


def _pick_main_platform_label(row: pd.Series) -> str:
    """Plataforma con más seguidores; empate → Instagram, luego TikTok, luego YouTube."""
    ig_f = int(row.get("ig_followers") or 0)
    tt_f = int(row.get("tt_followers") or 0)
    yt_f = int(row.get("yt_subscriber_count") or 0)
    order = [("Instagram", ig_f), ("Tiktok", tt_f), ("Youtube", yt_f)]
    best_l, best_f = order[0]
    for label, fc in order[1:]:
        if fc > best_f:
            best_l, best_f = label, fc
    if best_f > 0:
        return best_l
    if _cell_ok(row.get("ig_username_resolved")) or _cell_ok(row.get("instagram_username")) or _cell_ok(
        row.get("instagram_url")
    ):
        return "Instagram"
    if _cell_ok(row.get("tt_username_resolved")) or _cell_ok(row.get("tiktok_username")):
        return "Tiktok"
    if _cell_ok(row.get("youtube_channel_url")) or _cell_ok(row.get("youtube_channel")):
        return "Youtube"
    return best_l


def _main_platform_follower_count(row: pd.Series, main: str) -> int:
    if main == "Instagram":
        return int(row.get("ig_followers") or row.get("instagram_followers") or 0)
    if main == "Tiktok":
        return int(row.get("tt_followers") or row.get("tiktok_followers") or 0)
    return int(row.get("yt_subscriber_count") or row.get("youtube_followers") or 0)


def apply_main_platform_identity(ctx: ValidationContext) -> ValidationContext:
    """
    Tras poblar datos de IG/TT/YT: define plataforma predominante (más seguidores),
    actualiza username, main_platform (Instagram | Tiktok | Youtube), picture (foto principal)
    y vertical (categorías de la red principal, reglas de redacción en minúsculas).
    Debe ejecutarse antes de compute_creator_social_score y del gate de aprobación.
    """
    key = "apply_main_platform_identity"
    df = ctx.df.copy()
    usernames: list[str] = []
    platforms: list[str] = []
    pictures: list[str] = []
    verticals: list[str] = []
    max_followers_out: list[int] = []

    for _, row in df.iterrows():
        main = _pick_main_platform_label(row)
        mf = _main_platform_follower_count(row, main)

        if main == "Instagram":
            un = str(row.get("ig_username_resolved") or row.get("instagram_username") or "").strip()
            pic = str(row.get("instagram_picture") or "").strip()
            raw_cat = row.get("instagram_category") or row.get("ig_business_category_name") or ""
            segs = split_category_segments(raw_cat)
        elif main == "Tiktok":
            un = str(row.get("tt_username_resolved") or row.get("tiktok_username") or "").strip()
            pic = str(row.get("tiktok_picture") or "").strip()
            comm = row.get("tt_commerce_category")
            sig = str(row.get("tt_signature") or row.get("tiktok_bio") or "")
            raw_cat = infer_tiktok_vertical_category(comm, sig)
            segs = split_category_segments(raw_cat)
        else:
            pic = str(row.get("youtube_picture") or "").strip()
            raw_cat = row.get("youtube_category") or row.get("yt_topic_categories_clean") or ""
            segs = normalize_youtube_topics_for_vertical(raw_cat)
            # Handle visible para operación diaria: @customUrl > slug del archivo > channel id
            un = str(row.get("yt_custom_url") or "").strip().lstrip("@")
            if not un:
                un = str(row.get("youtube_channel") or "").strip().lstrip("@")
            if not un:
                un = str(row.get("yt_channel_id") or "").strip()

        vert = format_vertical_phrase(segs)
        usernames.append(un)
        platforms.append(main)
        pictures.append(pic)
        verticals.append(vert)
        max_followers_out.append(mf)

    df["username"] = usernames
    df["main_platform"] = platforms
    df["picture"] = pictures
    df["vertical"] = verticals
    # Columna operativa alineada con vertical (categoría principal del creador en la red mayor).
    df["category"] = verticals
    df["max_followers"] = max_followers_out

    _log(
        ctx,
        key,
        "Identidad principal: username, main_platform, picture y vertical por red predominante.",
        ok=True,
        rows=len(df),
    )
    ctx.df = df
    return ctx


def compute_creator_social_score(ctx: ValidationContext) -> ValidationContext:
    """
    Score total 0–16 (crietiors_instagram.md): suma engagement IG+TT+YT (c/u 0–3),
    tier seguidores (0–2), plataformas activas (0–2), completitud (0–2), actividad 30d (0–1).
    Añade creator_score_total_0_16 y creator_priority_band (priority_13_16 | standard_8_12 | low_1_7).
    Ejecutar después de apply_main_platform_identity (y fetches IG/TT/YT).
    """
    key = "compute_creator_social_score"
    df = ctx.df.copy()
    out_rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        out_rows.append(row_creator_score(row))
    score_df = pd.DataFrame(out_rows)
    for c in score_df.columns:
        df[c] = score_df[c].values
    _log(
        ctx,
        key,
        "Score creador 0–16 y banda calculados.",
        ok=True,
        rows=len(df),
    )
    ctx.df = df
    return ctx


def sync_identity_columns_from_creator_main_platform(ctx: ValidationContext) -> ValidationContext:
    """
    Tras `compute_creator_social_score`: alinea username, picture, max_followers y vertical
    con la plataforma en `creator_main_platform` (instagram | tiktok | youtube).

    Instagram: categoría vacía o solo basura → vertical por defecto; se eliminan tokens None.
    """
    key = "sync_identity_columns_from_creator_main_platform"
    df = ctx.df.copy()
    if "creator_main_platform" not in df.columns:
        _log(
            ctx,
            key,
            "Sin creator_main_platform; ejecute antes compute_creator_social_score.",
            skipped=True,
        )
        ctx.df = df
        return ctx

    usernames: list[str] = []
    pictures: list[str] = []
    max_followers_list: list[int] = []
    verticals: list[str] = []

    for _, row in df.iterrows():
        plat = str(row.get("creator_main_platform") or "").strip().lower()

        if plat == "instagram":
            un = str(row.get("instagram_username") or "").strip().lstrip("@")
            pic = str(row.get("instagram_picture") or "").strip()
            try:
                mf = int(row.get("instagram_followers") or row.get("ig_followers") or 0)
            except (TypeError, ValueError):
                mf = 0
            v = _clean_vertical_for_display(row.get("instagram_category"))
            if not v:
                v = _INSTAGRAM_VERTICAL_DEFAULT
        elif plat == "tiktok":
            un = str(row.get("tiktok_username") or "").strip().lstrip("@")
            pic = str(row.get("tiktok_picture") or "").strip()
            try:
                mf = int(row.get("tiktok_followers") or row.get("tt_followers") or 0)
            except (TypeError, ValueError):
                mf = 0
            v = _clean_vertical_for_display(row.get("tiktok_category"))
        elif plat == "youtube":
            un = str(row.get("yt_custom_url") or "").strip().lstrip("@")
            if not un:
                un = str(row.get("youtube_channel") or "").strip().lstrip("@")
            if not un:
                un = str(row.get("yt_channel_id") or "").strip()
            pic = str(row.get("youtube_picture") or "").strip()
            try:
                mf = int(row.get("youtube_followers") or row.get("yt_subscriber_count") or 0)
            except (TypeError, ValueError):
                mf = 0
            v = _clean_vertical_for_display(row.get("youtube_category"))
        else:
            un = str(row.get("username") or "").strip()
            pic = str(row.get("picture") or "").strip()
            try:
                mf = int(row.get("max_followers") or 0)
            except (TypeError, ValueError):
                mf = 0
            v = _clean_vertical_for_display(row.get("vertical"))

        usernames.append(un)
        pictures.append(pic)
        max_followers_list.append(mf)
        verticals.append(v)

    df["username"] = usernames
    df["picture"] = pictures
    df["max_followers"] = max_followers_list
    df["vertical"] = verticals
    df["category"] = verticals

    _log(
        ctx,
        key,
        "username, picture, max_followers, vertical y category según creator_main_platform.",
        ok=True,
        rows=len(df),
    )
    ctx.df = df
    return ctx


def fetch_facebook_recent_reel_activity(ctx: ValidationContext) -> ValidationContext:
    """
    Usa facebook_page o el handle de Instagram para resolver la URL de la página,
    scrapea con Apify (facebook-pages-scraper) y marca fb_exclude_per_recent_reel_rule
    si hay un Reel publicado en los últimos N meses (facebook_reel_lookback_months).
    """
    key = "fetch_facebook_recent_reel_activity"
    df = ctx.df.copy()
    token = (settings.apify_api_token or "").strip()
    actor = (settings.apify_facebook_pages_actor_id or "apify/facebook-pages-scraper").strip()
    max_rows = settings.facebook_max_pages_per_run
    months = settings.facebook_reel_lookback_months
    delay = settings.apify_facebook_delay_seconds
    cache: dict[str, Any] = ctx.pipeline_cache.setdefault("fb_apify_url_cache", {})

    if not token:
        _log(ctx, key, "Sin APIFY_API_TOKEN; no se consulta Facebook.", skipped=True)
        empty = empty_fb_reel_row(source="skipped", error="no_credentials")
        for col, val in empty.items():
            df[col] = val
        ctx.df = df
        return ctx

    rows_out: list[dict[str, Any]] = []
    n_ok = n_skip = n_err = 0
    processed = 0

    for _, row in df.iterrows():
        if processed >= max_rows:
            rows_out.append(empty_fb_reel_row(source="skipped", error="max_pages_per_run"))
            n_skip += 1
            continue
        processed += 1

        resolved = resolve_facebook_page_url(row)
        if not resolved:
            rows_out.append(empty_fb_reel_row(source="skipped", error="no_facebook_url"))
            n_skip += 1
            continue

        ck = resolved.lower().split("?")[0]
        bundle = cache.get(ck)
        err = ""
        if bundle is None:
            bundle, err = fetch_facebook_page_bundle_apify(
                resolved,
                token=token,
                actor_id=actor,
            )
            if bundle is not None:
                cache[ck] = bundle
            time.sleep(delay)

        if bundle is None:
            rows_out.append(
                flatten_facebook_reel_row(
                    source="apify",
                    error=err or "fetch_failed",
                    resolved_url=resolved,
                    page_found=False,
                    page_name="",
                    posts_n=0,
                    reel_in_window=False,
                    latest_reel_iso="",
                )
            )
            n_err += 1
            continue

        posts = bundle.get("posts") or []
        reel_ok, reel_iso = any_reel_within_months(posts, months=months)
        flat = flatten_facebook_reel_row(
            source="apify",
            error="",
            resolved_url=str(bundle.get("url") or resolved),
            page_found=True,
            page_name=str(bundle.get("page_name") or ""),
            posts_n=len(posts),
            reel_in_window=reel_ok,
            latest_reel_iso=reel_iso,
        )
        n_ok += 1
        rows_out.append(flat)

    fb_df = pd.DataFrame(rows_out)
    for c in fb_df.columns:
        df[c] = fb_df[c].values

    _log(
        ctx,
        key,
        "Facebook: actividad Reel evaluada (Apify).",
        ok=True,
        rows=len(rows_out),
        count_ok=n_ok,
        skipped=n_skip,
        errors=n_err,
        reel_lookback_months=months,
    )
    ctx.df = df
    return ctx
