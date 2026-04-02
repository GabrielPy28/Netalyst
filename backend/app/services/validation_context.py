from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    import pandas as pd


@dataclass
class ValidationContext:
    """Estado compartido al ejecutar pasos de un programa"""

    df: Any  # pd.DataFrame (evita import pesado en type-check only)
    program_id: str
    criterion_id: str | None = None
    criterion_nombre: str | None = None
    logs: list[dict[str, Any]] = field(default_factory=list)
    # Caché por criterio (p. ej. Hunter por email); se reinicia al cambiar de criterio.
    pipeline_cache: dict[str, Any] = field(default_factory=dict)
    # Acumulado de filas excluidas (exclusion_stage / exclusion_reason); persiste entre criterios.
    df_excluded: Any | None = None


StepFn = Callable[[ValidationContext], ValidationContext]
