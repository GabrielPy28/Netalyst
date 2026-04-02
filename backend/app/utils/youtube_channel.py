"""
YouTube: canal vía Data API v3 + engagement del último video subido.
((likes + comentarios) / vistas del último video) × 100; misma rúbrica 0–3.
"""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import unquote, urlparse

import pandas as pd

from app.utils.social_engagement_rubric import engagement_points_0_3
from app.utils.social_vertical_format import format_vertical_phrase, normalize_youtube_topics_for_vertical

logger = logging.getLogger(__name__)

_CHANNEL_PATH = re.compile(r"/channel/([^/?#]+)", re.I)
_HANDLE_PATH = re.compile(r"/@([^/?#]+)", re.I)
_USER_PATH = re.compile(r"/user/([^/?#]+)", re.I)
_C_PATH = re.compile(r"/c/([^/?#]+)", re.I)


def is_channel_id(username: Any) -> bool:
    """True si es un ID de canal (UC…) y no un @handle."""
    if username is None or (isinstance(username, float) and pd.isna(username)):
        return False
    if not isinstance(username, str):
        u = str(username).strip()
    else:
        u = username.strip()
    if not u:
        return False
    return u.startswith("UC") and len(u) >= 24 and "@" not in u


def clean_topic_categories(cats: list[str] | None) -> str:
    """Resume topicCategories (URLs Wikipedia) a etiquetas legibles."""
    if not cats:
        return ""
    out: list[str] = []
    for url in cats:
        if not isinstance(url, str) or not url.strip():
            continue
        part = url.rstrip("/").split("/")[-1]
        part = unquote(part).replace("_", " ")
        if part:
            out.append(part)
    return "; ".join(out)


def parse_youtube_channel_reference(raw: str) -> tuple[str, str] | None:
    """
    Devuelve (modo_api, valor) para channels().list:
    - ('id', channel_id) — solo si el segmento es un ID UC… válido
    - ('handle', '@nombre') — parámetro forHandle (/c/slug, /@x, o /channel/slug cuando slug no es UC…)
    - ('username', legacy_user) — parámetro forUsername (/user/…)
    """
    s = (raw or "").strip()
    if not s:
        return None

    if is_channel_id(s):
        return ("id", s)

    lower = s.lower()
    if "youtube.com" in lower or "youtu.be" in lower:
        if not s.startswith("http"):
            s = "https://" + s
        try:
            path = unquote(urlparse(s).path)
        except Exception:  # noqa: BLE001
            return None

        m = _CHANNEL_PATH.search(path)
        if m:
            segment = m.group(1).strip()
            if is_channel_id(segment):
                return ("id", segment)
            # URLs tipo youtube.com/channel/thefashionsessions (slug, no ID UC…)
            if segment:
                return ("handle", f"@{segment.lstrip('@')}")

        m = _HANDLE_PATH.search(path)
        if m:
            return ("handle", f"@{m.group(1).strip()}")

        m = _USER_PATH.search(path)
        if m:
            return ("username", m.group(1).strip())

        m = _C_PATH.search(path)
        if m:
            return ("handle", f"@{m.group(1).strip()}")

        return None

    if s.startswith("@"):
        return ("handle", s)

    if "/" not in s and " " not in s:
        return ("handle", f"@{s.lstrip('@')}")

    return None


def _int_str(d: dict[str, Any], key: str) -> int:
    v = d.get(key)
    if v is None:
        return 0
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _normalize_video_statistics(raw: dict[str, Any]) -> dict[str, str]:
    keys = (
        "viewCount",
        "likeCount",
        "dislikeCount",
        "favoriteCount",
        "commentCount",
    )
    out: dict[str, str] = {}
    for k in keys:
        v = raw.get(k)
        out[k] = str(v) if v is not None else "0"
    return out


def _youtube_build(api_key: str) -> Any:
    from googleapiclient.discovery import build

    return build("youtube", "v3", developerKey=api_key, cache_discovery=False)


