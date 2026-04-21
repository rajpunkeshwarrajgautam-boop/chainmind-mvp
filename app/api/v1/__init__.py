from fastapi import APIRouter

from app.api.v1 import auth as auth_routes
from app.api.v1 import billing as billing_routes
from app.api.v1 import external_signals as external_signals_routes
from app.api.v1 import governance as governance_routes
from app.api.v1 import oidc_sso as oidc_sso_routes
from app.api.v1 import data_quality as data_quality_routes
from app.api.v1 import ml_ops as ml_ops_routes
from app.api.v1 import disruptions as disruption_routes
from app.api.v1 import forecast_jobs as forecast_jobs_routes
from app.api.v1 import forecasting as forecasting_routes
from app.api.v1 import integrations as integrations_routes
from app.api.v1 import inventory as inventory_routes
from app.api.v1 import notifications as notifications_routes
from app.api.v1 import reporting as reporting_routes
from app.api.v1 import scenarios as scenario_routes
from app.api.v1 import uploads as uploads_routes

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
api_router.include_router(oidc_sso_routes.router, prefix="/auth", tags=["auth"])
api_router.include_router(forecast_jobs_routes.router, prefix="/forecast", tags=["forecasting"])
api_router.include_router(forecasting_routes.router, prefix="/forecast", tags=["forecasting"])
api_router.include_router(uploads_routes.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(inventory_routes.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(disruption_routes.router, prefix="/disruptions", tags=["disruptions"])
api_router.include_router(integrations_routes.router, prefix="/integrations", tags=["integrations"])
api_router.include_router(scenario_routes.router, prefix="/scenarios", tags=["scenarios"])
api_router.include_router(reporting_routes.router, prefix="/reporting", tags=["reporting"])
api_router.include_router(notifications_routes.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(ml_ops_routes.router, prefix="/ml", tags=["ml"])
api_router.include_router(data_quality_routes.router, prefix="/data-quality", tags=["data-quality"])
api_router.include_router(billing_routes.router, prefix="/billing", tags=["billing"])
api_router.include_router(external_signals_routes.router, prefix="/signals", tags=["signals"])
api_router.include_router(governance_routes.router, prefix="/governance", tags=["governance"])

__all__ = ["api_router"]
