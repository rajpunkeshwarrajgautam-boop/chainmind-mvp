"""Synthetic daily sales series for demos and smoke tests."""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_sample_sales_rows(*, history_days: int = 365, seed: int = 42) -> list[dict[str, int | str]]:
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start="2023-01-01", periods=history_days, freq="D")
    base_sales = 100.0
    trend = np.linspace(0, 50, len(dates))
    seasonality = 20 * np.sin(2 * np.pi * dates.dayofyear / 365.0)
    noise = rng.normal(0, 10, len(dates))
    sales = np.maximum(base_sales + trend + seasonality + noise, 0).astype(int)
    df = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "sales": sales})
    return df.to_dict(orient="records")
