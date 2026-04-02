"""
Patrones en email (dominio / local) que marcan revisión manual.
No elimina filas: solo etiqueta (email_pattern_flag, email_pattern_hits).
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

# Subcadenas a buscar en el email completo en minúsculas (instrucciones + typos comunes).
_EMAIL_SUBSTRING_HITS: tuple[str, ...] = (
    "university",
    "support",
    "retails",
    "retail",
    "deals",
    "museum",
    "museoum",
    "state.",
    "state.gov",
    "government",
    "goverment",
    "llc",
    "reservations",
    "client",
    "customer",
    "noreply",
    "notreplay",
    "no-reply",
    "hyundai",
    "mattel",
    "hasbro",
    "universal",
    "newyorktimes",
    "shop",
    "sales",
    "ships",
    "group",
    "store",
    "boutique",
    "association",
    "ministry",
    "church",
    "foundation",
    "fundation",
    "school",
    "department",
    "media",
    "agency",
    "studio",
    "productions",
    "entertainment",
    "athletics",
    "warriors",
    "eagles",
    "raiders",
    "patriots",
    "football",
    "soccer",
    "basketball",
    # ligas / equipos (puede dar falsos positivos; revisar manualmente si aplica)
    "@fc.",
    ".fc.",
    "-fc-",
    "nfl",
    "nba",
    "mlb",
    "nhl",
)


def _safe_email_str(v: Any) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def _domain_tld_flags(domain: str) -> list[str]:
    hits: list[str] = []
    d = domain.lower()
    if d.endswith(".org"):
        hits.append("tld_org")
    if d.endswith(".ong"):
        hits.append("tld_ong")
    return hits


def _substring_hits(email_lower: str) -> list[str]:
    found: list[str] = []
    for sub in _EMAIL_SUBSTRING_HITS:
        if sub in email_lower:
            found.append(sub)
    # "info" como palabra de negocio: local genérico info@ o .info. en local
    local = email_lower.split("@", 1)[0] if "@" in email_lower else email_lower
    if local in ("info", "hello", "contact", "team", "support"):
        found.append("generic_local")
    elif re.match(r"^info[\d._-]", local) or local.startswith("info."):
        found.append("info_prefix_local")
    return found


def screen_email_row(email: Any) -> tuple[bool, str]:
    """
    Devuelve (flagged, hits_csv).
    flagged=True → no se envía a Hunter en el paso siguiente (revisión manual).
    """
    raw = _safe_email_str(email)
    if not raw or "@" not in raw:
        return True, "invalid_or_empty"

    parts = raw.rsplit("@", 1)
    if len(parts) != 2:
        return True, "invalid_or_empty"
    local, domain = parts[0].lower(), parts[1].lower()
    email_lower = f"{local}@{domain}"

    hits: list[str] = []
    hits.extend(_domain_tld_flags(domain))
    hits.extend(_substring_hits(email_lower))
    seen: set[str] = set()
    uniq: list[str] = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            uniq.append(h)

    if uniq:
        return True, ";".join(uniq)
    return False, ""


def add_email_pattern_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    out = df.copy()
    flags: list[bool] = []
    hit_strs: list[str] = []
    for _, row in out.iterrows():
        f, h = screen_email_row(row.get("email"))
        flags.append(f)
        hit_strs.append(h)
    out["email_pattern_flag"] = flags
    out["email_pattern_hits"] = hit_strs
    n_flagged = sum(flags)
    stats = {
        "rows": len(out),
        "email_pattern_flagged": int(n_flagged),
        "email_pattern_clear": int(len(out) - n_flagged),
    }
    return out, stats
