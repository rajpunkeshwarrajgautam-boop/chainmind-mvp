from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1 import api_router
from app.core.config import get_settings
from app.db.bootstrap import ensure_bootstrap_admin, ensure_default_model_version
from app.db.session import check_database_connectivity, create_tables, dispose_engine, get_session_factory
from app.web.legacy import router as legacy_router

log = logging.getLogger("chainmind")

REQUESTS = Counter(
    "chainmind_http_requests_total",
    "HTTP requests",
    ["method", "path_template", "status"],
)
LATENCY = Histogram(
    "chainmind_http_request_duration_seconds",
    "Latency",
    ["method", "path_template"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)


def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_logging()
    create_tables()
    db = get_session_factory()()
    try:
        ensure_default_model_version(db)
        boot = ensure_bootstrap_admin(db)
        if boot:
            log.warning("Bootstrap admin created: %s", boot.get("admin_email"))
            log.warning("One-time API key emitted (see logs once): set BOOTSTRAP_ADMIN_* only on first boot")
    finally:
        db.close()
    yield
    dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="ChainMind",
        version="2.0.0",
        lifespan=lifespan,
        description="Production-hardened API: multi-tenant persistence, jobs, observability.",
    )

    limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if settings.trusted_host_list:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_host_list)

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.jwt_secret,
        max_age=3600,
        same_site="lax",
        https_only=settings.environment == "production",
    )

    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
        route = request.scope.get("route")
        template = getattr(route, "path", request.url.path) if route else request.url.path
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        LATENCY.labels(request.method, template).observe(elapsed)
        REQUESTS.labels(request.method, template, str(response.status_code)).inc()
        return response

    app.include_router(api_router)
    app.include_router(legacy_router)

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "chainmind"}

    @app.get("/ready", tags=["ops"])
    async def ready() -> JSONResponse:
        db_ok = check_database_connectivity()
        redis_ok = True
        try:
            import redis

            r = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1)
            r.ping()
        except Exception:
            redis_ok = False
        ok = db_ok and redis_ok
        return JSONResponse(
            status_code=200 if ok else 503,
            content={"ready": ok, "database": db_ok, "redis": redis_ok},
        )

    @app.get("/metrics", tags=["ops"])
    async def metrics() -> Response:
        data = generate_latest()
        return Response(data, media_type=CONTENT_TYPE_LATEST)

    def custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
        )
        openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Obtain a token from POST /api/v1/auth/register or /api/v1/auth/login, then Authorize here.",
        }
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]

    return app
