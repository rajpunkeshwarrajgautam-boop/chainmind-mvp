from __future__ import annotations

import hashlib
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth_context import AuthContext
from app.core.config import get_settings
from app.db.models import ApiKey, Tenant, User
from app.db.session import get_db
from app.security.jwt_tokens import decode_token


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_or_create_default_tenant(db: Session) -> Tenant:
    settings = get_settings()
    t = db.execute(select(Tenant).where(Tenant.slug == settings.default_tenant_slug)).scalar_one_or_none()
    if t:
        return t
    t = Tenant(slug=settings.default_tenant_slug, name="Default tenant")
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


async def require_auth(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> AuthContext:
    settings = get_settings()

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token)
            user = db.get(User, int(payload.sub))
            if not user or not user.is_active:
                raise HTTPException(status_code=401, detail="Invalid user")
            if user.tenant_id != payload.tenant_id:
                raise HTTPException(status_code=401, detail="Tenant mismatch")
            return AuthContext(tenant_id=user.tenant_id, user=user, auth_method="jwt")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid bearer token") from None

    if x_api_key:
        digest = _hash_key(x_api_key)
        key = db.execute(
            select(ApiKey).where(ApiKey.key_hash == digest, ApiKey.revoked_at.is_(None)),
        ).scalar_one_or_none()
        if key:
            user = db.get(User, key.user_id) if key.user_id else None
            return AuthContext(tenant_id=key.tenant_id, user=user, auth_method="api_key")

        if settings.chainmind_api_key and x_api_key == settings.chainmind_api_key:
            tenant = get_or_create_default_tenant(db)
            return AuthContext(tenant_id=tenant.id, user=None, auth_method="legacy_key")

        raise HTTPException(status_code=401, detail="Invalid API key")

    if settings.chainmind_api_key:
        raise HTTPException(status_code=401, detail="Authentication required")

    if settings.environment == "production":
        raise HTTPException(status_code=401, detail="Authentication required in production")

    tenant = get_or_create_default_tenant(db)
    return AuthContext(tenant_id=tenant.id, user=None, auth_method="legacy_key")


async def require_planner(
    ctx: Annotated[AuthContext, Depends(require_auth)],
) -> AuthContext:
    ctx.require_roles("planner", "admin")
    return ctx
