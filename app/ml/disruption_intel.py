from __future__ import annotations

import math
from typing import Any

# Lightweight geography / concentration heuristics for MVP demos.
_COUNTRY_RISK: dict[str, float] = {
    "US": 12,
    "CA": 14,
    "MX": 28,
    "CN": 35,
    "TW": 32,
    "VN": 30,
    "DE": 18,
    "PL": 22,
    "IN": 26,
    "GB": 16,
    "DEFAULT": 25,
}

_ALT_CATALOG: dict[str, list[str]] = {
    "electronics": ["Flex Ltd.", "Jabil Inc.", "Benchmark Electronics"],
    "apparel": ["Li & Fung (demo)", "Regional cut-and-sew co-op"],
    "food": ["Sysco alternate DC", "US Foods backup route"],
    "default": ["Secondary domestic vendor", "Near-shore backup supplier"],
}


class DisruptionIntelligence:
    def monitor_suppliers(self, suppliers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        scored = []
        for s in suppliers:
            country = str(s.get("country", "DEFAULT")).upper()[:2]
            base = _COUNTRY_RISK.get(country, _COUNTRY_RISK["DEFAULT"])
            fin = s.get("financial_health_score")
            fin_component = 40.0
            if fin is not None:
                fin_component = max(0.0, min(60.0, 100.0 - float(fin) * 0.6))
            otp = s.get("on_time_pct")
            otp_component = 25.0
            if otp is not None:
                otp_component = max(0.0, min(40.0, (100.0 - float(otp)) * 0.8))
            spend = float(s.get("spend_share", 0.2) or 0.0)
            concentration = min(55.0, spend * 120.0)
            score = min(100.0, base * 0.35 + fin_component + otp_component * 0.35 + concentration)
            tier = "low"
            if score >= 70:
                tier = "critical"
            elif score >= 45:
                tier = "elevated"
            scored.append(
                {
                    "supplier_id": s.get("id", "unknown"),
                    "name": s.get("name", "Supplier"),
                    "risk_score": round(score, 1),
                    "tier": tier,
                    "drivers": {
                        "region_baseline": round(base, 1),
                        "financial_stress": round(fin_component, 1),
                        "service_level": round(otp_component, 1),
                        "spend_concentration": round(concentration, 1),
                    },
                },
            )
        return scored

    def suggest_mitigations(self, suppliers: list[dict[str, Any]], scored: list[dict[str, Any]]) -> list[dict[str, Any]]:
        mitigations: list[dict[str, Any]] = []
        critical = [x for x in scored if x["tier"] == "critical"]
        if critical:
            mitigations.append(
                {
                    "type": "qualify_alternate",
                    "message": "Qualify at least one alternate for each critical supplier within 60 days.",
                    "suppliers": [c["supplier_id"] for c in critical],
                },
            )
        spend = [float(s.get("spend_share", 0) or 0) for s in suppliers]
        if spend and max(spend) > 0.45:
            mitigations.append(
                {
                    "type": "de_concentrate",
                    "message": "Largest supplier represents >45% spend — run an RFQ to split volume.",
                },
            )
        category = str(suppliers[0].get("category", "default")).lower() if suppliers else "default"
        alts = _ALT_CATALOG.get(category, _ALT_CATALOG["default"])
        mitigations.append(
            {
                "type": "alternate_suppliers",
                "message": "Seed list for sourcing outreach (demo data, not endorsements).",
                "ideas": alts,
            },
        )
        mitigations.append(
            {
                "type": "inventory_buffer",
                "message": "Increase safety stock by 10–15% on single-sourced SKUs until alternates are live.",
            },
        )
        mitigations.append(
            {
                "type": "logistics",
                "message": "Map secondary lanes / ports; run a tabletop exercise quarterly.",
            },
        )
        return mitigations

    def predict_disruptions(self, suppliers: list[dict[str, Any]]) -> dict[str, Any]:
        scored = self.monitor_suppliers(suppliers)
        overall = float(sum(s["risk_score"] for s in scored) / len(scored)) if scored else 0.0
        mitigations = self.suggest_mitigations(suppliers, scored)
        return {
            "success": True,
            "overall_risk": round(overall, 1),
            "suppliers": scored,
            "mitigations": mitigations,
        }


disruption_intel = DisruptionIntelligence()
