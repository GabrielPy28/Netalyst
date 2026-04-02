"""
TikTok: perfil + engagement ≈ (likes + comentarios + shares en muestra de posts) / seguidores × 100.
Fuente: Apify TikTok Scraper (actor criterios_tiktok.md). Misma rúbrica 0–3 que Instagram.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from app.utils.social_engagement_rubric import engagement_points_0_3

logger = logging.getLogger(__name__)

_TIKTOK_HOST = re.compile(r"tiktok\.com", re.I)


def infer_tiktok_vertical_category(commerce: Any, signature: str) -> str:
    """
    Si commerceUserInfo.category viene vacío, infiere desde la firma (bio) del perfil.
    Si no hay señal clara, usa categorías por defecto (p. ej. digital creator).
    """
    comm = str(commerce).strip() if commerce is not None else ""
    if comm and comm.lower() not in {"", "nan", "none", "—"}:
        return comm
    sig = (signature or "").lower()
    if not sig.strip():
        return "digital creator"
    if any(k in sig for k in ("hair", "salon", "barber", "stylist", "hairstylist")):
        return "hair and hairstylist"
    has_music = any(
        k in sig for k in ("musician", "music", "producer", "composer", "singer", "rapper", "band")
    )
    has_game = any(k in sig for k in ("game", "gaming", "gamer", "esports"))
    has_stream = "stream" in sig
    if has_music and has_game and has_stream:
        return "music and games and streaming"
    if has_music and has_game:
        return "music and games"
    if has_music and has_stream:
        return "music and streaming"
    if has_music:
        return "music"
    if has_game:
        return "games"
    if has_stream:
        return "entertainment"
    if any(k in sig for k in ("comedy", "comedian", "humor", "funny", "jokes")):
        return "humor"
    if any(k in sig for k in ("fitness", "fashion", "beauty", "travel", "vlog", "lifestyle")):
        return "lifestyle"
    return "digital creator"


def normalize_tiktok_username(value: str | None) -> str | None:
    """Handle sin @; si viene URL de perfil TikTok, extrae el usuario."""
    if value is None or not str(value).strip():
        return None
    s = str(value).strip()
    if _TIKTOK_HOST.search(s):
        if not s.startswith("http"):
            s = "https://" + s
        try:
            path = urlparse(s).path.strip("/")
        except Exception:  # noqa: BLE001
            return None
        parts = [p for p in path.split("/") if p]
        if not parts:
            return None
        first = parts[0].lstrip("@")
        if first.lower() in {"video", "foryou", "following"}:
            return None
        return first or None
    return s.lstrip("@")


def fetch_tiktok_apify(
    username: str,
    *,
    token: str,
    actor_id: str,
    max_posts: int,
) -> dict[str, Any] | None:
    try:
        from apify_client import ApifyClient
    except ImportError:
        logger.warning("apify_client no instalado")
        return None

    handle = username.strip().lstrip("@")
    if not handle:
        return None

    n_fetch = max(1, int(max_posts))
    run_input: dict[str, Any] = {
        "excludePinnedPosts": False,
        "profiles": [handle],
        "profileSorting": "latest",
        "resultsPerPage": n_fetch,
        "shouldDownloadAvatars": False,
        "shouldDownloadCovers": False,
        "shouldDownloadSlideshowImages": False,
        "shouldDownloadSubtitles": False,
        "shouldDownloadVideos": False,
    }
    client = ApifyClient(token)
    try:
        run = client.actor(actor_id).call(run_input=run_input)
        ds = run.get("defaultDatasetId")
        if not ds:
            return None
        items: list[dict[str, Any]] = []
        for it in client.dataset(ds).iterate_items():
            if isinstance(it, dict):
                items.append(it)
        return _tiktok_aggregate_from_posts(items, max_posts=n_fetch)
    except Exception as e:  # noqa: BLE001
        logger.warning("Apify TikTok error %s: %s", handle, e)
        return None


def _tiktok_aggregate_from_posts(
    items: list[dict[str, Any]],
    *,
    max_posts: int,
) -> dict[str, Any] | None:
    if not items:
        return None
    first = items[0]
    am = first.get("authorMeta") if isinstance(first.get("authorMeta"), dict) else {}
    fans = int(am.get("fans") or 0)
    digg = comments = shares = 0
    n = 0
    for it in items:
        if n >= max_posts:
            break
        digg += int(it.get("diggCount") or 0)
        comments += int(it.get("commentCount") or 0)
        shares += int(it.get("shareCount") or 0)
        n += 1

    pct = (digg + comments + shares) / fans * 100.0 if fans > 0 else 0.0
    commerce = am.get("commerceUserInfo") if isinstance(am.get("commerceUserInfo"), dict) else {}
    latest_at = first.get("createTimeISO")
    if latest_at is None and first.get("createTime") is not None:
        try:
            latest_at = datetime.fromtimestamp(
                int(first["createTime"]), tz=timezone.utc
            ).isoformat()
        except (TypeError, ValueError, OSError):
            latest_at = ""

    avatar = str(
        am.get("avatarLarger")
        or am.get("avatarMedium")
        or am.get("avatar")
        or ""
    ).strip()

    video_total = 0
    for vk in ("video", "videoCount", "videos", "aweme_count"):
        v = am.get(vk)
        if v is not None:
            try:
                video_total = max(video_total, int(v))
            except (TypeError, ValueError):
                pass

    return {
        "username": str(am.get("name") or first.get("input") or ""),
        "nickName": str(am.get("nickName") or ""),
        "signature": str(am.get("signature") or ""),
        "followersCount": fans,
        "verified": bool(am.get("verified")),
        "privateAccount": bool(am.get("privateAccount")),
        "commerceCategory": commerce.get("category"),
        "avatar": avatar,
        "_video_count_profile": video_total,
        "_likes_sum": digg,
        "_comments_sum": comments,
        "_shares_sum": shares,
        "_posts_sampled": n,
        "_engagement_pct": round(pct, 4),
        "_latest_content_at": str(latest_at or ""),
    }


def flatten_tiktok_item(item: dict[str, Any], *, source: str) -> dict[str, Any]:
    followers = int(item.get("followersCount") or 0)
    likes = int(item.get("_likes_sum") or 0)
    comments = int(item.get("_comments_sum") or 0)
    shares = int(item.get("_shares_sum") or 0)
    posts_n = int(item.get("_posts_sampled") or 0)
    pct = float(item.get("_engagement_pct") or 0.0)
    pts = engagement_points_0_3(pct)
    latest_at = str(item.get("_latest_content_at") or "")
    avatar = str(item.get("avatar") or "").strip()
    sig = str(item.get("signature") or "")
    cc = item.get("commerceCategory")
    cat_str = infer_tiktok_vertical_category(cc, sig)
    video_total = int(item.get("_video_count_profile") or 0)
    posts_display = video_total if video_total > 0 else posts_n
    verified = bool(item.get("verified"))
    return {
        "tt_fetch_source": source,
        "tt_fetch_error": "",
        "tt_username_resolved": str(item.get("username") or ""),
        "tt_followers": followers,
        "tt_nickname": str(item.get("nickName") or ""),
        "tt_signature": sig,
        "tt_verified": verified,
        "tt_private_account": bool(item.get("privateAccount")),
        "tt_commerce_category": item.get("commerceCategory"),
        "tt_posts_sampled": posts_n,
        "tt_likes_sum": likes,
        "tt_comments_sum": comments,
        "tt_shares_sum": shares,
        "tt_engagement_pct": pct,
        "tt_engagement_points_0_3": pts,
        "tt_latest_content_at": latest_at,
        "tiktok_followers": followers,
        "tiktok_post_count": posts_display,
        "tiktok_picture": avatar,
        "tiktok_bio": sig,
        "tiktok_category": cat_str,
        "tiktok_verified": verified,
    }


def empty_tt_row(*, source: str = "skipped", error: str = "") -> dict[str, Any]:
    return {
        "tt_fetch_source": source,
        "tt_fetch_error": error,
        "tt_username_resolved": "",
        "tt_followers": 0,
        "tt_nickname": "",
        "tt_signature": "",
        "tt_verified": False,
        "tt_private_account": False,
        "tt_commerce_category": None,
        "tt_posts_sampled": 0,
        "tt_likes_sum": 0,
        "tt_comments_sum": 0,
        "tt_shares_sum": 0,
        "tt_engagement_pct": 0.0,
        "tt_engagement_points_0_3": 0,
        "tt_latest_content_at": "",
        "tiktok_followers": 0,
        "tiktok_post_count": 0,
        "tiktok_picture": "",
        "tiktok_bio": "",
        "tiktok_category": "",
        "tiktok_verified": False,
    }
