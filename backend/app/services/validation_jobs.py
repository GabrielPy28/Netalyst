"""
Validación en segundo plano para corridas muy largas (horas).

Una petición HTTP abierta (SSE) suele cortarse por proxies (~1 h) o límites del proveedor.
Aquí el cliente recibe un job_id al instante y hace polling corto hasta complete/error.
"""

from __future__ import annotations

import os
import tempfile
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Literal

import pandas as pd

from app.core.config import settings
from app.core.db import get_session_factory
from app.services.validation_runner import (
    build_creadores_output_zip_bytes,
    iter_validation_sse_events,
    run_validation,
)


@dataclass
class ValidationJobState:
    job_id: uuid.UUID
    program_id: uuid.UUID
    response_mode: Literal["json", "zip"]
    status: Literal["running", "complete", "error"] = "running"
    events_tail: deque[dict[str, Any]] = field(default_factory=deque)
    result: dict[str, Any] | None = None
    error_message: str | None = None
    zip_path: str | None = None
    summary: dict[str, Any] | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def touch(self) -> None:
        self.updated_at = time.time()

    def append_event(self, ev: dict[str, Any]) -> None:
        max_n = max(10, int(settings.validation_job_events_tail_max))
        with self._lock:
            self.events_tail.append(ev)
            while len(self.events_tail) > max_n:
                self.events_tail.popleft()
            self.touch()

    def snapshot_tail(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self.events_tail)

    def remove_zip(self) -> None:
        p = self.zip_path
        self.zip_path = None
        if p and os.path.isfile(p):
            try:
                os.unlink(p)
            except OSError:
                pass


_jobs: dict[uuid.UUID, ValidationJobState] = {}
_registry_lock = threading.Lock()


def _count_running() -> int:
    return sum(1 for j in _jobs.values() if j.status == "running")


def purge_stale_validation_jobs() -> None:
    """Elimina trabajos antiguos y archivos ZIP temporales."""
    max_age = max(3600.0, float(settings.validation_job_max_age_hours) * 3600.0)
    now = time.time()
    with _registry_lock:
        to_del: list[uuid.UUID] = []
        for jid, job in _jobs.items():
            if job.status == "running":
                continue
            if now - job.created_at > max_age:
                to_del.append(jid)
        for jid in to_del:
            job = _jobs.pop(jid, None)
            if job:
                job.remove_zip()


def try_register_job(
    program_id: uuid.UUID,
    response_mode: Literal["json", "zip"],
) -> ValidationJobState | None:
    """
    Crea el registro del job si hay cupo. Devuelve None si hay demasiados en ejecución.
    """
    purge_stale_validation_jobs()
    max_c = max(1, int(settings.validation_async_max_concurrent))
    with _registry_lock:
        if _count_running() >= max_c:
            return None
        jid = uuid.uuid4()
        job = ValidationJobState(job_id=jid, program_id=program_id, response_mode=response_mode)
        _jobs[jid] = job
        return job


def get_job(job_id: uuid.UUID) -> ValidationJobState | None:
    purge_stale_validation_jobs()
    return _jobs.get(job_id)


def _run_json_job(job: ValidationJobState, df: pd.DataFrame) -> None:
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        for ev in iter_validation_sse_events(db, job.program_id, df):
            job.append_event(ev)
            t = ev.get("type")
            if t == "error":
                job.status = "error"
                job.error_message = str(ev.get("message") or "Error en validación")
                return
            if t == "complete":
                job.result = dict(ev)
                job.result.pop("type", None)
                job.status = "complete"
                return
        job.status = "error"
        job.error_message = "La validación terminó sin evento complete."
    except Exception as e:  # noqa: BLE001
        job.status = "error"
        job.error_message = str(e)
    finally:
        db.close()
        job.touch()


def _run_zip_job(job: ValidationJobState, df: pd.DataFrame) -> None:
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        job.append_event(
            {
                "type": "step_start",
                "criterion_nombre": "Exportación ZIP",
                "criterion_orden": 0,
                "paso_num": 1,
                "step_nombre": "Ejecutando validación completa (puede tardar varias horas)",
                "funcion_a_ejecutar": "run_validation_zip_bundle",
            }
        )
        out_df, ex_df, blocks, program_nombre = run_validation(db, job.program_id, df)
        job.append_event(
            {
                "type": "step_done",
                "criterion_nombre": "Validación",
                "criterion_orden": 0,
                "paso_num": 1,
                "step_nombre": "Pipeline completo",
                "funcion_a_ejecutar": "run_validation",
                "ok": True,
                "logs_tail": [],
            }
        )
        payload = build_creadores_output_zip_bytes(out_df, ex_df)
        fd, path = tempfile.mkstemp(prefix="valjob-", suffix=".zip")
        try:
            os.write(fd, payload)
        finally:
            os.close(fd)
        job.zip_path = path
        n_ex = len(ex_df) if ex_df is not None else 0
        job.summary = {
            "program_nombre": program_nombre,
            "rows": len(out_df),
            "excluded_rows": n_ex,
        }
        job.status = "complete"
    except LookupError as e:
        job.status = "error"
        job.error_message = str(e)
    except ValueError as e:
        job.status = "error"
        job.error_message = str(e)
    except KeyError as e:
        job.status = "error"
        job.error_message = str(e)
    except Exception as e:  # noqa: BLE001
        job.status = "error"
        job.error_message = str(e)
    finally:
        db.close()
        job.touch()


def spawn_validation_job(
    job: ValidationJobState,
    df: pd.DataFrame,
) -> None:
    """Arranca el worker en un hilo daemon (misma estrategia que upload-stream)."""

    def target() -> None:
        if job.response_mode == "zip":
            _run_zip_job(job, df)
        else:
            _run_json_job(job, df)

    threading.Thread(target=target, name=f"validation-job-{job.job_id}", daemon=True).start()
