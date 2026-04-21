from __future__ import annotations

import math
from typing import Any


class RealTimeOptimizer:
    """What-if and stress helpers for planning sessions."""

    def scenario_planning(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Simple stock projection: linear burn using adjusted daily demand.
        """
        base_mu = float(payload.get("daily_demand_mean", 100.0))
        multiplier = float(payload.get("demand_multiplier", 1.0))
        mu = max(base_mu * multiplier, 1e-6)
        stock = float(payload.get("current_on_hand", 0.0))
        inbound = float(payload.get("inbound_units", 0.0))
        lead_time = int(payload.get("lead_time_days", 7))
        lead_time = max(0, lead_time)

        effective = stock + inbound
        days_until_stockout = math.floor(effective / mu) if mu > 0 else None
        stress_days = int(payload.get("horizon_days", 30))
        end_stock = effective - mu * stress_days

        return {
            "success": True,
            "adjusted_daily_demand": round(mu, 3),
            "projected_stock_after_horizon": round(end_stock, 2),
            "approx_days_of_cover": round(effective / mu, 2) if mu else None,
            "approx_stockout_day_index": days_until_stockout,
            "notes": "Linear demand assumption; use forecasts for seasonality-aware plans.",
        }


realtime_optimizer = RealTimeOptimizer()
