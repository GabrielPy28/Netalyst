"""Lectura de CSV / Excel subidos."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

import pandas as pd
from fastapi import UploadFile

if TYPE_CHECKING:
    pass


def read_uploaded_table(file: UploadFile) -> pd.DataFrame:
    name = (file.filename or "").lower()
    raw = file.file.read()
    if not raw:
        raise ValueError("El archivo está vacío.")

    if name.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(raw))
    elif name.endswith(".xlsx") or name.endswith(".xls"):
        df = pd.read_excel(io.BytesIO(raw))
    else:
        raise ValueError("Formato no soportado. Use .csv, .xlsx o .xls.")

    df.columns = [str(c).strip() for c in df.columns]
    return df
