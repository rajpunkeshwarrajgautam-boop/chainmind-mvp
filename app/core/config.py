from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = Field(default="development", description="development|staging|production|test")

    database_url: str = Field(
        default="sqlite:///./chainmind.db",
        description="SQLAlchemy URL (Postgres in prod, SQLite for local tests).",
    )
    redis_url: str = Field(default="redis://localhost:6379/0")
    celery_broker_url: str | None = Field(
        default=None,
        description="Defaults to redis_url when unset.",
    )
    celery_result_backend: str | None = Field(default=None, description="Defaults to redis_url.")

    jwt_secret: str = Field(
        default="chainmind-development-jwt-secret-min-32-chars",
        min_length=16,
        description="Rotate in production; used to sign JWT access tokens.",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://127.0.0.1:8000",
        description="Comma-separated origins.",
    )
    trusted_hosts: str | None = Field(default=None, description="Comma-separated hosts for TrustedHostMiddleware.")

    # Legacy single-key auth (superseded by DB API keys + JWT)
    chainmind_api_key: str | None = None
    access_token: str = "chainmind-dev-token"
    demo_user: str = "demo"
    demo_password: str = "demo"

    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None
    default_tenant_slug: str = "default"

    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_id_starter: str | None = None
    stripe_tax_behavior: str = Field(default="exclusive", description="exclusive|inclusive for Checkout tax.")
    stripe_customer_portal_return_url: str | None = None

    rate_limit_default: str = "200/minute"

    # External signals (adapters; keys optional)
    open_meteo_enabled: bool = True
    fred_api_key: str | None = None

    max_upload_bytes: int = 5_000_000

    # OIDC / enterprise SSO (Okta, Azure AD, Auth0, etc.)
    oidc_issuer: str | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: str | None = None
    oidc_redirect_uri: str | None = Field(
        default=None,
        description="Registered redirect, e.g. https://api.example.com/api/v1/auth/oidc/callback",
    )
    oidc_scope: str = "openid email profile"
    oidc_role_claim: str = "groups"
    oidc_admin_groups: str = Field(
        default="chainmind-admins",
        description="Comma-separated group names mapped to admin role.",
    )
    oidc_jit_provision: bool = Field(default=False, description="Create local user on first SSO login.")

    # Object storage (optional; otherwise uploads stay in Postgres BYTEA)
    aws_s3_bucket: str | None = None
    aws_s3_prefix: str = "uploads/"
    aws_kms_key_id: str | None = Field(default=None, description="SSE-KMS key for S3 uploads.")
    aws_region: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def trusted_host_list(self) -> list[str] | None:
        if not self.trusted_hosts:
            return None
        return [h.strip() for h in self.trusted_hosts.split(",") if h.strip()]

    @property
    def celery_broker(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def celery_backend(self) -> str:
        return self.celery_result_backend or self.redis_url


def get_settings() -> Settings:
    return Settings()


# Mutable alias refreshed on import; tests may monkeypatch get_settings.
settings = get_settings()
