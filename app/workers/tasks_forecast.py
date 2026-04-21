from __future__ import annotations

import logging

import pandas as pd
from sqlalchemy.orm import Session

from app.db.models import ForecastJob, ForecastJobStatus, utcnow
from app.db.session import get_session_factory
from app.ml.forecaster import forecaster
from app.workers.celery_app import celery_app

log = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5, name="forecast.run_job")
def run_forecast_job(self, job_id: int) -> dict:
    factory = get_session_factory()
    db: Session = factory()
    try:
        job = db.get(ForecastJob, job_id)
        if not job:
            return {"ok": False, "error": "job not found"}
        job.status = ForecastJobStatus.running.value
        db.commit()

        df = pd.DataFrame(job.sales_json)
        df.columns = [str(c).strip().lower() for c in df.columns]
        result = forecaster.train_and_predict(df, days_ahead=job.days_ahead)
        if not result.get("success"):
            job.status = ForecastJobStatus.failed.value
            job.error_message = result.get("message", "forecast failed")
            job.completed_at = utcnow()
            db.commit()
            return {"ok": False, "job_id": job_id, "error": job.error_message}

        job.status = ForecastJobStatus.completed.value
        job.result_json = result
        job.completed_at = utcnow()
        db.commit()
        return {"ok": True, "job_id": job_id}
    except Exception as exc:  # noqa: BLE001
        log.exception("forecast job failed")
        job = db.get(ForecastJob, job_id)
        if job:
            job.status = ForecastJobStatus.failed.value
            job.error_message = str(exc)
            job.completed_at = utcnow()
            db.commit()
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {"ok": False, "job_id": job_id, "error": str(exc)}
    finally:
        db.close()
