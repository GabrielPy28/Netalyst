"""
Facebook Page: detectar si hubo publicación tipo Reel en los últimos N meses (Apify).
Criterio de negocio: excluir creadores con reel reciente (p. ej. 6 meses).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from app.utils.instagram_profile import parse_instagram_handle_from_url
from app.utils.social_creator_scoring import parse_iso_datetime

logger = logging.getLogger(__name__)

def resolve_facebook_page_url(row: pd.Series) -> str | None:
    """Prioridad: columna facebook_page; si no, URL desde handle de Instagram."""
    fp = row.get("facebook_page")
    if fp is not None and not (isinstance(fp, float) and pd.isna(fp)):
        s = str(fp).strip()
        if s and s.lower() not in {"nan", "none"}:
            if s.startswith("http://") or s.startswith("https://"):
                return s.split("?")[0].rstrip("/")
            return f"https://www.facebook.com/{s.lstrip('/').lstrip('@')}"

    ig = row.get("instagram_url")
    if ig is not None and not (isinstance(ig, float) and pd.isna(ig)) and str(ig).strip():
        handle = parse_instagram_handle_from_url(str(ig).strip())
        if handle:
            return f"https://www.facebook.com/{handle}"

    iu = row.get("instagram_username")
    if iu is not None and not (isinstance(iu, float) and pd.isna(iu)) and str(iu).strip():
        h = str(iu).strip().lstrip("@")
        if h:
            return f"https://www.facebook.com/{h}"

    return None


def _is_facebook_reel_post(post: dict[str, Any]) -> bool:
    parts = [
        str(post.get("url") or ""),
        str(post.get("postUrl") or ""),
        str(post.get("link") or ""),
        str(post.get("permalink") or ""),
    ]
    blob = " ".join(parts).lower()
    if "/reel" in blob or "/reels/" in blob:
        return True
    t = str(post.get("type") or post.get("postType") or post.get("mediaType") or "").lower()
    return "reel" in t


def _post_datetime(post: dict[str, Any]) -> datetime | None:
    for k in (
        "publishedAt",
        "date",
        "time",
        "timestamp",
        "createdAt",
        "postDate",
        "creation_time",
    ):
        if k in post:
            dt = parse_iso_datetime(post.get(k))
            if dt is not None:
                return dt
    return None


def any_reel_within_months(
    posts: list[dict[str, Any]],
    *,
    months: int = 6,
) -> tuple[bool, str]:
    """
    True si existe al menos un post identificado como Reel con fecha >= cutoff.
    Devuelve (encontrado, iso del reel más reciente en ventana o vacío).
    """
    if not posts:
        return False, ""
    days = max(1, int(round(float(months) * 30.4375)))
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    best: datetime | None = None
    for post in posts:
        if not isinstance(post, dict) or not _is_facebook_reel_post(post):
            continue
        dt = _post_datetime(post)
        if dt is None:
            continue
        if dt >= cutoff:
            if best is None or dt > best:
                best = dt
    if best is None:
        return False, ""
    return True, best.astimezone(timezone.utc).isoformat()


def fetch_facebook_page_bundle_apify(
    page_url: str,
    *,
    token: str,
    actor_id: str,
) -> tuple[dict[str, Any] | None, str]:
    """
    Retorna ({posts, page_name, url}, "") o (None, código_error).
    """
    try:
        from apify_client import ApifyClient
    except ImportError:
        return None, "apify_client_missing"

    client = ApifyClient(token)
    run_input: dict[str, Any] = {
        "startUrls": [{"url": page_url}],
        "maxPagesPerQuery": 1,
    }
    try:
        run = client.actor(actor_id).call(
            run_input=run_input,
            timeout_secs=120,
            memory_mbytes=1024,
        )
        st = run.get("status")
        if st in ("FAILED", "ABORTED", "TIMED-OUT"):
            return None, f"actor_{st}"
        ds = run.get("defaultDatasetId")
        if not ds:
            return None, "no_dataset"
        items = list(client.dataset(ds).iterate_items())
        if not items:
            return None, "empty_dataset"
        item = items[0]
        if not isinstance(item, dict):
            return None, "invalid_item"
        if item.get("error"):
            return None, "page_error"
        name = str(item.get("title") or item.get("pageName") or "")
        out_url = str(item.get("pageUrl") or item.get("facebookUrl") or page_url)
        raw = item.get("posts") or item.get("latestPosts") or []
        posts: list[dict[str, Any]] = []
        if isinstance(raw, list):
            posts = [p for p in raw if isinstance(p, dict)]
        return {"posts": posts, "page_name": name, "url": out_url}, ""
    except Exception as e:  # noqa: BLE001
        logger.warning("Apify Facebook error %s: %s", page_url, e)
        return None, "fetch_failed"


def flatten_facebook_reel_row(
    *,
    source: str,
    error: str,
    resolved_url: str,
    page_found: bool,
    page_name: str,
    posts_n: int,
    reel_in_window: bool,
    latest_reel_iso: str,
) -> dict[str, Any]:
    exclude = bool(page_found and reel_in_window)
    return {
        "fb_fetch_source": source,
        "fb_fetch_error": error,
        "fb_resolved_url": resolved_url,
        "fb_page_found": page_found,
        "fb_page_name": page_name,
        "fb_posts_parsed_count": posts_n,
        "fb_reel_within_6_months": reel_in_window,
        "fb_latest_reel_in_window_at": latest_reel_iso,
        "fb_exclude_per_recent_reel_rule": exclude,
    }


def empty_fb_reel_row(*, source: str = "skipped", error: str = "") -> dict[str, Any]:
    return flatten_facebook_reel_row(
        source=source,
        error=error,
        resolved_url="",
        page_found=False,
        page_name="",
        posts_n=0,
        reel_in_window=False,
        latest_reel_iso="",
    )
