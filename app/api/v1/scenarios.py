from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.auth_context import AuthContext
from app.api.deps_security import require_auth
from app.ml.scenarios import realtime_optimizer

router = APIRouter()


class WhatIfRequest(BaseModel):
    daily_demand_mean: float = Field(100, gt=0)
    demand_multiplier: float = Field(1.0, gt=0)
    current_on_hand: float = Field(0, ge=0)
    inbound_units: float = Field(0, ge=0)
    lead_time_days: int = Field(7, ge=0, le=120)
    horizon_days: int = Field(30, ge=1, le=365)


@router.post("/what-if")
async def what_if(_ctx: Annotated[AuthContext, Depends(require_auth)], body: WhatIfRequest):
    payload = body.model_dump()
    return realtime_optimizer.scenario_planning(payload)
