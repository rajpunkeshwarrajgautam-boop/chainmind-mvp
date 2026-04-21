from __future__ import annotations

from typing import Any


class SupplyChainConnector:
    """Integration façade — wire credentials in production; returns capability matrix for MVP."""

    def connect_erp(self, erp_type: str) -> dict[str, Any]:
        supported = {"SAP": "planned", "Oracle": "planned", "NetSuite": "planned", "Dynamics": "planned"}
        key = (erp_type or "").strip().upper() or "UNKNOWN"
        return {
            "erp_type": key,
            "status": "stub",
            "ready": key in supported,
            "message": "Connector stubs ship with MVP; enable with partner credentials.",
        }

    def connect_warehouse_systems(self) -> dict[str, Any]:
        return {
            "wms": ["Manhattan", "BlueYonder", "HighJump"],
            "status": "stub",
            "message": "WMS webhooks + ASN ingestion not configured.",
        }

    def connect_transportation_systems(self) -> dict[str, Any]:
        return {
            "tms": ["project44", "FourKites", "Descartes"],
            "status": "stub",
            "message": "Carrier EDI / TMS events map to disruption engine in Phase 2.",
        }

    def external_data_feeds(self) -> dict[str, Any]:
        return {
            "weather": {"provider": "Open-Meteo (demo)", "status": "stub"},
            "macro": {"provider": "FRED (demo)", "status": "stub"},
            "news_sentiment": {"provider": "GDELT-lite (demo)", "status": "stub"},
        }

    def status(self) -> dict[str, Any]:
        return {
            "connectors": {
                "erp": self.connect_erp("SAP"),
                "warehouse": self.connect_warehouse_systems(),
                "transportation": self.connect_transportation_systems(),
                "external": self.external_data_feeds(),
            }
        }


connector = SupplyChainConnector()