def fetch_youtube_channel_bundle(
    api_key: str,
    *,
    lookup_kind: str,
    lookup_value: str,
    request_delay: float,
) -> tuple[dict[str, Any] | None, str]:
    """
    Devuelve (payload_plano_para_flatten, error_code).
    error_code vacío si OK.
    """
    import time

    try:
        from googleapiclient.errors import HttpError
    except ImportError:
        return None, "google_api_client_missing"

    yt = _youtube_build(api_key)
    try:
        if lookup_kind == "id":
            ch_req = yt.channels().list(
                part="snippet,statistics,status,topicDetails,contentDetails",
                id=lookup_value,
                maxResults=1,
            )
        elif lookup_kind == "handle":
            ch_req = yt.channels().list(
                part="snippet,statistics,status,topicDetails,contentDetails",
                forHandle=lookup_value,
                maxResults=1,
            )
        elif lookup_kind == "username":
            ch_req = yt.channels().list(
                part="snippet,statistics,status,topicDetails,contentDetails",
                forUsername=lookup_value,
                maxResults=1,
            )
        else:
            return None, "invalid_lookup_kind"

        ch_resp = ch_req.execute()
        time.sleep(request_delay)
        items = ch_resp.get("items") or []
        if not items:
            return None, "channel_not_found"

        ch = items[0]
        channel_id = str(ch.get("id") or "")
        snippet = ch.get("snippet") or {}
        stats = ch.get("statistics") or {}
        status = ch.get("status") or {}
        topic = ch.get("topicDetails") or {}
        content = ch.get("contentDetails") or {}
        related = content.get("relatedPlaylists") or {}
        uploads_id = related.get("uploads") or ""

        hidden_subs = bool(stats.get("hiddenSubscriberCount"))
        subs = 0 if hidden_subs else _int_str(stats, "subscriberCount")

        latest_views = latest_likes = latest_comments = 0
        latest_vid = ""
        latest_title = ""
        latest_published = ""

        if uploads_id:
            pl_req = yt.playlistItems().list(
                part="contentDetails",
                playlistId=uploads_id,
                maxResults=1,
            )
            pl_resp = pl_req.execute()
            time.sleep(request_delay)
            pl_items = pl_resp.get("items") or []
            if pl_items:
                latest_vid = (
                    pl_items[0].get("contentDetails") or {}
                ).get("videoId") or ""

        if latest_vid:
            v_req = yt.videos().list(
                part="statistics,snippet",
                id=latest_vid,
            )
            v_resp = v_req.execute()
            time.sleep(request_delay)
            v_items = v_resp.get("items") or []
            if v_items:
                v0 = v_items[0]
                vstats = _normalize_video_statistics(v0.get("statistics") or {})
                vsnip = v0.get("snippet") or {}
                latest_title = str(vsnip.get("title") or "")
                latest_published = str(vsnip.get("publishedAt") or "")
                latest_views = int(vstats.get("viewCount") or 0)
                latest_likes = int(vstats.get("likeCount") or 0)
                latest_comments = int(vstats.get("commentCount") or 0)

        if latest_views > 0:
            pct = (latest_likes + latest_comments) / latest_views * 100.0
        else:
            pct = 0.0

        topics = topic.get("topicCategories")
        topic_list = topics if isinstance(topics, list) else []

        thumbs = snippet.get("thumbnails") or {}
        med_thumb = (
            thumbs.get("medium")
            or thumbs.get("high")
            or thumbs.get("default")
            or {}
        )
        thumbnail_medium_url = str(med_thumb.get("url") or "").strip()

        return (
            {
                "channel_id": channel_id,
                "title": str(snippet.get("title") or ""),
                "description": str(snippet.get("description") or ""),
                "custom_url": str(snippet.get("customUrl") or ""),
                "country": str(snippet.get("country") or ""),
                "subscriber_count": subs,
                "hidden_subscriber_count": hidden_subs,
                "video_count": _int_str(stats, "videoCount"),
                "view_count_channel": _int_str(stats, "viewCount"),
                "privacy_status": str(status.get("privacyStatus") or ""),
                "topic_categories_clean": clean_topic_categories(
                    [str(x) for x in topic_list]
                ),
                "thumbnail_medium_url": thumbnail_medium_url,
                "latest_video_id": latest_vid,
                "latest_video_title": latest_title,
                "latest_video_published_at": latest_published,
                "latest_video_views": latest_views,
                "latest_likes": latest_likes,
                "latest_comments": latest_comments,
                "engagement_pct": round(pct, 4),
            },
            "",
        )
    except HttpError as e:
        logger.warning("YouTube API HttpError: %s", e)
        time.sleep(request_delay)
        status = getattr(getattr(e, "resp", None), "status", "?")
        return None, f"http_error_{status}"
    except Exception as e:  # noqa: BLE001
        logger.warning("YouTube API error: %s", e)
        time.sleep(request_delay)
        return None, "fetch_failed"


