"""Registro de funciones ejecutables por `funcion_a_ejecutar` en BD."""

from __future__ import annotations

from app.services.validation_context import StepFn
from app.utils import creator_pipeline_steps as steps
from app.utils import email_hunter_steps as email_steps
from app.utils import pipeline_gate_steps as gate_steps
from app.utils import social_account_steps as social_steps

STEP_REGISTRY: dict[str, StepFn] = {
    "load_creator_columns": steps.load_creator_columns,
    "extract_best_name_source": steps.extract_best_name_source,
    "apply_name_parser": steps.apply_name_parser,
    "process_full_dataframe": steps.process_full_dataframe,
    "screen_email_patterns": email_steps.screen_email_patterns,
    "hunter_verify_emails": email_steps.hunter_verify_emails,
    "load_social_verification_columns": social_steps.load_social_verification_columns,
    "fetch_instagram_profiles": social_steps.fetch_instagram_profiles,
    "fetch_tiktok_profiles": social_steps.fetch_tiktok_profiles,
    "fetch_youtube_channels": social_steps.fetch_youtube_channels,
    "apply_main_platform_identity": social_steps.apply_main_platform_identity,
    "compute_creator_social_score": social_steps.compute_creator_social_score,
    "sync_identity_columns_from_creator_main_platform": (
        social_steps.sync_identity_columns_from_creator_main_platform
    ),
    "fetch_facebook_recent_reel_activity": social_steps.fetch_facebook_recent_reel_activity,
    "gate_social_followers_and_min_score": gate_steps.gate_social_followers_and_min_score,
    "gate_facebook_recent_reel_exclusions": gate_steps.gate_facebook_recent_reel_exclusions,
    "gate_email_hunter_failures": gate_steps.gate_email_hunter_failures,
}


def get_step_function(key: str) -> StepFn:
    k = key.strip()
    fn = STEP_REGISTRY.get(k)
    if fn is None:
        raise KeyError(
            f"Función de paso no registrada: {k!r}. "
            f"Regístrela en app.utils.step_registry.STEP_REGISTRY."
        )
    return fn
