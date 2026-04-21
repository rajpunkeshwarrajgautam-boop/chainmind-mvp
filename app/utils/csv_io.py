from __future__ import annotations

import io

import pandas as pd


def load_sales_frame(contents: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(contents))
    df.columns = [c.strip().lower() for c in df.columns]
    if "date" not in df.columns or "sales" not in df.columns:
        msg = 'CSV must include "date" and "sales" columns.'
        raise ValueError(msg)
    return df
