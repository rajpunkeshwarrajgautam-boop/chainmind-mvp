# Stripe live cutover check (pilot)

Run this once before enabling live charges.

## Preconditions
- `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID_STARTER`, `STRIPE_WEBHOOK_SECRET` configured.
- Webhook endpoint reachable: `/api/v1/billing/webhook`.
- DPA signed (see `docs/legal/stripe-dpa-note.md`).

## Test-mode validation
1. Create or confirm one pilot product/price in Stripe.
2. Run checkout from app API (`POST /api/v1/billing/checkout-session`).
3. Complete payment using Stripe test card.
4. Confirm webhook events delivered successfully.
5. Confirm app DB subscription row reflects active state for tenant.

## Evidence to capture
- Stripe event IDs
- checkout session ID
- webhook delivery screenshot/log
- tenant subscription row snapshot (ID/status)

## Go / no-go
- **Go live** only if end-to-end test succeeds once with no manual DB edits.
- If failed, keep test mode, fix issue, and repeat full flow.
