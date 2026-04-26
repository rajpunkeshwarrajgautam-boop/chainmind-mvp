from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth_context import AuthContext
from app.api.deps_security import require_auth
from app.db.models import IntegrationRun
from app.db.session import get_db
from app.integrations.catalog import CATALOG, list_catalog
from app.services.data_ingestion import connector

router = APIRouter()


@router.get("/status")
async def integration_status(_ctx: Annotated[AuthContext, Depends(require_auth)]):
    return connector.status()


@router.get("/catalog")
async def integration_catalog(_ctx: Annotated[AuthContext, Depends(require_auth)]):
    return list_catalog()


class ReconcileRequest(BaseModel):
    connector_id: str = Field(..., description="Key from /catalog")
    payload: dict[str, Any] = Field(default_factory=dict)


@router.post("/reconcile")
async def integration_reconcile(
    _ctx: Annotated[AuthContext, Depends(require_auth)],
    body: ReconcileRequest,
    db: Annotated[Session, Depends(get_db)],
):
    if body.connector_id not in CATALOG:
        return {"success": False, "message": "Unknown connector_id"}
    spec = CATALOG[body.connector_id]
    reconciliation = {
        "checks_run": [c.get("name") for c in spec.get("reconciliation_checks", [])],
        "status": "template_only",
        "note": "Wire ERP credentials + CDC to execute checks; this persists the run for audit.",
        "implementation": "mvp_stub",
        "next_steps": "Add connector credentials to env, implement connector.execute in app/services/data_ingestion.py, then replace template_only status.",
    }
    run = IntegrationRun(
        tenant_id=_ctx.tenant_id,
        connector_type=body.connector_id,
        status="recorded",
        payload=body.payload,
        reconciliation=reconciliation,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return {"success": True, "integration_run_id": run.id, "reconciliation": reconciliation}
