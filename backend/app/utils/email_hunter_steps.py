"""
Pasos del criterio: patrones en email (sin borrar filas) + Hunter.io Verifier.
Registrar en BD como criterio con orden mayor (último) y pasos en orden 1, 2.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.core.config import settings
from app.services.validation_context import ValidationContext
from app.utils.email_screening import add_email_pattern_columns
from app.utils.hunter_client import hunter_result_passes, verify_email


def _log(ctx: ValidationContext, step_key: str, message: str, **extra: Any) -> None:
    ctx.logs.append({"funcion": step_key, "message": message, **extra})


def screen_email_patterns(ctx: ValidationContext) -> ValidationContext:
    """Paso 1: marca emails con patrones de negocio/institución (no elimina filas)."""
    key = "screen_email_patterns"
    if "email" not in ctx.df.columns:
        _log(ctx, key, "Falta columna email.", ok=False)
        raise ValueError("El DataFrame debe incluir la columna email.")
    df, stats = add_email_pattern_columns(ctx.df)
    _log(
        ctx,
        key,
        "Patrones de email evaluados (email_pattern_flag / email_pattern_hits).",
        ok=True,
        **stats,
    )
    ctx.df = df
    return ctx


def hunter_verify_emails(ctx: ValidationContext) -> ValidationContext:
    """
    Paso 2: Hunter solo en filas sin email_pattern_flag.
    Pasa si hunter_score >= hunter_min_score y status ∈ {valid, accept_all}.
    """
    key = "hunter_verify_emails"
    df = ctx.df.copy()

    if "email_pattern_flag" not in df.columns:
        _log(
            ctx,
            key,
            "Falta email_pattern_flag; ejecute antes screen_email_patterns.",
            ok=False,
        )
        raise ValueError("Ejecute el paso screen_email_patterns antes de hunter_verify_emails.")

    cache: dict[str, Any] = ctx.pipeline_cache.setdefault("hunter_cache", {})
    calls_box: list[int] = ctx.pipeline_cache.setdefault("hunter_calls", [0])
    max_calls = settings.hunter_max_calls_per_run
    api_key = (settings.hunter_api_key or "").strip()

    statuses: list[Any] = []
    scores: list[Any] = []
    disposables: list[Any] = []
    webmails: list[Any] = []
    mx_list: list[Any] = []
    smtp_list: list[Any] = []
    accept_all_list: list[Any] = []
    passed: list[bool] = []
    skip_reasons: list[str] = []

    if not api_key:
        _log(ctx, key, "HUNTER_API_KEY no configurada; se omiten llamadas a Hunter.", skipped=True)

    for _, row in df.iterrows():
        flagged = bool(row.get("email_pattern_flag", False))
        email = row.get("email")

        if flagged:
            statuses.append(None)
            scores.append(None)
            disposables.append(None)
            webmails.append(None)
            mx_list.append(None)
            smtp_list.append(None)
            accept_all_list.append(None)
            passed.append(False)
            skip_reasons.append("pattern_flag")
            continue

        em = "" if email is None or (isinstance(email, float) and pd.isna(email)) else str(email).strip()
        if not em or "@" not in em:
            statuses.append(None)
            scores.append(None)
            disposables.append(None)
            webmails.append(None)
            mx_list.append(None)
            smtp_list.append(None)
            accept_all_list.append(None)
            passed.append(False)
            skip_reasons.append("invalid_email")
            continue

        if not api_key:
            statuses.append(None)
            scores.append(None)
            disposables.append(None)
            webmails.append(None)
            mx_list.append(None)
            smtp_list.append(None)
            accept_all_list.append(None)
            passed.append(False)
            skip_reasons.append("no_api_key")
            continue

        res = verify_email(api_key, em, cache, calls_box, max_calls)

        if res.get("_hunter_skip") == "max_calls":
            statuses.append(None)
            scores.append(None)
            disposables.append(None)
            webmails.append(None)
            mx_list.append(None)
            smtp_list.append(None)
            accept_all_list.append(None)
            passed.append(False)
            skip_reasons.append("max_calls")
            continue

        statuses.append(res.get("hunter_status"))
        scores.append(res.get("hunter_score"))
        disposables.append(res.get("hunter_disposable"))
        webmails.append(res.get("hunter_webmail"))
        mx_list.append(res.get("hunter_mx_records"))
        smtp_list.append(res.get("hunter_smtp_check"))
        accept_all_list.append(res.get("hunter_accept_all"))

        if res.get("_hunter_error"):
            passed.append(False)
            skip_reasons.append("api_error")
        elif hunter_result_passes(res):
            passed.append(True)
            skip_reasons.append("ok")
        else:
            passed.append(False)
            skip_reasons.append("hunter_rules_failed")

    df["hunter_status"] = statuses
    df["hunter_score"] = scores
    df["hunter_disposable"] = disposables
    df["hunter_webmail"] = webmails
    df["hunter_mx_records"] = mx_list
    df["hunter_smtp_check"] = smtp_list
    df["hunter_accept_all"] = accept_all_list
    df["email_hunter_passed"] = passed
    df["email_hunter_skip_reason"] = skip_reasons

    n_ok = sum(1 for r in skip_reasons if r == "ok")
    n_rules = sum(1 for r in skip_reasons if r == "hunter_rules_failed")
    _log(
        ctx,
        key,
        "Verificación Hunter completada.",
        ok=True,
        hunter_calls=calls_box[0],
        hunter_max_calls=max_calls,
        email_hunter_passed_count=n_ok,
        hunter_rules_failed_count=n_rules,
        min_score_required=settings.hunter_min_score,
        allowed_statuses=["valid", "accept_all"],
    )
    ctx.df = df
    return ctx
