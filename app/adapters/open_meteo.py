"""Public Open-Meteo API (no key) — production should add SLAs, caching, and fallbacks."""

from __future__ import annotations

from typing import Any

import httpx


def fetch_daily_temperature(lat: float, lon: float) -> dict[str, Any]:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max",
        "forecast_days": 7,
        "timezone": "auto",
    }
    with httpx.Client(timeout=10.0) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
        return {"provider": "open-meteo", "data": r.json()}