def flatten_youtube_row(payload: dict[str, Any], *, source: str) -> dict[str, Any]:
    pct = float(payload.get("engagement_pct") or 0.0)
    pts = engagement_points_0_3(pct)
    subs = int(payload.get("subscriber_count") or 0)
    vcount = int(payload.get("video_count") or 0)
    desc = str(payload.get("description") or "")
    topic_clean = str(payload.get("topic_categories_clean") or "")
    topic_segs = normalize_youtube_topics_for_vertical(topic_clean)
    topic_display = format_vertical_phrase(topic_segs) if topic_segs else topic_clean.strip()
    thumb = str(payload.get("thumbnail_medium_url") or "").strip()
    return {
        "yt_fetch_source": source,
        "yt_fetch_error": "",
        "yt_channel_id": str(payload.get("channel_id") or ""),
        "yt_title": str(payload.get("title") or ""),
        "yt_custom_url": str(payload.get("custom_url") or ""),
        "yt_subscriber_count": subs,
        "yt_hidden_subscriber_count": bool(payload.get("hidden_subscriber_count")),
        "yt_video_count": vcount,
        "yt_view_count_channel": int(payload.get("view_count_channel") or 0),
        "yt_country": str(payload.get("country") or ""),
        "yt_privacy_status": str(payload.get("privacy_status") or ""),
        "yt_topic_categories_clean": topic_display,
        "yt_latest_video_id": str(payload.get("latest_video_id") or ""),
        "yt_latest_video_title": str(payload.get("latest_video_title") or ""),
        "yt_latest_video_published_at": str(payload.get("latest_video_published_at") or ""),
        "yt_latest_video_views": int(payload.get("latest_video_views") or 0),
        "yt_latest_likes": int(payload.get("latest_likes") or 0),
        "yt_latest_comments": int(payload.get("latest_comments") or 0),
        "yt_engagement_pct": pct,
        "yt_engagement_points_0_3": pts,
        "youtube_followers": subs,
        "youtube_post_count": vcount,
        "youtube_picture": thumb,
        "youtube_bio": desc,
        "youtube_category": topic_display,
        "youtube_verified": False,
    }


def empty_yt_row(*, source: str = "skipped", error: str = "") -> dict[str, Any]:
    return {
        "yt_fetch_source": source,
        "yt_fetch_error": error,
        "yt_channel_id": "",
        "yt_title": "",
        "yt_custom_url": "",
        "yt_subscriber_count": 0,
        "yt_hidden_subscriber_count": False,
        "yt_video_count": 0,
        "yt_view_count_channel": 0,
        "yt_country": "",
        "yt_privacy_status": "",
        "yt_topic_categories_clean": "",
        "yt_latest_video_id": "",
        "yt_latest_video_title": "",
        "yt_latest_video_published_at": "",
        "yt_latest_video_views": 0,
        "yt_latest_likes": 0,
        "yt_latest_comments": 0,
        "yt_engagement_pct": 0.0,
        "yt_engagement_points_0_3": 0,
        "youtube_followers": 0,
        "youtube_post_count": 0,
        "youtube_picture": "",
        "youtube_bio": "",
        "youtube_category": "",
        "youtube_verified": False,
    }
