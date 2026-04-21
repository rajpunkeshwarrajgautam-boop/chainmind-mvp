from __future__ import annotations

from typing import Annotated, Any

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth_context import AuthContext
from app.api.deps_security import require_auth
from app.core.config import get_settings
from app.db.models import Subscription
from app.db.session import get_db

router = APIRouter()


class CheckoutRequest(BaseModel):
    success_url: str
    cancel_url: str
    quantity: int = 1


@router.post("/checkout-session")
async def create_checkout_session(
    ctx: Annotated[AuthContext, Depends(require_auth)],
    body: CheckoutRequest,
    db: Annotated[Session, Depends(get_db)],
):
    settings = get_settings()
    if not settings.stripe_secret_key or not settings.stripe_price_id_starter:
        raise HTTPException(status_code=501, detail="Stripe not configured (STRIPE_SECRET_KEY / STRIPE_PRICE_ID_STARTER).")
    stripe.api_key = settings.stripe_secret_key
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": settings.stripe_price_id_starter, "quantity": body.quantity}],
        success_url=body.success_url,
        cancel_url=body.cancel_url,
        customer_creation="always",
        subscription_data={
            "metadata": {"tenant_id": str(ctx.tenant_id)},
            "description": f"ChainMind tenant {ctx.tenant_id}",
        },
        metadata={"tenant_id": str(ctx.tenant_id)},
    )
    return {"checkout_url": session.url, "id": session.id}


@router.post("/portal-session")
async def customer_portal(
    ctx: Annotated[AuthContext, Depends(require_auth)],
    db: Annotated[Session, Depends(get_db)],
):
    settings = get_settings()
    if not settings.stripe_secret_key or not settings.stripe_customer_portal_return_url:
        raise HTTPException(status_code=501, detail="Configure STRIPE_SECRET_KEY and STRIPE_CUSTOMER_PORTAL_RETURN_URL.")
    stripe.api_key = settings.stripe_secret_key
    sub = db.execute(select(Subscription).where(Subscription.tenant_id == ctx.tenant_id)).scalar_one_or_none()
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer on file for tenant.")
    session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=settings.stripe_customer_portal_return_url,
    )
    return {"portal_url": session.url}


def _upsert_subscription(db: Session, tenant_id: int, **kwargs: Any) -> None:
    sub = db.execute(select(Subscription).where(Subscription.tenant_id == tenant_id)).scalar_one_or_none()
    if not sub:
        sub = Subscription(tenant_id=tenant_id)
        db.add(sub)
    for k, v in kwargs.items():
        setattr(sub, k, v)
    db.commit()


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    stripe_signature: Annotated[str | None, Header(alias="Stripe-Signature")] = None,
):
    settings = get_settings()
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=501, detail="Stripe webhook secret not configured.")
    stripe.api_key = settings.stripe_secret_key or ""
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature or "",
            secret=settings.stripe_webhook_secret,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid webhook: {exc}") from exc

    etype = event["type"]
    data_object = event["data"]["object"]

    if etype == "checkout.session.completed":
        tenant_id = int(data_object.get("metadata", {}).get("tenant_id", "0") or 0)
        customer = data_object.get("customer")
        if tenant_id and customer:
            _upsert_subscription(
                db,
                tenant_id,
                stripe_customer_id=customer,
                stripe_subscription_id=data_object.get("subscription"),
                plan="starter",
                status="active",
            )

    if etype in {"customer.subscription.updated", "customer.subscription.deleted"}:
        tenant_id = int(data_object.get("metadata", {}).get("tenant_id", "0") or 0)
        if tenant_id:
            _upsert_subscription(
                db,
                tenant_id,
                stripe_subscription_id=data_object.get("id"),
                status=data_object.get("status", "unknown"),
            )

    return {"received": True, "type": etype}
