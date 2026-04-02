"""
Pasos de filtrado: mueven filas de ctx.df a ctx.df_excluded con etapa y razón.
Orden esperado: tras redes+score → Facebook → nombres → Hunter.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.core.config import settings
from app.services.validation_context import ValidationContext
from app.utils.exclusion_pipeline import (
    STAGE_EMAIL,
    STAGE_FACEBOOK,
    STAGE_SOCIAL,
    append_excluded,
)
from app.utils.social_creator_scoring import ensure_creator_score_columns


def _log(ctx: ValidationContext, step_key: str, message: str, **extra: Any) -> None:
    ctx.logs.append({"funcion": step_key, "message": message, **extra})


HUNTER_REASON_ES: dict[str, str] = {
    "ok": "",
    "pattern_flag": "Email marcado por patrón institucional/negocio",
    "invalid_email": "Email inválido o vacío",
    "no_api_key": "HUNTER_API_KEY no configurada",
    "max_calls": "Límite de llamadas Hunter alcanzado en esta corrida",
    "api_error": "Error de API Hunter",
    "hunter_rules_failed": "No supera la verificación Hunter (score o estado)",
}


def gate_social_followers_and_min_score(ctx: ValidationContext) -> ValidationContext:
    """
    Tras obtener datos de redes y el score 0–16:
    - Excluye si la cuenta con más seguidores tiene < 100k (configurable).
    - Excluye si el score total < creator_min_approval_score.
    """
    key = "gate_social_followers_and_min_score"
    df = ensure_creator_score_columns(ctx.df.copy())
    min_f = int(settings.creator_min_followers_for_approval)
    min_score = float(settings.creator_min_approval_score)

    fail_followers = df["creator_main_platform_followers"] < min_f
    ex_f = df.loc[fail_followers]
    append_excluded(
        ctx,
        ex_f,
        STAGE_SOCIAL,
        f"La cuenta principal tiene menos de {min_f:,} seguidores",
    )
    df = df.loc[~fail_followers].reset_index(drop=True)

    fail_score = df["creator_score_total_0_16"] < min_score
    ex_s = df.loc[fail_score]
    append_excluded(
        ctx,
        ex_s,
        STAGE_SOCIAL,
        f"Puntaje total inferior al mínimo de aprobación ({min_score})",
    )
    df = df.loc[~fail_score].reset_index(drop=True)

    _log(
        ctx,
        key,
        "Filtro redes: seguidores mínimos y puntaje de aprobación.",
        ok=True,
        min_followers=min_f,
        min_score=min_score,
        remaining_rows=len(df),
        excluded_followers=int(fail_followers.sum()),
        excluded_score=int(fail_score.sum()),
    )
    ctx.df = df
    return ctx


def gate_facebook_recent_reel_exclusions(ctx: ValidationContext) -> ValidationContext:
    """Excluye creadores con Reel reciente en Facebook (fb_exclude_per_recent_reel_rule)."""
    key = "gate_facebook_recent_reel_exclusions"
    df = ctx.df.copy()
    col = "fb_exclude_per_recent_reel_rule"
    if col not in df.columns:
        _log(
            ctx,
            key,
            "Sin columnas Facebook; omitir gate (ejecute fetch_facebook_recent_reel_activity).",
            skipped=True,
        )
        return ctx

    months = int(settings.facebook_reel_lookback_months)
    mask_ex = df[col].fillna(False).astype(bool)
    ex = df.loc[mask_ex]
    append_excluded(
        ctx,
        ex,
        STAGE_FACEBOOK,
        f"Actividad reciente: Reel en Facebook en los últimos {months} meses",
    )
    df = df.loc[~mask_ex].reset_index(drop=True)
    _log(
        ctx,
        key,
        "Filtro Facebook Reels.",
        ok=True,
        excluded=int(mask_ex.sum()),
        remaining_rows=len(df),
    )
    ctx.df = df
    return ctx


def gate_email_hunter_failures(ctx: ValidationContext) -> ValidationContext:
    """Excluye filas que no pasan Hunter (tras screen_email_patterns + hunter_verify_emails)."""
    key = "gate_email_hunter_failures"
    df = ctx.df.copy()
    if "email_hunter_passed" not in df.columns:
        _log(
            ctx,
            key,
            "Falta email_hunter_passed; ejecute hunter_verify_emails antes.",
            ok=False,
        )
        raise ValueError(
            "Ejecute screen_email_patterns y hunter_verify_emails antes de gate_email_hunter_failures."
        )

    ok_mask = df["email_hunter_passed"].fillna(False).astype(bool)
    ex = df.loc[~ok_mask].copy()
    if "email_hunter_skip_reason" in ex.columns:
        sr_col = ex["email_hunter_skip_reason"].fillna("").astype(str)
    else:
        sr_col = pd.Series("", index=ex.index)
    reasons = sr_col.map(lambda x: HUNTER_REASON_ES.get(x, f"Verificación email: {x}"))
    append_excluded(ctx, ex, STAGE_EMAIL, reasons)
    df = df.loc[ok_mask].reset_index(drop=True)
    _log(
        ctx,
        key,
        "Filtro email Hunter.",
        ok=True,
        excluded=int((~ok_mask).sum()),
        remaining_rows=len(df),
    )
    ctx.df = df
    return ctx
