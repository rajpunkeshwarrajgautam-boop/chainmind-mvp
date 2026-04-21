from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth_context import AuthContext
from app.api.deps_security import require_auth
from app.db.models import BacktestRun, ModelVersion
from app.db.session import get_db
from app.ml.evaluation import run_backtest

router = APIRouter()


class BacktestRequest(BaseModel):
    sales_data: list[dict[str, Any]] = Field(...)
    holdout_days: int = Field(7, ge=3, le=60)


@router.post("/backtests")
async def create_backtest(
    ctx: Annotated[AuthContext, Depends(require_auth)],
    body: BacktestRequest,
    db: Annotated[Session, Depends(get_db)],
):
    result = run_backtest(body.sales_data, holdout_days=body.holdout_days)
    if not result.get("success"):
        return result
    mv = db.execute(select(ModelVersion).where(ModelVersion.is_champion.is_(True))).scalar_one_or_none()
    br = BacktestRun(
        tenant_id=ctx.tenant_id,
        model_version_id=mv.id if mv else None,
        metrics={"mape": result["mape"], "holdout_days": result["holdout_days"]},
        segments=result.get("segments"),
    )
    db.add(br)
    db.commit()
    db.refresh(br)
    return {"success": True, "backtest_id": br.id, **result}


@router.get("/model-versions")
async def list_model_versions(
    _ctx: Annotated[AuthContext, Depends(require_auth)],
    db: Annotated[Session, Depends(get_db)],
):
    rows = db.scalars(select(ModelVersion).order_by(ModelVersion.created_at.desc()).limit(50)).all()
    return {
        "items": [
            {
                "id": r.id,
                "name": r.name,
                "version_tag": r.version_tag,
                "artifact_uri": r.artifact_uri,
                "is_champion": r.is_champion,
                "metrics": r.metrics,
            }
            for r in rows
        ],
    }
