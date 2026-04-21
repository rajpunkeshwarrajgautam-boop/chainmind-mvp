from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor


class ChainMindForecaster:
    """Reference behavior matches the original ChainMind MVP snippet (RF + calendar/lags + concat tail)."""

    def __init__(self) -> None:
        # Original spec: RandomForestRegressor(n_estimators=50, random_state=42)
        self.model = RandomForestRegressor(n_estimators=50, random_state=42)

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        df["sales"] = pd.to_numeric(df["sales"], errors="coerce")
        df = df.dropna(subset=["sales"])
        df = df.sort_values("date").reset_index(drop=True)

        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        df["day"] = df["date"].dt.day
        df["dayofweek"] = df["date"].dt.dayofweek
        df["dayofyear"] = df["date"].dt.dayofyear
        df["quarter"] = df["date"].dt.quarter

        df["sales_ma_7"] = df["sales"].rolling(window=7, min_periods=1).mean()
        df["sales_ma_30"] = df["sales"].rolling(window=30, min_periods=1).mean()
        df["sales_lag_1"] = df["sales"].shift(1)
        df["sales_lag_7"] = df["sales"].shift(7)
        df["sales_lag_30"] = df["sales"].shift(30)

        return df.bfill().ffill()

    def train_and_predict(self, df: pd.DataFrame, days_ahead: int = 30) -> dict:
        if df.empty or len(df) < 14:
            return {
                "success": False,
                "error": "insufficient_rows",
                "message": "Need at least 14 rows with valid date and sales after cleaning.",
            }

        try:
            df_processed = self.prepare_features(df)
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

            X = df_processed[feature_columns]
            y = df_processed["sales"]
            self.model.fit(X, y)

            last_date = df_processed["date"].max()
            future_dates = [last_date + timedelta(days=i) for i in range(1, days_ahead + 1)]

            future_df = pd.DataFrame(
                {
                    "date": future_dates,
                    "sales": [float(y.iloc[-1])] * days_ahead,
                }
            )

            # Original spec: pd.concat([df_processed.tail(60), future_df])
            combined = pd.concat([df_processed.tail(60), future_df], ignore_index=True)
            future_processed = self.prepare_features(combined).tail(days_ahead)
            X_future = future_processed[feature_columns]
            predictions = self.model.predict(X_future)

            in_sample = self.model.predict(X)
            residuals = y.values - in_sample
            std_dev = float(np.std(residuals)) if len(residuals) else 0.0
            lower_bound = predictions - (1.96 * std_dev)
            upper_bound = predictions + (1.96 * std_dev)

            window = min(30, len(y))
            tail_pred = self.model.predict(X.tail(window))
            tail_y = y.tail(window).values
            denom = np.maximum(np.abs(tail_y), 1e-6)
            mape = float(np.mean(np.abs(tail_y - tail_pred) / denom))
            accuracy_pct = max(0.0, min(99.9, (1.0 - mape) * 100.0))
            # Snippet templates used `Accuracy: {{ (1-result.accuracy_score)*100 }}%` with a flawed
            # in-sample definition; we expose `accuracy_score` so that formula matches `accuracy_pct`.
            accuracy_score = max(0.0, min(1.0, 1.0 - accuracy_pct / 100.0))

            preds_list = predictions.tolist()
            peak = float(np.max(predictions))
            low = float(np.min(predictions))
            avg = float(np.mean(predictions))

            return {
                "success": True,
                "dates": [d.strftime("%Y-%m-%d") for d in future_dates],
                "predictions": preds_list,
                "lower_bound": lower_bound.tolist(),
                "upper_bound": upper_bound.tolist(),
                "accuracy_pct": accuracy_pct,
                "accuracy_score": accuracy_score,
                "insights": {
                    "peak": peak,
                    "low": low,
                    "avg": avg,
                },
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "success": False,
                "error": str(exc),
                "message": "Failed to generate forecast. Please check your data format.",
            }


forecaster = ChainMindForecaster()
