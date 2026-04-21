"""Certified mapping *templates* — partner engineering fills per customer ERP tenant."""

from __future__ import annotations

from typing import Any

CATALOG: dict[str, dict[str, Any]] = {
    "sap_s4_otc": {
        "version": "0.1.0",
        "description": "Order-to-cash extracts (VBAP/VBAK) → ChainMind sales grain",
        "grain": "daily_sku_location",
        "source_objects": ["VBAK", "VBAP", "LIPS", "MARD"],
        "field_map": {
            "order_date": "VBAK.ERDAT",
            "material": "VBAP.MATNR",
            "qty": "VBAP.KWMENG",
            "plant": "VBAP.WERKS",
        },
        "reconciliation_checks": [
            {"name": "sum_qty_vs_billing", "sql_hint": "Compare VBAP sum vs billing doc VF"},
        ],
    },
    "oracle_fusion_inventory": {
        "version": "0.1.0",
        "description": "Inventory transactions → on-hand snapshots",
        "grain": "daily_location",
        "rest_resources": ["/fscmRestApi/resources/latest/inventoryBalances"],
    },
    "manhattan_wms": {
        "version": "0.1.0",
        "description": "ASN / shipment confirmations",
        "webhook_events": ["SHIP_CONFIRM", "ADJUSTMENT"],
    },
}


def list_catalog() -> dict[str, Any]:
    return {"items": [{"id": k, **{kk: vv for kk, vv in v.items() if kk != "field_map"}} for k, v in CATALOG.items()]}
