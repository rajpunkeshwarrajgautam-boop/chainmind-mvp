from __future__ import annotations

import hashlib
import secrets
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ApiKey, ModelVersion, Tenant, User


def _hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ensure_default_model_version(db: Session) -> ModelVersion | None:
    existing = db.execute(select(ModelVersion).where(ModelVersion.is_champion.is_(True))).scalar_one_or_none()
    if existing:
        return existing
    mv = ModelVersion(
        name="chainmind_rf",
        version_tag="v1.0.0",
        artifact_uri="inline:sklearn.RandomForestRegressor",
        metrics={"description": "Default champion for MVP serving path"},
        is_champion=True,
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)
    return mv


def ensure_bootstrap_admin(db: Session) -> dict[str, Any] | None:
    settings = get_settings()
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        return None
    if db.execute(select(User).limit(1)).scalar_one_or_none():
        return None

    tenant = Tenant(slug=settings.default_tenant_slug, name="Default organization")
    db.add(tenant)
    db.flush()

    from app.security.passwords import hash_password

    user = User(
        tenant_id=tenant.id,
        email=settings.bootstrap_admin_email.lower(),
        hashed_password=hash_password(settings.bootstrap_admin_password),
        role="admin",
    )
    db.add(user)
    db.commit()

    raw_key = f"cm_{secrets.token_urlsafe(32)}"
    prefix = raw_key[:12]
    api = ApiKey(
        tenant_id=tenant.id,
        user_id=user.id,
        name="bootstrap-admin",
        key_hash=_hash_api_key(raw_key),
        prefix=prefix,
        scopes=["*"],
    )
    db.add(api)
    db.commit()

    return {
        "tenant_slug": tenant.slug,
        "admin_email": user.email,
        "api_key_once": raw_key,
        "message": "Store the API key securely; it cannot be retrieved again.",
    }
