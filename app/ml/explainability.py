from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance

from app.ml.forecaster import ChainMindForecaster


def explain_forecast_from_history(sales_data: list[dict[str, Any]], *, random_state: int = 42) -> dict[str, Any]:
    """Permutation importance on the same feature matrix as production forecaster."""
    df = pd.DataFrame(sales_data)
    df.columns = [str(c).strip().lower() for c in df.columns]
    if len(df) < 20:
        return {"success": False, "message": "Need at least 20 rows for explainability."}
    model = ChainMindForecaster()
    df_p = model.prepare_features(df)
    feature_columns = [
        "year",
        "month",
        "day",
        "dayofweek",
        "dayofyear",
        "quarter",
        "sales_ma_7",
        "sales_ma_30",
        "sales_lag_1",
        "sales_lag_7",
        "sales_lag_30",
    ]
    X_df = df_p[feature_columns]
    y = df_p["sales"]
    model.model.fit(X_df, y)
    result = permutation_importance(
        model.model,
        X_df,
        y,
        n_repeats=8,
        random_state=random_state,
        n_jobs=1,
    )
    names = feature_columns
    order = np.argsort(result.importances_mean)[::-1]
    ranked = {names[i]: float(result.importances_mean[i]) for i in order}
    out: dict[str, Any] = {
        "success": True,
        "method": "permutation_importance",
        "feature_importance": ranked,
    }
    if hasattr(result, "baseline_score"):
        out["baseline_score"] = float(result.baseline_score)
    return out
