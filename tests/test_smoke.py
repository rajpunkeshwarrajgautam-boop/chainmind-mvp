from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.ml.disruption_intel import disruption_intel
from app.ml.inventory_optimizer import inventory_optimizer


def test_health(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_ready(client: TestClient):
    res = client.get("/ready")
    # Redis may be unavailable in bare CI — database must be ok
    assert res.status_code in (200, 503)
    body = res.json()
    assert "database" in body


def test_dashboard_root(client: TestClient):
    res = client.get("/")
    assert res.status_code == 200
    assert "ChainMind" in res.text


def test_forecast_sample(client: TestClient, auth_headers: dict[str, str]):
    res = client.post(
        "/api/v1/forecast/sample",
        json={"days_ahead": 7, "history_days": 60},
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["success"] is True
    assert body["job_id"]


def test_forecast_jobs_list(client: TestClient, auth_headers: dict[str, str]):
    client.post("/api/v1/forecast/sample", json={"days_ahead": 5, "history_days": 40}, headers=auth_headers)
    res = client.get("/api/v1/forecast/jobs", headers=auth_headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 1


def test_upload_preview(client: TestClient, auth_headers: dict[str, str]):
    csv = "date,sales\n2024-01-01,10\n2024-01-02,12\n"
    res = client.post("/api/v1/uploads/preview", files={"file": ("t.csv", csv, "text/csv")}, headers=auth_headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["row_count"] == 2
    assert "date" in body["columns"]


def test_upload_forecast_multipart(client: TestClient, auth_headers: dict[str, str]):
    lines = ["date,sales"] + [f"2024-01-{i+1:02d},{100 + i}" for i in range(20)]
    csv = "\n".join(lines) + "\n"
    res = client.post(
        "/api/v1/uploads/forecast",
        files={"file": ("sales.csv", csv, "text/csv")},
        data={"days_ahead": 5},
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["success"] is True
    assert body["job_id"]
    assert "upload_id" in body
    assert len(body.get("predictions", [])) == 5


def test_openapi_includes_bearer_scheme(client: TestClient):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    schemes = spec.get("components", {}).get("securitySchemes", {})
    assert "BearerAuth" in schemes
    assert schemes["BearerAuth"]["type"] == "http"


def test_forecast_v1(client: TestClient, auth_headers: dict[str, str]):
    payload = {
        "sales_data": [{"date": f"2024-01-{i+1:02d}", "sales": 100 + i} for i in range(20)],
        "days_ahead": 10,
    }
    res = client.post("/api/v1/forecast", json=payload, headers=auth_headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["success"] is True
    assert len(body["predictions"]) == 10
    assert "job_id" in body


def test_inventory_optimizer_math():
    out = inventory_optimizer.calculate_optimal_stock_levels(
        {
            "daily_demand_mean": 10.0,
            "daily_demand_std": 2.0,
            "current_on_hand": 200.0,
            "lead_time_days": 7,
            "ordering_cost": 75.0,
            "unit_cost": 12.0,
            "holding_cost_rate_annual": 0.25,
            "service_level_z": 1.65,
        },
    )
    assert out["success"] is True
    assert out["reorder_point"] > 0
    assert out["order_quantity_eoq"] > 0


def test_disruption_scores():
    res = disruption_intel.predict_disruptions(
        [
            {
                "id": "s1",
                "name": "Acme",
                "country": "CN",
                "spend_share": 0.6,
                "on_time_pct": 70,
                "financial_health_score": 40,
                "category": "electronics",
            },
        ],
    )
    assert res["success"] is True
    assert res["overall_risk"] > 0
    assert res["mitigations"]
