from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_explainability_requires_auth(client: TestClient, auth_headers: dict[str, str]):
    payload = {"sales_data": [{"date": f"2024-01-{i+1:02d}", "sales": 100 + i} for i in range(25)]}
    fc = client.post("/api/v1/forecast", json={**payload, "days_ahead": 5}, headers=auth_headers)
    assert fc.status_code == 200, fc.text
    job_id = fc.json()["job_id"]
    ex = client.post(f"/api/v1/governance/forecasts/{job_id}/explain", headers=auth_headers)
    assert ex.status_code == 200, ex.text
    body = ex.json()
    assert body["success"] is True
    assert "feature_importance" in body
