# Pilot scope boundaries — MVP vs extended surface

**Owner:** engineering + GTM alignment before pilot sign-off.

## Definitions

| Tier | Meaning | Customer communication |
|------|---------|-------------------------|
| **MVP vertical slice** | Register → JWT → `POST /api/v1/forecast/sample` (or CSV upload path) → poll `GET /api/v1/forecast/jobs/{id}` until `completed`. Health/readiness and documented upload preview/forecast are included for demos. | Safe to demonstrate as **working pilot software**. |
| **Extended stub** | Routes exist for roadmap positioning but are **not** enterprise integrations or paid billing until configured. | Disclose as **template / not wired**; do not imply parity with a named ERP or live billing. |

## Route classes

### MVP vertical slice (pytest: `mvp_vertical_slice`)

- `/health`, `/ready`
- `/api/v1/auth/register`, login as used by tests
- `/api/v1/forecast/sample`, `/api/v1/forecast/jobs*`, `/api/v1/forecast` (JSON body)
- `/api/v1/uploads/preview`, `/api/v1/uploads/forecast` (per README)
- OpenAPI security scheme present (`BearerAuth`)

### Extended stub — billing (pytest: `extended_stub`)

- `/api/v1/billing/*` returns **501** until `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID_STARTER`, and related vars are set (see `app/api/v1/billing.py`).
- **Boundary test:** `tests/test_pilot_boundaries.py::test_billing_checkout_returns_501_without_stripe`

### Extended stub — integrations (pytest: `extended_stub`)

- `/api/v1/integrations/reconcile` persists an audit row but reconciliation payload stays **`template_only`** / `mvp_stub` until connector credentials and real CDC are implemented.
- **Boundary test:** `tests/test_pilot_boundaries.py::test_integrations_reconcile_is_template_only`

### Offline helpers (not HTTP contract)

- Pure ML/helper tests (`inventory_optimizer`, `disruption_intel`) are **not** pilot API promises; marker: `offline_helper`.

## How to run

```bash
# Default CI / PR gate — everything including governance and offline helpers
pytest tests/ -q

# Pilot contract subset: README slice + uploads + OpenAPI + stub honesty (no governance, no offline-only ML)
pytest tests/ -m "mvp_vertical_slice or extended_stub" -q
```

`tests/test_governance.py` is intentionally **unmarked**: it validates a live governance path but is not part of the minimal **curl** vertical slice; keep it in the full suite before release.

Extended-stub tests **must** stay green in CI without Stripe or ERP secrets so scope stays honest.
