"""Cliente Hunter.io Email Verifier v2 (urllib, sin dependencias extra)."""

from __future__ import annotations

import json
import logging
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from app.core.config import settings

logger = logging.getLogger(__name__)

HUNTER_VERIFIER_URL = "https://api.hunter.io/v2/email-verifier"

_ALLOWED_STATUSES: frozenset[str] = frozenset({"valid", "accept_all"})


def normalize_hunter_status(status: str | None) -> str:
    if not status:
        return ""
    return str(status).strip().lower().replace(" ", "_").replace("-", "_")


def hunter_result_passes(result: dict[str, Any] | None) -> bool:
    if not result or result.get("_hunter_error"):
        return False
    score = result.get("hunter_score")
    try:
        score_int = int(score) if score is not None else 0
    except (TypeError, ValueError):
        score_int = 0
    st = normalize_hunter_status(result.get("hunter_status"))
    if score_int < settings.hunter_min_score:
        return False
    return st in _ALLOWED_STATUSES


def _empty_result(*, error: bool = False) -> dict[str, Any]:
    base = {
        "hunter_status": None,
        "hunter_score": None,
        "hunter_disposable": None,
        "hunter_webmail": None,
        "hunter_mx_records": None,
        "hunter_smtp_check": None,
        "hunter_accept_all": None,
    }
    if error:
        base["_hunter_error"] = True
    return base


def verify_email(
    api_key: str,
    email: str,
    cache: dict[str, Any],
    calls_counter: list[int],
    max_calls: int,
) -> dict[str, Any]:
    """
    Llama a Hunter (o devuelve caché). Siempre devuelve dict con claves hunter_*;
    _hunter_error indica fallo de red/API.
    """
    email_norm = (email or "").strip().lower()
    if not email_norm:
        return _empty_result(error=True)

    if email_norm in cache:
        return cache[email_norm]

    if calls_counter[0] >= max_calls:
        out = _empty_result(error=True)
        out["_hunter_skip"] = "max_calls"
        cache[email_norm] = out
        return out

    params = {"email": email_norm, "api_key": api_key}
    url = f"{HUNTER_VERIFIER_URL}?{urlencode(params)}"
    result: dict[str, Any]

    try:
        with urlopen(url, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        payload = json.loads(raw)
        data = payload.get("data") or {}
        result = {
            "hunter_status": data.get("status"),
            "hunter_score": data.get("score"),
            "hunter_disposable": data.get("disposable"),
            "hunter_webmail": data.get("webmail"),
            "hunter_mx_records": data.get("mx_records"),
            "hunter_smtp_check": data.get("smtp_check"),
            "hunter_accept_all": data.get("accept_all"),
        }
    except HTTPError as e:
        logger.warning("Hunter HTTPError %s: %s", email_norm, e)
        result = _empty_result(error=True)
    except URLError as e:
        logger.warning("Hunter URLError %s: %s", email_norm, e)
        result = _empty_result(error=True)
    except Exception as e:  # noqa: BLE001
        logger.warning("Hunter error %s: %s", email_norm, e)
        result = _empty_result(error=True)

    cache[email_norm] = result
    calls_counter[0] += 1
    time.sleep(settings.hunter_request_delay_seconds)
    return result
