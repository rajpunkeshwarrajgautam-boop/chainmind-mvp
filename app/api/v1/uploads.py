from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth_context import AuthContext
from app.api.deps_security import require_auth
from app.core.config import get_settings
from app.db.models import ForecastJob, ForecastJobStatus, Upload as UploadModel, utcnow
from app.db.session import get_db
from app.ml.forecaster import forecaster
from app.services.audit_service import write_audit
from app.utils.csv_io import load_sales_frame

router = APIRouter()


def _read_upload_limited(raw: bytes, settings) -> str:
    if len(raw) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds max_upload_bytes ({settings.max_upload_bytes}).")
    return raw.decode("utf-8", errors="replace")


@router.post("/preview")
async def upload_preview(
    ctx: Annotated[AuthContext, Depends(require_auth)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
):
    settings = get_settings()
    raw_bytes = await file.read()
    raw = _read_upload_limited(raw_bytes, settings)
    try:
        df = load_sales_frame(raw)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {exc}") from exc

    preview = df.head(8).to_dict(orient="records")
    cols = [str(c).strip().lower() for c in df.columns]
    return {
        "row_count": int(len(df)),
        "columns": cols,
        "preview": preview,
        "filename": file.filename or "upload.csv",
    }


@router.post("/forecast")
async def upload_and_forecast(
    request: Request,
    ctx: Annotated[AuthContext, Depends(require_auth)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
    days_ahead: Annotated[int, Form()] = 30,
):
    settings = get_settings()
    if days_ahead < 1 or days_ahead > 365:
        raise HTTPException(status_code=400, detail="days_ahead must be 1–365")

    raw_bytes = await file.read()
    raw = _read_upload_limited(raw_bytes, settings)
    try:
        df = load_sales_frame(raw)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {exc}") from exc

    df.columns = [str(c).strip().lower() for c in df.columns]
    if "date" not in df.columns or "sales" not in df.columns:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": 'CSV must include "date" and "sales" columns.'},
        )

    storage_key = f"{ctx.tenant_id}/{file.filename or 'upload.csv'}"
    body_store = raw_bytes[: settings.max_upload_bytes]
    try:
        from app.storage.s3_store import put_bytes

        if settings.aws_s3_bucket and settings.aws_region:
            put_bytes(key=storage_key, body=body_store, content_type=file.content_type)
            body_store = None
    except Exception:
        pass

    up = UploadModel(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user.id if ctx.user else None,
        filename=file.filename or "upload.csv",
        content_type=file.content_type,
        size_bytes=len(raw_bytes),
        body=body_store,
    )
    db.add(up)
    db.flush()

    sales_rows = df.to_dict(orient="records")
    forecast = forecaster.train_and_predict(df, days_ahead=days_ahead)
    idem = str(uuid.uuid4())
    job = ForecastJob(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user.id if ctx.user else None,
        idempotency_key=idem,
        status=ForecastJobStatus.completed.value if forecast.get("success") else ForecastJobStatus.failed.value,
        days_ahead=days_ahead,
        sales_json=[dict(r) for r in sales_rows],
        result_json=forecast if forecast.get("success") else None,
        error_message=None if forecast.get("success") else forecast.get("message"),
        completed_at=utcnow(),
    )
    db.add(job)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Could not persist forecast job") from None
    db.refresh(job)

    if forecast.get("success"):
        write_audit(
            db,
            tenant_id=ctx.tenant_id,
            user_id=ctx.user.id if ctx.user else None,
            action="forecast.upload.completed",
            resource_type="forecast_job",
            resource_id=str(job.id),
            detail={"upload_id": up.id, "days_ahead": days_ahead},
            ip_address=request.client.host if request.client else None,
        )

    status = 200 if forecast.get("success") else 422
    payload = dict(forecast)
    payload["job_id"] = job.id
    payload["upload_id"] = up.id
    return JSONResponse(status_code=status, content=payload)
