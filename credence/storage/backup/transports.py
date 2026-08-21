"""Multi-Backend Cloud Storage Transports for GCS, S3/MinIO & Local Filesystem."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from credence.config import settings

logger = logging.getLogger("credence.storage.backup.transports")


async def upload_to_cloud_storage(
    local_file: Path,
    manifest_file: Optional[Path],
    bucket_name: str,
    storage_backend: str,
) -> Optional[str]:
    """Upload compressed backup archive and manifest to GCS or S3."""
    remote_name = local_file.name
    manifest_name = manifest_file.name if manifest_file else None

    if (
        storage_backend == "gcs"
        or bucket_name.startswith("gs://")
        or "nexus" in bucket_name
        or "credence" in bucket_name
    ):
        clean_bucket = bucket_name.replace("gs://", "").strip("/")
        cloud_uri = f"gs://{clean_bucket}/backups/{remote_name}"
        try:
            from google.cloud import storage as gcs_storage  # type: ignore[import-not-found]

            client = gcs_storage.Client()
            bucket = client.bucket(clean_bucket)
            blob = bucket.blob(f"backups/{remote_name}")
            blob.upload_from_filename(str(local_file))

            if manifest_file and manifest_file.exists():
                m_blob = bucket.blob(f"backups/{manifest_name}")
                m_blob.upload_from_filename(str(manifest_file))

            logger.info("Successfully uploaded backup to GCS: %s", cloud_uri)
            return cloud_uri
        except ImportError:
            logger.debug("google-cloud-storage not installed; trying fallback")
        except Exception as ge:
            logger.warning("GCS direct client upload failed: %s", ge)

    if storage_backend == "s3" or settings.STORAGE_BACKEND == "s3":
        try:
            from credence.storage.s3 import S3BlobStorage

            bucket_name = bucket_name or settings.S3_BUCKET_NAME or "credence-backups"
            s3 = S3BlobStorage(
                bucket_name=bucket_name,
                endpoint_url=settings.S3_ENDPOINT_URL,
                access_key_id=settings.S3_ACCESS_KEY_ID,
                secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            )
            key = f"backups/{remote_name}"
            data = local_file.read_bytes()
            uri = await s3.put_blob(key, data, content_type="application/gzip")
            if manifest_file and manifest_file.exists():
                await s3.put_blob(
                    f"backups/{manifest_name}", manifest_file.read_bytes(), content_type="application/json"
                )
            logger.info("Successfully uploaded backup to S3: %s", uri)
            return uri
        except Exception as se:
            logger.warning("S3 blob upload failed: %s", se)

    return None


async def download_from_cloud_storage(
    bucket_name: str,
    remote_filename: str,
    target_local_path: Path,
    storage_backend: str,
) -> bool:
    """Download backup archive from GCS or S3."""
    if (
        storage_backend == "gcs"
        or bucket_name.startswith("gs://")
        or "nexus" in bucket_name
        or "credence" in bucket_name
    ):
        clean_bucket = bucket_name.replace("gs://", "").strip("/")
        try:
            from google.cloud import storage as gcs_storage  # type: ignore[import-not-found]

            client = gcs_storage.Client()
            bucket = client.bucket(clean_bucket)
            blob = bucket.blob(f"backups/{remote_filename}")
            if not blob.exists():
                logger.info("No cloud backup found at gs://%s/backups/%s", clean_bucket, remote_filename)
                return False

            target_local_path.parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(str(target_local_path))
            logger.info("Successfully downloaded backup from gs://%s/backups/%s", clean_bucket, remote_filename)
            return True
        except ImportError:
            logger.debug("google-cloud-storage not installed for download")
        except Exception as ge:
            logger.warning("GCS download failed: %s", ge)

    if storage_backend == "s3" or settings.STORAGE_BACKEND == "s3":
        try:
            from credence.storage.s3 import S3BlobStorage

            bucket_name = bucket_name or settings.S3_BUCKET_NAME or "credence-backups"
            s3 = S3BlobStorage(
                bucket_name=bucket_name,
                endpoint_url=settings.S3_ENDPOINT_URL,
                access_key_id=settings.S3_ACCESS_KEY_ID,
                secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            )
            key = f"backups/{remote_filename}"
            blob_bytes = await s3.get_blob(key)
            if blob_bytes:
                target_local_path.parent.mkdir(parents=True, exist_ok=True)
                target_local_path.write_bytes(blob_bytes)
                logger.info("Successfully downloaded backup from S3: %s", key)
                return True
        except Exception as se:
            logger.warning("S3 download failed: %s", se)

    return False
