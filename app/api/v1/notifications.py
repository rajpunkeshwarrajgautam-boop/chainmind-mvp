from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.auth_context import AuthContext
from app.api.deps_security import require_auth
from app.services.notification_service import notification_service

router = APIRouter()


@router.get("")
async def list_notifications(_ctx: Annotated[AuthContext, Depends(require_auth)]):
    return {"items": notification_service.list()}
