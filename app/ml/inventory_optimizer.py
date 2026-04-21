from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


class InventoryOptimizer:
    """Classic inventory policies: safety stock, reorder point, EOQ, health score."""

    @staticmethod
    def _demand_stats_from_series(sales: pd.Series) -> tuple[float, float]:
        sales = pd.to_numeric(sales, errors="coerce").dropna()
        if sales.empty:
            return 0.0, 1.0
        mu = float(sales.mean())
        sigma = float(sales.std(ddof=1)) if len(sales) > 1 else max(abs(mu) * 0.15, 1.0)
        return mu, max(sigma, 1e-3)

    def calculate_optimal_stock_levels(self, product_data: dict[str, Any]) -> dict[str, Any]:
        """
        product_data keys:
          - sales_series or sales_data (list of dicts with sales)
          - daily_demand_mean, daily_demand_std (optional overrides)
          - current_on_hand, lead_time_days, ordering_cost, unit_cost
          - holding_cost_rate_annual (e.g. 0.2), service_level_z (default 1.65)
          - locations (optional): [{name, on_hand, sales_data|daily_mean}]
        """
        lead_time = int(product_data.get("lead_time_days", 7))
        lead_time = max(1, lead_time)
        review_period = int(product_data.get("review_period_days", 1))
        review_period = max(1, review_period)

        ordering_cost = float(product_data.get("ordering_cost", 50.0))
        unit_cost = float(product_data.get("unit_cost", 10.0))
        holding_rate = float(product_data.get("holding_cost_rate_annual", 0.2))
        z = float(product_data.get("service_level_z", 1.65))
        on_hand = float(product_data.get("current_on_hand", 0.0))

        mu = product_data.get("daily_demand_mean")
        sigma = product_data.get("daily_demand_std")

        if mu is None or sigma is None:
            sales = None
            if "sales_series" in product_data and product_data["sales_series"] is not None:
                sales = pd.Series(product_data["sales_series"])
            elif "sales_data" in product_data and product_data["sales_data"]:
                df = pd.DataFrame(product_data["sales_data"])
                cols = {str(c).lower(): c for c in df.columns}
                if "sales" in cols:
                    sales = pd.to_numeric(df[cols["sales"]], errors="coerce")
            if sales is None:
                raise ValueError("Provide daily_demand_mean/std or sales_data / sales_series.")
            mu, sigma = self._demand_stats_from_series(sales)

        mu = float(mu)
        sigma = float(sigma)

        protection_period = lead_time + review_period
        safety_stock = z * sigma * math.sqrt(protection_period)
        reorder_point = mu * protection_period + safety_stock

        annual_demand = max(mu * 365.0, 1.0)
        holding_cost_per_unit_year = max(unit_cost * holding_rate, 1e-6)
        eoq = math.sqrt((2.0 * annual_demand * ordering_cost) / holding_cost_per_unit_year)

        days_of_cover = on_hand / mu if mu > 1e-6 else float("inf")
        target_days = protection_period + (safety_stock / mu if mu > 1e-6 else 0.0)
        health = 100.0 - min(100.0, abs(days_of_cover - target_days) * 4.0)
        health = max(0.0, min(100.0, health))

        cross_location: list[dict[str, Any]] = []
        locs = product_data.get("locations") or []
        if isinstance(locs, list) and len(locs) >= 2:
            rows = []
            for loc in locs:
                name = loc.get("name", "location")
                stock = float(loc.get("on_hand", 0))
                if loc.get("sales_data"):
                    sdf = pd.DataFrame(loc["sales_data"])
                    sdf.columns = [str(c).strip().lower() for c in sdf.columns]
                    if "sales" not in sdf.columns:
                        m = mu
                    else:
                        m, _ = self._demand_stats_from_series(sdf["sales"])
                else:
                    m = float(loc.get("daily_mean", mu))
                doc = stock / m if m > 1e-6 else float("inf")
                rows.append({"name": name, "days_of_cover": doc, "on_hand": stock, "mu": m})
            avg_doc = float(np.mean([r["days_of_cover"] for r in rows if math.isfinite(r["days_of_cover"])]))
            for r in rows:
                if math.isfinite(r["days_of_cover"]) and r["days_of_cover"] > avg_doc * 1.35:
                    donors = [x for x in rows if math.isfinite(x["days_of_cover"]) and x["days_of_cover"] < avg_doc * 0.85]
                    for d in donors:
                        move = min(r["on_hand"], r["mu"] * 5) * 0.1
                        if move > 1:
                            cross_location.append(
                                {
                                    "from": r["name"],
                                    "to": d["name"],
                                    "suggested_units": round(move, 1),
                                    "rationale": "Rebalance days-of-cover across network",
                                },
                            )

        return {
            "success": True,
            "daily_demand_mean": mu,
            "daily_demand_std": sigma,
            "safety_stock": round(safety_stock, 2),
            "reorder_point": round(reorder_point, 2),
            "order_quantity_eoq": round(eoq, 2),
            "inventory_health_score": round(health, 1),
            "days_of_cover": round(days_of_cover, 2) if math.isfinite(days_of_cover) else None,
            "target_days_of_cover": round(target_days, 2),
            "cross_location_recommendations": cross_location[:5],
        }


inventory_optimizer = InventoryOptimizer()
