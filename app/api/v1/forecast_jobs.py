from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth_context import AuthContext
from app.api.deps_security import require_auth
from app.db.models import ForecastJob, ForecastJobStatus
from app.db.session import get_db
from app.services.audit_service import write_audit
from app.workers.tasks_forecast import run_forecast_job

router = APIRouter()


@router.get("/jobs")
async def list_forecast_jobs(
    ctx: Annotated[AuthContext, Depends(require_auth)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 20,
):
    limit = max(1, min(limit, 100))
    rows = (
        db.execute(
            select(ForecastJob)
            .where(ForecastJob.tenant_id == ctx.tenant_id)
            .order_by(desc(ForecastJob.created_at))
            .limit(limit),
        )
        .scalars()
        .all()
    )
    return {
        "items": [
            {
                "id": j.id,
                "status": j.status,
                "days_ahead": j.days_ahead,
                "has_result": j.result_json is not None,
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            }
            for j in rows
        ],
    }


class ForecastJobCreate(BaseModel):
    sales_data: list[dict[str, float | int | str]] = Field(...)
    days_ahead: int = Field(30, ge=1, le=365)


@router.post("/jobs")
async def enqueue_forecast(
    body: ForecastJobCreate,
    ctx: Annotated[AuthContext, Depends(require_auth)],
    db: Annotated[Session, Depends(get_db)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    key = idempotency_key or str(uuid.uuid4())
    existing = db.execute(
        select(ForecastJob).where(ForecastJob.tenant_id == ctx.tenant_id, ForecastJob.idempotency_key == key),
    ).scalar_one_or_none()
    if existing:
        return {"job_id": existing.id, "status": existing.status, "deduplicated": True}

    job = ForecastJob(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user.id if ctx.user else None,
        idempotency_key=key,
        status=ForecastJobStatus.pending.value,
        days_ahead=body.days_ahead,
        sales_json=[dict(r) for r in body.sales_data],
    )
    db.add(job)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.execute(
            select(ForecastJob).where(ForecastJob.tenant_id == ctx.tenant_id, ForecastJob.idempotency_key == key),
        ).scalar_one()
        return {"job_id": existing.id, "status": existing.status, "deduplicated": True}
    db.refresh(job)
    run_forecast_job.delay(job.id)
    write_audit(
        db,
        tenant_id=ctx.tenant_id,
        user_id=ctx.user.id if ctx.user else None,
        action="forecast.job.enqueued",
        resource_type="forecast_job",
        resource_id=str(job.id),
        detail={"idempotency_key": key},
    )
    return {"job_id": job.id, "status": job.status, "deduplicated": False}


@router.get("/jobs/{job_id}")
async def get_forecast_job(
    job_id: int,
    ctx: Annotated[AuthContext, Depends(require_auth)],
    db: Annotated[Session, Depends(get_db)],
):
    job = db.get(ForecastJob, job_id)
    if not job or job.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "status": job.status,
        "result": job.result_json,
        "error": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }
