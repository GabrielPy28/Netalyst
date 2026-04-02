"""
Instagram: perfil + engagement ≈ (likes + comentarios en muestra de posts) / seguidores × 100.
Fuentes: Apify (actor Instagram Scraper) o Instaloader como respaldo.
"""

from __future__ import annotations

import logging
from datetime import timezone
from typing import Any
from urllib.parse import urlparse

from app.utils.social_engagement_rubric import engagement_points_0_3

logger = logging.getLogger(__name__)


def instagram_engagement_points(pct: float) -> int:
    """Rúbrica crietiors_instagram.md (0–3 pts)."""
    return engagement_points_0_3(pct)


def parse_instagram_handle_from_url(url: str) -> str | None:
    if not url or not str(url).strip():
        return None
    u = str(url).strip()
    if not u.startswith("http"):
        u = "https://" + u
    try:
        path = urlparse(u).path.strip("/")
    except Exception:  # noqa: BLE001
        return None
    if not path:
        return None
    first = path.split("/")[0].lower()
    if first in {"p", "reel", "reels", "stories", "explore", "tv"}:
        return None
    return path.split("/")[0] or None


def normalize_instagram_profile_url(url_or_handle: str) -> str | None:
    s = (url_or_handle or "").strip()
    if not s:
        return None
    if s.startswith("http://") or s.startswith("https://"):
        return s.split("?")[0].rstrip("/") + "/"
    h = s.lstrip("@")
    return f"https://www.instagram.com/{h}/"


def _latest_post_timestamp_iso(posts: list[dict[str, Any]]) -> str:
    if not posts:
        return ""
    ts = posts[0].get("timestamp")
    return str(ts).strip() if ts is not None else ""


def _engagement_from_posts(followers: int, posts: list[dict[str, Any]], max_posts: int) -> tuple[int, int, int, float]:
    likes = comments = 0
    n = 0
    for p in posts:
        if n >= max_posts:
            break
        likes += int(p.get("likesCount") or 0)
        comments += int(p.get("commentsCount") or 0)
        n += 1
    if followers <= 0:
        return likes, comments, n, 0.0
    pct = (likes + comments) / followers * 100.0
    return likes, comments, n, round(pct, 4)


