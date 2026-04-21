from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.auth_context import AuthContext
from app.api.deps_security import require_auth
from app.ml.disruption_intel import disruption_intel
from app.services.notification_service import notification_service
from pydantic import BaseModel, Field

router = APIRouter()


class Supplier(BaseModel):
    id: str
    name: str
    country: str = Field("US", min_length=2, max_length=2)
    spend_share: float = Field(0.2, ge=0, le=1)
    on_time_pct: float | None = Field(None, ge=0, le=100)
    financial_health_score: float | None = Field(None, ge=0, le=100)
    category: str | None = Field(None, description="Hint for alternate supplier ideas")


class DisruptionRequest(BaseModel):
    suppliers: list[Supplier]


@router.post("/analyze")
async def analyze_disruptions(
    _ctx: Annotated[AuthContext, Depends(require_auth)],
    body: DisruptionRequest,
):
    if not body.suppliers:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Provide at least one supplier."},
        )
    suppliers_payload = [s.model_dump() for s in body.suppliers]
    result = disruption_intel.predict_disruptions(suppliers_payload)
    worst = max(result["suppliers"], key=lambda x: x["risk_score"]) if result["suppliers"] else None
    if worst and worst["tier"] == "critical":
        notification_service.add(
            "Supplier risk critical",
            f"{worst['name']} scored {worst['risk_score']}",
            severity="warning",
        )
    return JSONResponse(content=result)
