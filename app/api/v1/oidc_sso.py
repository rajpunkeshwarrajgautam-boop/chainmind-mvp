from __future__ import annotations

import secrets
from typing import Annotated

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import User
from app.db.session import get_db
from app.security.jwt_tokens import create_access_token
from app.security.passwords import hash_password

router = APIRouter()

_oauth = OAuth()


def _ensure_oidc_client():
    settings = get_settings()
    if not settings.oidc_issuer or not settings.oidc_client_id:
        return None
    client = _oauth.create_client("oidc")
    if client is None:
        meta = settings.oidc_issuer.rstrip("/") + "/.well-known/openid-configuration"
        _oauth.register(
            name="oidc",
            server_metadata_url=meta,
            client_id=settings.oidc_client_id,
            client_secret=settings.oidc_client_secret or "",
            client_kwargs={"scope": settings.oidc_scope},
        )
    return _oauth.create_client("oidc")


@router.get("/oidc/login")
async def oidc_login(request: Request):
    settings = get_settings()
    client = _ensure_oidc_client()
    if not client or not settings.oidc_redirect_uri:
        raise HTTPException(status_code=501, detail="OIDC is not configured (OIDC_ISSUER, OIDC_CLIENT_ID, OIDC_REDIRECT_URI).")
    return await client.authorize_redirect(request, settings.oidc_redirect_uri)


@router.get("/oidc/callback")
async def oidc_callback(request: Request, db: Annotated[Session, Depends(get_db)]):
    settings = get_settings()
    client = _ensure_oidc_client()
    if not client:
        raise HTTPException(status_code=501, detail="OIDC is not configured.")
    token = await client.authorize_access_token(request)
    userinfo = token.get("userinfo") or {}
    email = (userinfo.get("email") or "").lower()
    subject = userinfo.get("sub")
    if not email or not subject:
        raise HTTPException(status_code=400, detail="OIDC token missing email or sub.")

    groups: list[str] = []
    claim = settings.oidc_role_claim
    raw_groups = userinfo.get(claim) or userinfo.get("groups") or []
    if isinstance(raw_groups, str):
        groups = [raw_groups]
    elif isinstance(raw_groups, list):
        groups = [str(g) for g in raw_groups]

    admin_groups = {g.strip() for g in settings.oidc_admin_groups.split(",") if g.strip()}
    role = "admin" if admin_groups.intersection(set(groups)) else "planner"

    user = db.execute(select(User).where(User.sso_subject == subject)).scalar_one_or_none()
    if not user and settings.oidc_jit_provision:
        from app.api.deps_security import get_or_create_default_tenant

        tenant = get_or_create_default_tenant(db)
        user = User(
            tenant_id=tenant.id,
            email=email,
            sso_subject=subject,
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not user:
        raise HTTPException(status_code=403, detail="User not provisioned; enable OIDC_JIT_PROVISION or create mapping.")

    access = create_access_token(user_id=user.id, tenant_id=user.tenant_id, role=user.role)
    return {"access_token": access, "token_type": "bearer", "email": user.email, "role": user.role}
