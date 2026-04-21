from __future__ import annotations

from typing import Any


class ReportingService:
    def build_executive_summary(
        self,
        forecast: dict[str, Any] | None = None,
        inventory: dict[str, Any] | None = None,
        disruption: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        summary: dict[str, Any] = {"generated": True, "blocks": []}
        if forecast and forecast.get("success"):
            summary["blocks"].append(
                {
                    "title": "Demand outlook",
                    "detail": f"Avg forecast {forecast['insights']['avg']:.1f} units/day; model fit score {forecast['accuracy_pct']:.1f}.",
                },
            )
        if inventory and inventory.get("success"):
            summary["blocks"].append(
                {
                    "title": "Inventory posture",
                    "detail": f"ROP {inventory['reorder_point']}, EOQ {inventory['order_quantity_eoq']}, health {inventory['inventory_health_score']}.",
                },
            )
        if disruption and disruption.get("success"):
            summary["blocks"].append(
                {
                    "title": "Supplier risk",
                    "detail": f"Portfolio risk index {disruption['overall_risk']} with {len(disruption['suppliers'])} suppliers scored.",
                },
            )
        return summary


reporting_service = ReportingService()
