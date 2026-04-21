from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict

from app.core.config import get_settings


class TokenPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sub: str
    tenant_id: int
    role: str = "viewer"


def create_access_token(*, user_id: int, tenant_id: int, role: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "tenant_id": tenant_id,
        "role": role,
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> TokenPayload:
    settings = get_settings()
    try:
        data = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return TokenPayload.model_validate(data)
    except JWTError as exc:  # pragma: no cover
        raise ValueError("invalid token") from exc
