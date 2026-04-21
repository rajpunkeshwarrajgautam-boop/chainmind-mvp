from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.ml.forecaster import ChainMindForecaster


def run_backtest(sales_data: list[dict[str, Any]], holdout_days: int = 7) -> dict[str, Any]:
    """Simple holdout: train on prefix, compare last `holdout_days` to model predictions."""
    df = pd.DataFrame(sales_data)
    df.columns = [str(c).strip().lower() for c in df.columns]
    if len(df) < holdout_days + 20:
        return {"success": False, "message": "Need more history for holdout evaluation."}
    train = df.iloc[: -holdout_days].copy()
    actual = df.iloc[-holdout_days:]["sales"].astype(float).values
    model = ChainMindForecaster()
    fc = model.train_and_predict(train, days_ahead=holdout_days)
    if not fc.get("success"):
        return fc
    pred = np.array(fc["predictions"][:holdout_days])
    mape = float(np.mean(np.abs(actual - pred) / np.maximum(np.abs(actual), 1e-6)))
    return {
        "success": True,
        "holdout_days": holdout_days,
        "mape": mape,
        "segments": {"global": {"mape": mape}},
        "champion_tag": "v1.0.0",
    }
