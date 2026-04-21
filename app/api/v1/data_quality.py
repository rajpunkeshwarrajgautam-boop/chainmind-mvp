from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.auth_context import AuthContext
from app.api.deps_security import require_auth
from app.services.data_quality import analyze_sales_frame

router = APIRouter()


class DataQualityRequest(BaseModel):
    sales_data: list[dict[str, Any]] = Field(...)


@router.post("/report")
async def data_quality_report(
    _ctx: Annotated[AuthContext, Depends(require_auth)],
    body: DataQualityRequest,
):
    return analyze_sales_frame(body.sales_data)
