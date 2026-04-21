from __future__ import annotations

from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.core.config import get_settings


def put_bytes(*, key: str, body: bytes, content_type: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    if not settings.aws_s3_bucket or not settings.aws_region:
        raise RuntimeError("S3 not configured (AWS_S3_BUCKET, AWS_REGION).")
    extra: dict[str, Any] = {}
    if settings.aws_kms_key_id:
        extra["ServerSideEncryption"] = "aws:kms"
        extra["SSEKMSKeyId"] = settings.aws_kms_key_id
    client = boto3.client("s3", region_name=settings.aws_region)
    full_key = f"{settings.aws_s3_prefix.rstrip('/')}/{key}".lstrip("/")
    try:
        client.put_object(
            Bucket=settings.aws_s3_bucket,
            Key=full_key,
            Body=body,
            ContentType=content_type or "application/octet-stream",
            **extra,
        )
    except ClientError as exc:
        raise RuntimeError(str(exc)) from exc
    return {"bucket": settings.aws_s3_bucket, "key": full_key}
