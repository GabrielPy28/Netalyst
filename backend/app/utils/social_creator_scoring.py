"""
Score total creador 0–16 (crietiors_instagram.md):
  suma engagement IG + TT + YT (0–3 cada uno) + tier seguidores (0–2)
  + plataformas activas (0–2) + completitud (0–2) + actividad 30 días (0–1).

Bandas: 13–16 prioritario, 8–12 estándar, 1–7 baja prioridad.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from app.utils.social_engagement_rubric import active_platform_count_points, follower_tier_points_0_2


def _nonempty(val: Any) -> bool:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    s = str(val).strip().lower()
    return bool(s) and s not in {"nan", "none"}


def parse_iso_datetime(val: Any) -> datetime | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        pass
    try:
        ts = pd.to_datetime(s, utc=True, errors="coerce")
        if pd.isna(ts):
            return None
        return ts.to_pydatetime()
    except Exception:  # noqa: BLE001
        return None


def content_within_days(val: Any, *, days: int) -> bool:
    dt = parse_iso_datetime(val)
    if dt is None:
        return False
    return dt >= datetime.now(timezone.utc) - timedelta(days=days)


def count_active_platforms_row(row: pd.Series) -> int:
    n = 0
    if _nonempty(row.get("instagram_url")) or _nonempty(row.get("instagram_username")):
        n += 1
    if _nonempty(row.get("tiktok_username")):
        n += 1
    if _nonempty(row.get("youtube_channel_url")) or _nonempty(row.get("youtube_channel")):
        n += 1
    return n


def max_followers_across_fetched(row: pd.Series) -> int:
    vals: list[int] = []
    for key in ("ig_followers", "tt_followers", "yt_subscriber_count"):
        try:
            v = row.get(key)
            if v is not None and not (isinstance(v, float) and pd.isna(v)):
                vals.append(int(v))
        except (TypeError, ValueError):
            continue
    return max(vals) if vals else 0


def completeness_points_0_2(row: pd.Series) -> float:
    """
    Nombre + vertical + handle(s) + país + email = 1.25 (proporcional si faltan).
    Teléfono (+0.75 bonus), tope 2.0.
    """
    name_ok = _nonempty(row.get("full_name")) or (
        _nonempty(row.get("first_name")) and _nonempty(row.get("last_name"))
    )
    vertical_ok = (
        _nonempty(row.get("vertical"))
        or _nonempty(row.get("category"))
        or _nonempty(row.get("instagram_category"))
        or _nonempty(row.get("tiktok_category"))
        or _nonempty(row.get("youtube_category"))
    )
    handles_ok = (
        _nonempty(row.get("instagram_url"))
        or _nonempty(row.get("instagram_username"))
        or _nonempty(row.get("tiktok_username"))
        or _nonempty(row.get("youtube_channel_url"))
        or _nonempty(row.get("youtube_channel"))
    )
    country_ok = (
        _nonempty(row.get("country"))
        or _nonempty(row.get("pais"))
        or _nonempty(row.get("yt_country"))
    )
    email_ok = _nonempty(row.get("email"))

    checks = [name_ok, vertical_ok, handles_ok, country_ok, email_ok]
    met = sum(1 for x in checks if x)
    base = 1.25 * (met / 5.0) if checks else 0.0

    phone_ok = False
    for col in ("phone", "telefono", "tel", "mobile", "phone_number"):
        if _nonempty(row.get(col)):
            phone_ok = True
            break
    bonus = 0.75 if phone_ok else 0.0
    return round(min(2.0, base + bonus), 4)


def recent_activity_30d_points(row: pd.Series) -> int:
    if content_within_days(row.get("ig_latest_content_at"), days=30):
        return 1
    if content_within_days(row.get("tt_latest_content_at"), days=30):
        return 1
    if content_within_days(row.get("yt_latest_video_published_at"), days=30):
        return 1
    return 0


def priority_band(total: float) -> str:
    if total >= 13:
        return "priority_13_16"
    if total >= 8:
        return "standard_8_12"
    if total >= 1:
        return "low_1_7"
    return "minimal_0"


def main_platform_for_row(row: pd.Series) -> tuple[str, int]:
    """Cuenta principal = la red con más seguidores según datos obtenidos (ig/tt/yt)."""
    pairs: list[tuple[str, int]] = []
    for key, label in (
        ("ig_followers", "instagram"),
        ("tt_followers", "tiktok"),
        ("yt_subscriber_count", "youtube"),
    ):
        try:
            v = row.get(key)
            n = 0 if v is None or (isinstance(v, float) and pd.isna(v)) else int(v)
        except (TypeError, ValueError):
            n = 0
        pairs.append((label, n))
    best = max(pairs, key=lambda x: x[1])
    return best[0], best[1]


def row_creator_score(row: pd.Series) -> dict[str, Any]:
    ig = int(row.get("ig_engagement_points_0_3") or 0)
    tt = int(row.get("tt_engagement_points_0_3") or 0)
    yt = int(row.get("yt_engagement_points_0_3") or 0)
    eng_sum = ig + tt + yt

    max_f = max_followers_across_fetched(row)
    main_pl, main_fc = main_platform_for_row(row)
    f_pts = follower_tier_points_0_2(max_f)

    ap_n = count_active_platforms_row(row)
    ap_pts = active_platform_count_points(ap_n)

    comp_pts = completeness_points_0_2(row)
    rec_pts = recent_activity_30d_points(row)

    total = round(eng_sum + f_pts + ap_pts + comp_pts + rec_pts, 4)
    band = priority_band(total)

    return {
        "creator_engagement_ig_points": ig,
        "creator_engagement_tt_points": tt,
        "creator_engagement_yt_points": yt,
        "creator_engagement_sum_0_9": eng_sum,
        "creator_max_followers_for_tier": max_f,
        "creator_main_platform": main_pl,
        "creator_main_platform_followers": main_fc,
        "creator_follower_tier_points_0_2": f_pts,
        "creator_active_platform_count": ap_n,
        "creator_platform_points_0_2": ap_pts,
        "creator_completeness_points_0_2": comp_pts,
        "creator_recent_activity_30d_points_0_1": rec_pts,
        "creator_score_total_0_16": total,
        "creator_priority_band": band,
    }


def ensure_creator_score_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Añade columnas de score y cuenta principal si aún no existen."""
    need = any(
        c not in df.columns
        for c in (
            "creator_score_total_0_16",
            "creator_main_platform",
            "creator_main_platform_followers",
        )
    )
    if not need:
        return df
    out = df.copy()
    parts = [row_creator_score(row) for _, row in df.iterrows()]
    sdf = pd.DataFrame(parts)
    for c in sdf.columns:
        out[c] = sdf[c].values
    return out
