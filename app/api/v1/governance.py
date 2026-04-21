from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth_context import AuthContext
from app.api.deps_security import require_planner
from app.db.models import ForecastExplainability, ForecastHumanOverride, ForecastJob
from app.db.session import get_db
from app.ml.explainability import explain_forecast_from_history
from app.services.audit_service import write_audit

router = APIRouter()


@router.post("/forecasts/{job_id}/explain")
async def explain_forecast_job(
    job_id: int,
    ctx: Annotated[AuthContext, Depends(require_planner)],
    db: Annotated[Session, Depends(get_db)],
):
    job = db.get(ForecastJob, job_id)
    if not job or job.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Forecast job not found")
    expl = explain_forecast_from_history(job.sales_json)
    if not expl.get("success"):
        return expl
    row = ForecastExplainability(
        tenant_id=ctx.tenant_id,
        forecast_job_id=job.id,
        feature_importance=expl["feature_importance"],
        notes="Auto-generated from permutation importance on training window.",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        tenant_id=ctx.tenant_id,
        user_id=ctx.user.id if ctx.user else None,
        action="forecast.explainability.created",
        resource_type="forecast_explainability",
        resource_id=str(row.id),
        detail={"job_id": job_id},
    )
    return {"success": True, "explainability_id": row.id, **expl}


class OverrideBody(BaseModel):
    adjusted_result_json: dict[str, Any] = Field(..., description="Must include dates/predictions keys.")
    rationale: str = Field(..., min_length=3)


@router.post("/forecasts/{job_id}/override")
async def override_forecast_job(
    job_id: int,
    body: OverrideBody,
    ctx: Annotated[AuthContext, Depends(require_planner)],
    db: Annotated[Session, Depends(get_db)],
):
    job = db.get(ForecastJob, job_id)
    if not job or job.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Forecast job not found")
    if not ctx.user:
        raise HTTPException(status_code=400, detail="Human overrides require a user-bound session.")
    row = ForecastHumanOverride(
        tenant_id=ctx.tenant_id,
        forecast_job_id=job.id,
        user_id=ctx.user.id,
        rationale=body.rationale,
        adjusted_result_json=body.adjusted_result_json,
    )
    db.add(row)
    job.result_json = body.adjusted_result_json
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        tenant_id=ctx.tenant_id,
        user_id=ctx.user.id,
        action="forecast.human_override",
        resource_type="forecast_job",
        resource_id=str(job.id),
        detail={"override_id": row.id},
    )
    return {"success": True, "override_id": row.id}
