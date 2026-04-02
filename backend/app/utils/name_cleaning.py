"""
Normalización de full_name / first_name según clean_full_names.md.
Usa pandas + python-nameparser (HumanName).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

import pandas as pd
from nameparser import HumanName

# Prefijos de una palabra (comparar sin puntuación final).
_SINGLE_PREFIXES: frozenset[str] = frozenset(
    {
        "dr",
        "doctor",
        "mr",
        "mrs",
        "ms",
        "miss",
        "sir",
        "madam",
        "chef",
        "official",
        "ing",
        "lic",
        "mg",
        "the",
        "hey",
        "come",
        "actrice",
        "actress",
        "actor",
        "couch",
        "coach",
        "designer",
        "beby",
        "baby",
        "hot",
    }
)

# Frases al inicio (minúsculas) que se eliminan de una vez.
_PHRASE_PREFIXES: tuple[str, ...] = (
    "hello i'm ",
    "hello im ",
    "this is ",
    "hi i'm ",
    "hi im ",
    "is",
    "i'm",
    "i am"
)

# Inicios tipo marca / frase comercial → fallback a username.
_BRANDISH_STARTS: tuple[str, ...] = (
    "home of ",
    "welcome to ",
    "its all ",
    "it's all ",
    "the world of ",
    "world of ",
    "the official ",
    "official ",
)

_GENERIC_EMAIL_LOCALS: frozenset[str] = frozenset(
    {
        "partners",
        "info",
        "contact",
        "hello",
        "team",
        "support",
        "sales",
        "media",
        "booking",
        "press",
    }
)

_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "\U0001F1E0-\U0001F1FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "]+",
    flags=re.UNICODE,
)
_ZWJ_VS_RE = re.compile("[\ufe0f\u200d]+")


def _safe_str(v: Any) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def _clean_surface_text(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = _ZWJ_VS_RE.sub("", s)
    s = _EMOJI_RE.sub("", s)
    s = re.sub(r"^[!?.…\s·|]+", "", s)
    s = s.replace("_", " ").replace("-", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _strip_phrase_prefixes(s: str) -> str:
    low = s.lower()
    for p in _PHRASE_PREFIXES:
        if low.startswith(p):
            s = s[len(p) :].strip()
            low = s.lower()
    return s


def _strip_single_token_prefixes(s: str) -> str:
    tokens = s.split()
    while tokens:
        norm = tokens[0].lower().rstrip(".:;!?")
        if norm in _SINGLE_PREFIXES:
            tokens.pop(0)
            continue
        break
    return " ".join(tokens)


def _strip_leading_lowercase_singletons(s: str) -> str:
    """Quita basura tipo 'a a Alaina…' o 'c Cassiee' (iniciales sueltas en minúscula)."""
    tokens = s.split()
    while tokens:
        t0 = tokens[0]
        if len(t0) == 1 and t0.isalpha() and t0.islower():
            tokens.pop(0)
            continue
        break
    return " ".join(tokens)


def clean_display_string(s: str) -> str:
    s = _clean_surface_text(s)
    s = _strip_phrase_prefixes(s)
    s = _strip_leading_lowercase_singletons(s)
    s = _strip_single_token_prefixes(s)
    s = re.sub(r"\s+", " ", s).strip()
    if s.isupper() and len(s) > 2:
        s = s.title()
    return s


def _infer_from_email_local(email: str) -> str:
    if not email or "@" not in email:
        return ""
    local = email.rsplit("@", 1)[0].strip()
    local = local.split("+")[0].strip()
    if local.lower() in _GENERIC_EMAIL_LOCALS:
        return ""
    guess = local.replace(".", " ").replace("_", " ")
    guess = re.sub(r"\s+", " ", guess).strip()
    if not guess or not any(c.isalpha() for c in guess):
        return ""
    if guess.isdigit():
        return ""
    return guess


def _bio_name_candidate(bio: str) -> str:
    if not bio:
        return ""
    line = bio.split("\n")[0].strip()
    if len(line) > 80:
        return ""
    words = line.split()
    if not words or len(words) > 4:
        return ""
    for w in words:
        letters = sum(c.isalpha() for c in w)
        if len(w) > 1 and letters < len(w) * 0.4:
            return ""
    return line


def pick_primary_raw(
    full_name: str, email: Any, bio: str
) -> tuple[str, str]:
    """Devuelve (texto crudo a parsear, fuente: full_name|email_local|instagram_bio)."""
    fn = _safe_str(full_name)
    if fn and clean_display_string(fn):
        return fn, "full_name"
    eg = _infer_from_email_local(_safe_str(email))
    if eg:
        return eg, "email_local"
    bc = _bio_name_candidate(_safe_str(bio))
    if bc:
        return bc, "instagram_bio"
    if fn:
        return fn, "full_name"
    return "", ""


def _brandish_line(tokens: list[str], lowered_joined: str) -> bool:
    for p in _BRANDISH_STARTS:
        if lowered_joined.startswith(p):
            return True
    return False


def should_fallback_to_username(cleaned: str, tokens: list[str]) -> bool:
    if not tokens:
        return True
    joined = " ".join(tokens)
    low = joined.lower()
    if _brandish_line(tokens, low):
        return True
    first = tokens[0]
    if len(first) == 1 and first.isalpha() and len(tokens) >= 2:
        return True
    if "*" in first:
        return True
    if "_" in first and len(first) > 4:
        return True
    return False


def _username_display(username: str) -> tuple[str, str]:
    u = _safe_str(username).lstrip("@")
    if not u:
        return "", ""
    d = f"@{u}"
    return d, d


def _compose_display_full(hn: HumanName, cleaned: str) -> str:
    parts = [p for p in [hn.title, hn.first, hn.middle, hn.last, hn.suffix] if p]
    if parts:
        out = " ".join(parts)
        out = re.sub(r"\s+", " ", out).strip()
        if out:
            return out
    return cleaned


def _word_capitalize_phrase(s: str) -> str:
    if not s or s.startswith("@"):
        return s
    return " ".join(w.capitalize() for w in s.split())


def _first_from_human_name(hn: HumanName, cleaned: str) -> str:
    first = (hn.first or "").strip()
    if first:
        return first
    mid = (hn.middle or "").strip()
    if mid:
        return mid.split()[0]
    toks = cleaned.split()
    return toks[0] if toks else ""


def _should_prefer_ig_full_name(cur: str, ig: str) -> bool:
    if not ig or len(ig.strip()) < 2:
        return False
    cur = cur.strip()
    if not cur:
        return True
    parts = cur.split()
    if parts and len(parts[0]) == 1 and parts[0].isalpha() and parts[0].islower():
        return True
    if re.match(r"^(?:[a-z]\s+){2,}", cur):
        return True
    return False


def process_name_row(row: pd.Series) -> tuple[str, str, str, str]:
    """
    Devuelve (full_name_display, first_name, last_name, source).
    source ∈ full_name | ig_full_name_raw | email_local | instagram_bio | username_fallback | kept_first_name
    """
    username = row.get("username")
    email = row.get("email")
    bio = row.get("instagram_bio")
    full_orig = _safe_str(row.get("full_name"))
    first_orig = _safe_str(row.get("first_name"))
    ig_fn = _safe_str(row.get("ig_full_name_raw"))

    if ig_fn and _should_prefer_ig_full_name(full_orig, ig_fn):
        raw, src = ig_fn, "ig_full_name_raw"
    else:
        raw, src = pick_primary_raw(full_orig, email, bio)
    cleaned = clean_display_string(raw) if raw else ""
    tokens = cleaned.split() if cleaned else []

    if should_fallback_to_username(cleaned, tokens):
        ff, fn = _username_display(_safe_str(username))
        if ff:
            return ff, fn, "", "username_fallback"
        if first_orig:
            return full_orig or cleaned, first_orig, "", "kept_first_name"
        return cleaned, cleaned, "", src or "empty"

    hn = HumanName(cleaned)
    display_full = _compose_display_full(hn, cleaned)
    display_full = clean_display_string(display_full) or cleaned
    first_out = _first_from_human_name(hn, cleaned)
    last_out = (hn.last or "").strip()
    if first_out:
        if first_out.isupper() and len(first_out) > 1:
            first_out = first_out.title()
    else:
        first_out = first_orig or ""

    if not display_full and first_out:
        display_full = first_out

    display_full = _word_capitalize_phrase(display_full)
    if first_out and not first_out.startswith("@"):
        first_out = first_out.capitalize() if " " not in first_out else _word_capitalize_phrase(first_out)
    if last_out and not last_out.startswith("@"):
        last_out = (
            last_out.capitalize() if " " not in last_out else _word_capitalize_phrase(last_out)
        )

    return display_full, first_out, last_out, src


def normalize_creator_names(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Actualiza full_name, first_name, last_name y añade name_cleaning_source.
    Devuelve (df, estadísticas).
    """
    out = df.copy()
    displays: list[str] = []
    firsts: list[str] = []
    lasts: list[str] = []
    sources: list[str] = []
    for _, row in out.iterrows():
        d, f, l, s = process_name_row(row)
        displays.append(d)
        firsts.append(f)
        lasts.append(l)
        sources.append(s)
    out["full_name"] = displays
    out["first_name"] = firsts
    out["last_name"] = lasts
    out["name_cleaning_source"] = sources
    counts = pd.Series(sources).value_counts().to_dict()
    stats = {"rows": len(out), "by_source": {str(k): int(v) for k, v in counts.items()}}
    return out, stats


def maybe_refresh_names_from_instagram_fetch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tras traer ig_full_name_raw: si el full_name del archivo tenía basura tipo 'a a …',
    reemplaza por el nombre del perfil y vuelve a normalizar.
    """
    if "ig_full_name_raw" not in df.columns or "full_name" not in df.columns:
        return df
    copy = df.copy()
    changed = False
    for idx in copy.index:
        ig = _safe_str(copy.at[idx, "ig_full_name_raw"])
        if not ig:
            continue
        cur = _safe_str(copy.at[idx, "full_name"])
        if _should_prefer_ig_full_name(cur, ig):
            copy.at[idx, "full_name"] = ig
            changed = True
    if not changed:
        return df
    out, _ = normalize_creator_names(copy)
    return out
