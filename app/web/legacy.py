from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api.deps_security import get_or_create_default_tenant, require_auth
from app.api.v1.forecasting import ForecastApiRequest
from app.core.config import get_settings
from app.db.models import Upload as UploadModel
from app.db.session import get_db
from app.ml.forecaster import forecaster
from app.services.notification_service import notification_service
from app.utils.csv_io import load_sales_frame
from app.utils.sample_sales import build_sample_sales_rows
from sqlalchemy.orm import Session

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(ROOT_DIR / "templates"))
log = logging.getLogger(__name__)

router = APIRouter(include_in_schema=False)


@router.get("/", response_model=None)
async def read_root(request: Request) -> HTMLResponse | RedirectResponse:
    if get_settings().environment == "production":
        return RedirectResponse(url="/docs", status_code=302)
    return templates.TemplateResponse(request, "index.html", {"result": None})


@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if get_settings().environment == "production":
        raise HTTPException(
            status_code=404,
            detail="HTML upload disabled in production. Use POST /api/v1/uploads/forecast with a Bearer token.",
        )
    try:
        raw_bytes = await file.read()
        raw = raw_bytes.decode("utf-8", errors="replace")
        df = load_sales_frame(raw)
        result = forecaster.train_and_predict(df)
        if result.get("success"):
            notification_service.add(
                "Forecast generated",
                "CSV upload processed for dashboard view",
                severity="info",
            )
            tenant = get_or_create_default_tenant(db)
            storage_key = f"{tenant.id}/{file.filename or 'upload.csv'}"
            body_store = raw_bytes[: 5_000_000]
            try:
                from app.storage.s3_store import put_bytes

                s = get_settings()
                if s.aws_s3_bucket and s.aws_region:
                    put_bytes(key=storage_key, body=body_store, content_type=file.content_type)
                    body_store = None
            except Exception:
                log.warning("S3 upload failed; storing bytes in DB instead", exc_info=True)
            up = UploadModel(
                tenant_id=tenant.id,
                user_id=None,
                filename=file.filename or "upload.csv",
                content_type=file.content_type,
                size_bytes=len(raw_bytes),
                body=body_store,
            )
            db.add(up)
            db.commit()
        return templates.TemplateResponse(request, "index.html", {"result": result})
    except Exception as exc:  # noqa: BLE001
        result = {
            "success": False,
            "error": str(exc),
            "message": "Failed to process file. Please ensure it is a valid CSV.",
        }
        return templates.TemplateResponse(request, "index.html", {"result": result})


@router.post("/generate-sample")
async def generate_sample(request: Request):
    if get_settings().environment == "production":
        raise HTTPException(
            status_code=404,
            detail="Sample HTML flow disabled in production. Use POST /api/v1/forecast/sample with a Bearer token.",
        )
    rows = build_sample_sales_rows(history_days=365)
    df = pd.DataFrame(rows)
    result = forecaster.train_and_predict(df)
    if result.get("success"):
        notification_service.add(
            "Sample forecast",
            "Synthetic series generated for exploration",
            severity="info",
        )
    return templates.TemplateResponse(request, "index.html", {"result": result})


@router.post("/api/forecast")
async def legacy_api_forecast(
    body: ForecastApiRequest,
    _: None = Depends(require_auth),
):
    try:
        df = pd.DataFrame(body.sales_data)
        df.columns = [str(c).strip().lower() for c in df.columns]
        if "date" not in df.columns or "sales" not in df.columns:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": 'Each row must include "date" and "sales".',
                },
            )
        forecast = forecaster.train_and_predict(df, days_ahead=body.days_ahead)
        status = 200 if forecast.get("success") else 422
        return JSONResponse(status_code=status, content=forecast)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(exc), "message": "API forecast failed"},
        )
