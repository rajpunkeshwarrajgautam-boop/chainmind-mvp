#!/usr/bin/env python3
"""Smoke-test the API vertical slice.

  # Against a running server (e.g. Docker or uvicorn on port 8000)
  python scripts/verify_vertical_slice.py

  # Same checks in-process (no server; used in CI)
  python scripts/verify_vertical_slice.py --in-process

  CHAINMIND_BASE_URL=http://127.0.0.1:8765 python scripts/verify_vertical_slice.py

  # Real pilot host + attachable evidence (redacted JSON under directory)
  CHAINMIND_BASE_URL=https://api.example.com python scripts/verify_vertical_slice.py --evidence-dir pilot-evidence/deploy-2026-04-21
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent


def _silence_authlib_jose_deprecation() -> None:
    """Match tests/conftest.py: Authlib forces 'always' for AuthlibDeprecationWarning; prepend ignore after."""
    try:
        import authlib.deprecate  # noqa: F401
        from authlib.deprecate import AuthlibDeprecationWarning
    except ImportError:
        return
    warnings.filterwarnings("ignore", category=AuthlibDeprecationWarning)


if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import httpx

BASE = os.environ.get("CHAINMIND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def _reject_placeholder_base() -> None:
    if "your-host" in BASE.lower():
        print(
            "CHAINMIND_BASE_URL still contains the placeholder 'your-host'. "
            "Set it to your real API origin (e.g. https://api.example.com) and re-run.",
            file=sys.stderr,
        )
        raise SystemExit(2)


def _safe_json(resp: httpx.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        return {"_non_json": resp.text[:4000]}


def _redact_register(body: dict[str, Any]) -> dict[str, Any]:
    out = dict(body)
    if "access_token" in out:
        out["access_token"] = "***REDACTED***"
    return out


def _write_evidence(evidence_dir: Path, name: str, payload: Any) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    path = evidence_dir / name
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _run_slice_http(
    client: httpx.Client,
    base_label: str,
    *,
    evidence_dir: Path | None,
) -> int:
    slug = f"v{uuid.uuid4().hex[:10]}"
    email = f"admin@{slug}.example.com"
    h = client.get("/health")
    h.raise_for_status()
    if evidence_dir:
        _write_evidence(evidence_dir, "health.json", {"url": f"{base_label}/health", **_safe_json(h)})

    reg = client.post(
        "/api/v1/auth/register",
        json={
            "tenant_slug": slug,
            "tenant_name": "Verify tenant",
            "email": email,
            "password": "longpassword123",
        },
    )
    if reg.status_code != 200:
        print("register failed:", reg.status_code, reg.text, file=sys.stderr)
        if evidence_dir:
            _write_evidence(
                evidence_dir,
                "register_failed.json",
                {"status_code": reg.status_code, "body": _safe_json(reg)},
            )
        return 1
    reg_body = reg.json()
    token = reg_body["access_token"]
    if evidence_dir:
        _write_evidence(
            evidence_dir,
            "register.json",
            {"url": f"{base_label}/api/v1/auth/register", "body": _redact_register(reg_body)},
        )

    auth = {"Authorization": f"Bearer {token}"}
    s = client.post(
        "/api/v1/forecast/sample",
        headers=auth,
        json={"days_ahead": 7, "history_days": 50},
    )
    if s.status_code != 200 or not s.json().get("success"):
        print("sample forecast failed:", s.status_code, s.text, file=sys.stderr)
        if evidence_dir:
            _write_evidence(evidence_dir, "forecast_sample_failed.json", {"status_code": s.status_code, "body": _safe_json(s)})
        return 1
    sample_body = s.json()
    job_id = sample_body["job_id"]
    if evidence_dir:
        sb = dict(sample_body)
        preds = sb.get("predictions")
        if isinstance(preds, list) and len(preds) > 12:
            sb["predictions"] = preds[:12] + [f"... truncated ({len(preds)} total)"]
        _write_evidence(evidence_dir, "forecast_sample.json", {"url": f"{base_label}/api/v1/forecast/sample", "body": sb})

    g = client.get(f"/api/v1/forecast/jobs/{job_id}", headers=auth)
    if g.status_code != 200:
        print("get job failed:", g.status_code, g.text, file=sys.stderr)
        if evidence_dir:
            _write_evidence(evidence_dir, "forecast_job_failed.json", {"status_code": g.status_code, "body": _safe_json(g)})
        return 1
    body = g.json()
    if body.get("status") != "completed":
        print("unexpected job status:", body, file=sys.stderr)
        if evidence_dir:
            _write_evidence(evidence_dir, "forecast_job_unexpected.json", body)
        return 1
    n = len(body.get("result", {}).get("predictions", []))
    if evidence_dir:
        jb = dict(body)
        rj = jb.get("result")
        if isinstance(rj, dict) and isinstance(rj.get("predictions"), list) and len(rj["predictions"]) > 12:
            rj = dict(rj)
            plist = rj["predictions"]
            rj["predictions"] = plist[:12] + [f"... truncated ({len(plist)} total)"]
            jb["result"] = rj
        _write_evidence(evidence_dir, "forecast_job.json", {"url": f"{base_label}/api/v1/forecast/jobs/{job_id}", "body": jb})

    if evidence_dir:
        _write_evidence(
            evidence_dir,
            "summary.json",
            {
                "base_url": base_label,
                "utc": datetime.now(timezone.utc).isoformat(),
                "tenant_slug": slug,
                "job_id": job_id,
                "predictions_count": n,
                "success": True,
            },
        )

    print(f"OK base={base_label} tenant={slug} job_id={job_id} predictions={n}")
    return 0


def _run_slice_testclient(client: Any, base_label: str) -> int:
    """TestClient-compatible: .get/.post with str paths."""
    slug = f"v{uuid.uuid4().hex[:10]}"
    email = f"admin@{slug}.example.com"
    h = client.get("/health")
    if h.status_code != 200:
        print("health failed:", h.status_code, h.text, file=sys.stderr)
        return 1
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "tenant_slug": slug,
            "tenant_name": "Verify tenant",
            "email": email,
            "password": "longpassword123",
        },
    )
    if reg.status_code != 200:
        print("register failed:", reg.status_code, reg.text, file=sys.stderr)
        return 1
    token = reg.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    s = client.post(
        "/api/v1/forecast/sample",
        headers=auth,
        json={"days_ahead": 7, "history_days": 50},
    )
    if s.status_code != 200 or not s.json().get("success"):
        print("sample forecast failed:", s.status_code, s.text, file=sys.stderr)
        return 1
    job_id = s.json()["job_id"]
    g = client.get(f"/api/v1/forecast/jobs/{job_id}", headers=auth)
    if g.status_code != 200:
        print("get job failed:", g.status_code, g.text, file=sys.stderr)
        return 1
    body = g.json()
    if body.get("status") != "completed":
        print("unexpected job status:", body, file=sys.stderr)
        return 1
    n = len(body.get("result", {}).get("predictions", []))
    print(f"OK base={base_label} tenant={slug} job_id={job_id} predictions={n}")
    return 0


def main() -> int:
    _silence_authlib_jose_deprecation()
    parser = argparse.ArgumentParser(description="Vertical slice smoke test")
    parser.add_argument(
        "--in-process",
        action="store_true",
        help="Run against TestClient + in-memory SQLite (no HTTP server).",
    )
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=None,
        help="Write redacted JSON artifacts for pilot evidence (HTTP mode only).",
    )
    args = parser.parse_args()

    if args.in_process and args.evidence_dir:
        print("--evidence-dir is only supported for HTTP runs (omit --in-process).", file=sys.stderr)
        return 2

    if args.in_process:
        os.environ.setdefault("ENVIRONMENT", "test")
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        os.environ.setdefault("JWT_SECRET", "verify-jwt-secret-minimum-32-characters-long")
        os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
        # TestClient uses host "testserver"; clear trusted hosts from a local .env.
        os.environ["TRUSTED_HOSTS"] = ""
        from app.db.session import dispose_engine

        dispose_engine()
        from app.main import create_app
        from fastapi.testclient import TestClient

        with TestClient(create_app()) as client:
            return _run_slice_testclient(client, "in-process")

    _reject_placeholder_base()
    with httpx.Client(base_url=BASE, timeout=60.0) as c:
        return _run_slice_http(c, BASE, evidence_dir=args.evidence_dir)


if __name__ == "__main__":
    raise SystemExit(main())
