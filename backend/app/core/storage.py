"""File storage helpers for resumes and uploads."""

from __future__ import annotations

import io
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", filename or "resume.pdf")
    return cleaned[:120] or "resume.pdf"


def _store_local(user_id: str, filename: str, content: bytes) -> str:
    backend_dir = Path(__file__).resolve().parents[2]
    target_dir = backend_dir / "data" / "resumes" / user_id
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = target_dir / f"{timestamp}_{_safe_filename(filename)}"
    target.write_bytes(content)
    return str(target)


def store_resume_pdf(user_id: str, filename: str, content: bytes) -> str:
    """Persist resume bytes to MinIO/S3-compatible storage with local fallback."""
    safe_name = _safe_filename(filename)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    object_key = f"resumes/{user_id}/{timestamp}_{safe_name}"

    if settings.STORAGE_BACKEND.lower() == "minio":
        secure = settings.MINIO_ENDPOINT.startswith("https://")
        endpoint = settings.MINIO_ENDPOINT.replace("https://", "").replace(
            "http://", ""
        )
        client = Minio(
            endpoint,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=secure,
        )

        try:
            if not client.bucket_exists(settings.MINIO_BUCKET_RESUMES):
                client.make_bucket(settings.MINIO_BUCKET_RESUMES)
            client.put_object(
                settings.MINIO_BUCKET_RESUMES,
                object_key,
                io.BytesIO(content),
                length=len(content),
                content_type="application/pdf",
            )
            return f"s3://{settings.MINIO_BUCKET_RESUMES}/{object_key}"
        except S3Error:
            logger.warning("Failed to upload resume to MinIO, storing locally instead")
        except Exception:
            logger.warning(
                "Unexpected storage error, storing resume locally", exc_info=True
            )

    return _store_local(user_id=user_id, filename=safe_name, content=content)
