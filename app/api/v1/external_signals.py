from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.adapters.open_meteo import fetch_daily_temperature
from app.api.auth_context import AuthContext
from app.api.deps_security import require_auth
from app.core.config import get_settings

router = APIRouter()


@router.get("/weather-sample")
async def weather_sample(
    _ctx: Annotated[AuthContext, Depends(require_auth)],
    lat: float = 40.7128,
    lon: float = -74.006,
):
    settings = get_settings()
    if not settings.open_meteo_enabled:
        raise HTTPException(status_code=503, detail="Open-Meteo adapter disabled.")
    return fetch_daily_temperature(lat, lon)