def fetch_instagram_apify(
    profile_url: str,
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

    client = ApifyClient(token)
    run_input: dict[str, Any] = {
        "directUrls": [profile_url],
        "resultsType": "posts",
        "resultsLimit": max(1, max_posts),
        "addParentData": True,
    }
    try:
        run = client.actor(actor_id).call(run_input=run_input)
        ds = run.get("defaultDatasetId")
        if not ds:
            return None
        item: dict[str, Any] | None = None
        for it in client.dataset(ds).iterate_items():
            if isinstance(it, dict) and it.get("username"):
                item = it
                break
            item = it if isinstance(it, dict) else item
        return item
    except Exception as e:  # noqa: BLE001
        logger.warning("Apify Instagram error %s: %s", profile_url, e)
        return None


def fetch_instagram_instaloader(
    handle: str,
    *,
    loader: Any,
    max_posts: int,
) -> dict[str, Any] | None:
    from instaloader import Profile

    try:
        profile = Profile.from_username(loader.context, handle)
    except Exception as e:  # noqa: BLE001
        logger.warning("Instaloader perfil %s: %s", handle, e)
        return None

    followers = int(profile.followers)
    likes = comments = n = 0
    latest_iso = ""
    try:
        for post in profile.get_posts():
            if not latest_iso and getattr(post, "date_utc", None):
                du = post.date_utc
                if du.tzinfo is None:
                    du = du.replace(tzinfo=timezone.utc)
                else:
                    du = du.astimezone(timezone.utc)
                latest_iso = du.isoformat()
            likes += int(post.likes)
            comments += int(post.comments)
            n += 1
            if n >= max_posts:
                break
    except Exception as e:  # noqa: BLE001
        logger.warning("Instaloader posts %s: %s", handle, e)

    pct = (likes + comments) / followers * 100.0 if followers > 0 else 0.0
    pic = str(getattr(profile, "profile_pic_url", None) or "").strip()
    try:
        total_posts = int(getattr(profile, "mediacount", 0) or 0)
    except (TypeError, ValueError):
        total_posts = 0
    return {
        "username": profile.username,
        "fullName": profile.full_name,
        "biography": profile.biography,
        "followersCount": followers,
        "verified": profile.is_verified,
        "businessCategoryName": getattr(profile, "business_category_name", None),
        "profilePicUrlHD": pic,
        "postsCount": total_posts,
        "_likes_sum": likes,
        "_comments_sum": comments,
        "_posts_sampled": n,
        "_engagement_pct": round(pct, 4),
        "_latest_content_at": latest_iso,
    }


def _extract_total_posts_count(item: dict[str, Any]) -> int:
    """Total de publicaciones del perfil (p. ej. postsCount de Apify / GraphQL)."""
    for key in ("postsCount", "posts_count", "totalPosts", "posts", "mediaCount", "edge_media_count"):
        v = item.get(key)
        if v is not None:
            try:
                n = int(v)
                if n >= 0:
                    return n
            except (TypeError, ValueError):
                pass
    for nested_key in ("owner", "profile", "user", "author"):
        sub = item.get(nested_key)
        if not isinstance(sub, dict):
            continue
        edge = sub.get("edge_owner_to_timeline_media")
        if isinstance(edge, dict) and edge.get("count") is not None:
            try:
                return int(edge["count"])
            except (TypeError, ValueError):
                pass
        for key in ("postsCount", "posts_count", "mediaCount"):
            v = sub.get(key)
            if v is not None:
                try:
                    n = int(v)
                    if n >= 0:
                        return n
                except (TypeError, ValueError):
                    pass
    return 0


def _instagram_profile_picture_url(item: dict[str, Any]) -> str:
    for k in ("profilePicUrlHD", "profilePicUrl", "profile_pic_url"):
        v = item.get(k)
        if v and str(v).strip():
            return str(v).strip()
    return ""


def flatten_instagram_item(item: dict[str, Any], *, source: str, max_posts: int) -> dict[str, Any]:
    """Fila uniforme para pandas (columnas iguales Apify / Instaloader)."""
    if item.get("_posts_sampled") is not None:
        followers = int(item.get("followersCount") or 0)
        likes = int(item.get("_likes_sum") or 0)
        comments = int(item.get("_comments_sum") or 0)
        posts_n = int(item.get("_posts_sampled") or 0)
        pct = float(item.get("_engagement_pct") or 0.0)
        latest_at = str(item.get("_latest_content_at") or "")
    else:
        followers = int(item.get("followersCount") or 0)
        posts = item.get("latestPosts") or []
        likes, comments, posts_n, pct = _engagement_from_posts(followers, posts, max_posts)
        latest_at = _latest_post_timestamp_iso(posts)

    posts_total = _extract_total_posts_count(item)
    post_count_out = posts_total if posts_total > 0 else posts_n

    pts = instagram_engagement_points(pct)
    pic = _instagram_profile_picture_url(item)
    bio = str(item.get("biography") or "")
    cat_str = str(item.get("businessCategoryName") or "").strip()
    verified = bool(item.get("verified"))
    return {
        "ig_fetch_source": source,
        "ig_fetch_error": "",
        "ig_username_resolved": str(item.get("username") or ""),
        "ig_followers": followers,
        "ig_full_name_raw": str(item.get("fullName") or ""),
        "ig_biography": bio,
        "ig_verified": verified,
        "ig_business_category_name": item.get("businessCategoryName"),
        "ig_posts_sampled": posts_n,
        "ig_likes_sum": likes,
        "ig_comments_sum": comments,
        "ig_engagement_pct": pct,
        "ig_engagement_points_0_3": pts,
        "ig_latest_content_at": latest_at,
        "instagram_followers": followers,
        "instagram_post_count": post_count_out,
        "instagram_picture": pic,
        "instagram_bio": bio,
        "instagram_category": cat_str,
        "instagram_verified": verified,
    }


def empty_ig_row(*, source: str = "skipped", error: str = "") -> dict[str, Any]:
    return {
        "ig_fetch_source": source,
        "ig_fetch_error": error,
        "ig_username_resolved": "",
        "ig_followers": 0,
        "ig_full_name_raw": "",
        "ig_biography": "",
        "ig_verified": False,
        "ig_business_category_name": None,
        "ig_posts_sampled": 0,
        "ig_likes_sum": 0,
        "ig_comments_sum": 0,
        "ig_engagement_pct": 0.0,
        "ig_engagement_points_0_3": 0,
        "ig_latest_content_at": "",
        "instagram_followers": 0,
        "instagram_post_count": 0,
        "instagram_picture": "",
        "instagram_bio": "",
        "instagram_category": "",
        "instagram_verified": False,
    }
