from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import pandas as pd
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth_context import AuthContext
from app.api.deps_security import require_auth
from app.db.models import ForecastJob, ForecastJobStatus, utcnow
from app.db.session import get_db
from app.ml.forecaster import forecaster
from app.services.audit_service import write_audit
from app.services.notification_service import notification_service
from app.utils.sample_sales import build_sample_sales_rows

router = APIRouter()


class ForecastApiRequest(BaseModel):
    sales_data: list[dict[str, float | int | str]] = Field(
        ...,
        description="Rows with date and sales, same shape as CSV upload.",
    )
    days_ahead: int = Field(30, ge=1, le=365)


class SampleForecastRequest(BaseModel):
    days_ahead: int = Field(30, ge=1, le=365)
    history_days: int = Field(365, ge=30, le=3650)


@router.post("/sample")
async def create_sample_forecast(
    request: Request,
    body: SampleForecastRequest,
    ctx: Annotated[AuthContext, Depends(require_auth)],
    db: Annotated[Session, Depends(get_db)],
):
    """Authenticated one-click demo: synthetic history → same forecast path as POST /forecast."""
    sales_data = build_sample_sales_rows(history_days=body.history_days)
    df = pd.DataFrame(sales_data)
    df.columns = [str(c).strip().lower() for c in df.columns]
    forecast = forecaster.train_and_predict(df, days_ahead=body.days_ahead)
    idem = str(uuid.uuid4())
    job = ForecastJob(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user.id if ctx.user else None,
        idempotency_key=idem,
        status=ForecastJobStatus.completed.value if forecast.get("success") else ForecastJobStatus.failed.value,
        days_ahead=body.days_ahead,
        sales_json=[dict(r) for r in sales_data],
        result_json=forecast if forecast.get("success") else None,
        error_message=None if forecast.get("success") else forecast.get("message"),
        completed_at=utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    if forecast.get("success"):
        notification_service.add(
            "Forecast ready",
            f"Sample {body.days_ahead}-day horizon",
            severity="info",
        )
        write_audit(
            db,
            tenant_id=ctx.tenant_id,
            user_id=ctx.user.id if ctx.user else None,
            action="forecast.sample.completed",
            resource_type="forecast_job",
            resource_id=str(job.id),
            detail={"days_ahead": body.days_ahead},
            ip_address=request.client.host if request.client else None,
        )
    status = 200 if forecast.get("success") else 422
    payload = dict(forecast)
    payload["job_id"] = job.id
    return JSONResponse(status_code=status, content=payload)


@router.post("")
async def create_forecast(
    request: Request,
    body: ForecastApiRequest,
    ctx: Annotated[AuthContext, Depends(require_auth)],
    db: Annotated[Session, Depends(get_db)],
):
    df = pd.DataFrame(body.sales_data)
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "date" not in df.columns or "sales" not in df.columns:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": 'Each row must include "date" and "sales".'},
        )
    idem_header = request.headers.get("Idempotency-Key")
    if idem_header:
        cached = db.execute(
            select(ForecastJob).where(
                ForecastJob.tenant_id == ctx.tenant_id,
                ForecastJob.idempotency_key == idem_header,
            ),
        ).scalar_one_or_none()
        if cached and cached.result_json:
            out = dict(cached.result_json)
            out["job_id"] = cached.id
            return JSONResponse(status_code=200, content=out)

    forecast = forecaster.train_and_predict(df, days_ahead=body.days_ahead)
    idem = idem_header or str(uuid.uuid4())
    existing = db.execute(
        select(ForecastJob).where(ForecastJob.tenant_id == ctx.tenant_id, ForecastJob.idempotency_key == idem),
    ).scalar_one_or_none()
    if existing:
        job = existing
    else:
        job = ForecastJob(
            tenant_id=ctx.tenant_id,
            user_id=ctx.user.id if ctx.user else None,
            idempotency_key=idem,
            status=ForecastJobStatus.completed.value if forecast.get("success") else ForecastJobStatus.failed.value,
            days_ahead=body.days_ahead,
            sales_json=[dict(r) for r in body.sales_data],
            result_json=forecast if forecast.get("success") else None,
            error_message=None if forecast.get("success") else forecast.get("message"),
            completed_at=utcnow(),
        )
        db.add(job)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            job = db.execute(
                select(ForecastJob).where(ForecastJob.tenant_id == ctx.tenant_id, ForecastJob.idempotency_key == idem),
            ).scalar_one()
        else:
            db.refresh(job)

    if forecast.get("success"):
        notification_service.add(
            "Forecast ready",
            f"{body.days_ahead}-day horizon generated via API",
            severity="info",
        )
        write_audit(
            db,
            tenant_id=ctx.tenant_id,
            user_id=ctx.user.id if ctx.user else None,
            action="forecast.sync.completed",
            resource_type="forecast_job",
            resource_id=str(job.id),
            detail={"days_ahead": body.days_ahead},
            ip_address=request.client.host if request.client else None,
        )
    status = 200 if forecast.get("success") else 422
    payload = dict(forecast)
    payload["job_id"] = job.id
    return JSONResponse(status_code=status, content=payload)
