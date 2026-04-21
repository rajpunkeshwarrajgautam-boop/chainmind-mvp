from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.auth_context import AuthContext
from app.api.deps_security import require_auth
from app.services.reporting_service import reporting_service

router = APIRouter()


class ExecutiveSummaryRequest(BaseModel):
    forecast: dict[str, Any] | None = None
    inventory: dict[str, Any] | None = None
    disruption: dict[str, Any] | None = None


@router.post("/executive-summary")
async def executive_summary(
    _ctx: Annotated[AuthContext, Depends(require_auth)],
    body: ExecutiveSummaryRequest,
):
    return reporting_service.build_executive_summary(
        forecast=body.forecast,
        inventory=body.inventory,
        disruption=body.disruption,
    )
