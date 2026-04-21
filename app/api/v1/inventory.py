from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.auth_context import AuthContext
from app.api.deps_security import require_auth
from app.ml.inventory_optimizer import inventory_optimizer
from app.services.notification_service import notification_service

router = APIRouter()


class InventoryRequest(BaseModel):
    sales_data: list[dict[str, Any]] | None = None
    daily_demand_mean: float | None = None
    daily_demand_std: float | None = None
    current_on_hand: float = Field(0, ge=0)
    lead_time_days: int = Field(7, ge=1, le=120)
    review_period_days: int = Field(1, ge=1, le=30)
    ordering_cost: float = Field(50, ge=0)
    unit_cost: float = Field(10, ge=0)
    holding_cost_rate_annual: float = Field(0.2, ge=0, le=1)
    service_level_z: float = Field(1.65, ge=0.5, le=3.5)
    locations: list[dict[str, Any]] | None = None


@router.post("/optimize")
async def optimize_inventory(
    _ctx: Annotated[AuthContext, Depends(require_auth)],
    body: InventoryRequest,
):
    try:
        payload = body.model_dump()
        result = inventory_optimizer.calculate_optimal_stock_levels(payload)
        notification_service.add(
            "Inventory plan refreshed",
            f"ROP {result['reorder_point']} | EOQ {result['order_quantity_eoq']}",
            severity="info",
        )
        return JSONResponse(content=result)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=422,
            content={"success": False, "message": str(exc)},
        )
