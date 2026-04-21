from __future__ import annotations

import os
import uuid

import pytest

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-minimum-32-characters")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
# Prevent local .env TRUSTED_HOSTS from rejecting TestClient host "testserver".
os.environ["TRUSTED_HOSTS"] = ""


@pytest.fixture()
def client():
    from app.db.session import dispose_engine

    dispose_engine()
    from app.main import create_app
    from fastapi.testclient import TestClient

    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    slug = f"t{uuid.uuid4().hex[:10]}"
    res = client.post(
        "/api/v1/auth/register",
        json={
            "tenant_slug": slug,
            "tenant_name": "Test tenant",
            "email": f"admin@{slug}.example.com",
            "password": "longpassword123",
        },
    )
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
