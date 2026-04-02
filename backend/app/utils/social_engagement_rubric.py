"""Rúbricas compartidas: engagement 0–3 y tier de seguidores (crietiors_instagram.md)."""


def engagement_points_0_3(pct: float) -> int:
    if pct < 0.5:
        return 0
    if pct < 1.5:
        return 1
    if pct <= 3.0:
        return 2
    return 3


def follower_tier_points_0_2(max_followers: int) -> float:
    """Seguidores máximos entre redes (0–2 pts). <100K → 0."""
    f = int(max_followers or 0)
    if f < 100_000:
        return 0.0
    if f < 500_000:
        return 0.5
    if f < 1_000_000:
        return 1.0
    if f < 5_000_000:
        return 1.5
    return 2.0


def active_platform_count_points(active_count: int) -> float:
    """Plataformas activas con presencia declarada (0–2 pts)."""
    n = int(active_count or 0)
    if n <= 0:
        return 0.0
    if n == 1:
        return 0.5
    if n == 2:
        return 1.0
    return 2.0
