"""Acumular filas excluidas con etapa y motivo (pipeline La Neta)."""

from __future__ import annotations

import pandas as pd

from app.services.validation_context import ValidationContext

COL_STAGE = "exclusion_stage"
COL_REASON = "exclusion_reason"

STAGE_SOCIAL = "1_redes_y_puntaje_aprobacion"
STAGE_FACEBOOK = "2_facebook_actividad_reciente"
STAGE_EMAIL = "4_email_hunter"


def append_excluded(
    ctx: ValidationContext,
    subset: pd.DataFrame,
    stage: str,
    reason: str | pd.Series,
) -> None:
    """Concatena filas excluidas; reason puede ser una Serie alineada al subset."""
    if subset.empty:
        return
    part = subset.copy()
    part[COL_STAGE] = stage
    if isinstance(reason, str):
        part[COL_REASON] = reason
    else:
        part[COL_REASON] = reason.values
    if ctx.df_excluded is None or len(ctx.df_excluded) == 0:
        ctx.df_excluded = part
    else:
        ctx.df_excluded = pd.concat([ctx.df_excluded, part], ignore_index=True)

