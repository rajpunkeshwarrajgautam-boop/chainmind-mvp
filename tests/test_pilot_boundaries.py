"""Lock honest pilot scope: billing and integrations stay stubbed without secrets."""

from __future__ import annotations

import pytest


@pytest.mark.extended_stub
def test_billing_checkout_returns_501_without_stripe(client, auth_headers):
    res = client.post(
        "/api/v1/billing/checkout-session",
        json={
            "success_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel",
            "quantity": 1,
        },
        headers=auth_headers,
    )
    assert res.status_code == 501, res.text
    assert "Stripe" in res.json().get("detail", "")


@pytest.mark.extended_stub
def test_integrations_reconcile_is_template_only(client, auth_headers):
    res = client.post(
        "/api/v1/integrations/reconcile",
        json={"connector_id": "sap_s4_otc", "payload": {"note": "pilot boundary test"}},
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body.get("success") is True
    recon = body.get("reconciliation") or {}
    assert recon.get("status") == "template_only"
    assert recon.get("implementation") == "mvp_stub"
