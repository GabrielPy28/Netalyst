"""Formato de la columna `vertical` según reglas de negocio (minúsculas, hasta 3 términos)."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd


def _norm_segment(s: str) -> str:
    t = s.strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t


def split_category_segments(raw: Any) -> list[str]:
    """Parte categorías tipo YouTube ('a; b') o listas separadas por coma."""
    if raw is None:
        return []
    try:
        if pd.isna(raw):
            return []
    except (TypeError, ValueError):
        pass
    s = str(raw).strip()
    if not s or s.lower() in {"nan", "none"}:
        return []
    if ";" in s:
        parts = re.split(r"\s*;\s*", s)
    elif "," in s:
        parts = re.split(r"\s*,\s*", s)
    else:
        parts = [s]
    out: list[str] = []
    for p in parts:
        n = _norm_segment(p)
        if n:
            out.append(n)
    return out


def normalize_youtube_topics_for_vertical(raw: Any) -> list[str]:
    """
    Limpia topicCategories ya resumidas (p. ej. desde Wikipedia paths):
    - "Lifestyle (sociology)" → lifestyle
    - "Video game culture; Sports game" → una frase "video game culture and sports game"
    """
    segs = split_category_segments(raw)
    if not segs:
        return []
    cleaned: list[str] = []
    for s in segs:
        t = str(s).strip()
        t = re.sub(r"\s*\([^)]+\)\s*$", "", t).strip()
        n = _norm_segment(t)
        if n:
            cleaned.append(n)
    if not cleaned:
        return []
    blob = " ".join(cleaned).lower()
    if "video game" in blob and "sports game" in blob:
        return ["video game culture and sports game"]
    return cleaned


def format_vertical_phrase(segments: list[str]) -> str:
    """
    - 3 términos: "lifestyle, travel and humor"
    - 2: "lifestyle and travel"
    - 1: el valor en minúsculas
    """
    seen: set[str] = set()
    uniq: list[str] = []
    for seg in segments:
        n = _norm_segment(seg)
        if not n or n in seen:
            continue
        seen.add(n)
        uniq.append(n)
        if len(uniq) >= 3:
            break
    if len(uniq) >= 3:
        return f"{uniq[0]}, {uniq[1]} and {uniq[2]}"
    if len(uniq) == 2:
        return f"{uniq[0]} and {uniq[1]}"
    if len(uniq) == 1:
        return uniq[0]
    return ""
