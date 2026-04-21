from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Tenant, User
from app.db.session import get_db
from app.security.jwt_tokens import create_access_token
from app.security.passwords import hash_password, verify_password

router = APIRouter()


class LoginRequest(BaseModel):
    tenant_slug: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8)


class RegisterRequest(BaseModel):
    tenant_slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$")
    tenant_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=10)


@router.post("/register")
async def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.execute(select(Tenant).where(Tenant.slug == body.tenant_slug)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Tenant slug already taken")
    tenant = Tenant(slug=body.tenant_slug, name=body.tenant_name)
    db.add(tenant)
    db.flush()
    user = User(
        tenant_id=tenant.id,
        email=str(body.email).lower(),
        hashed_password=hash_password(body.password),
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user_id=user.id, tenant_id=user.tenant_id, role=user.role)
    return {"access_token": token, "token_type": "bearer", "tenant_slug": tenant.slug}


@router.post("/login")
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    tenant = db.execute(select(Tenant).where(Tenant.slug == body.tenant_slug)).scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=401, detail="Unknown tenant")
    user = db.execute(
        select(User).where(User.tenant_id == tenant.id, User.email == str(body.email).lower()),
    ).scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User disabled")
    token = create_access_token(user_id=user.id, tenant_id=user.tenant_id, role=user.role)
    return {"access_token": token, "token_type": "bearer"}
