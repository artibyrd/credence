"""Multi-Backend Cloud Storage Transports for GCS, S3/MinIO & Local Filesystem."""

from __future__ import annotations

import asyncio
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

        def _sync_gcs_upload() -> Optional[str]:
            try:
                from google.cloud import storage as gcs_storage  # type: ignore[import-not-found]

                client = gcs_storage.Client()
                bucket = client.bucket(clean_bucket)

                # 1. Upload timestamped snapshot
                blob = bucket.blob(f"backups/{remote_name}")
                blob.upload_from_filename(str(local_file))

                if manifest_file and manifest_file.exists():
                    m_blob = bucket.blob(f"backups/{manifest_name}")
                    m_blob.upload_from_filename(str(manifest_file))

                # 2. Upload latest pointer copies
                latest_gz = local_file.parent / "credence_latest.db.gz"
                if latest_gz.exists():
                    l_blob = bucket.blob("backups/credence_latest.db.gz")
                    l_blob.upload_from_filename(str(latest_gz))

                latest_manifest = latest_gz.with_suffix(".manifest.json")
                if latest_manifest.exists():
                    lm_blob = bucket.blob(f"backups/{latest_manifest.name}")
                    lm_blob.upload_from_filename(str(latest_manifest))

                logger.info("Successfully uploaded backup and latest pointer to GCS: %s", cloud_uri)
                return cloud_uri
            except ImportError:
                logger.debug("google-cloud-storage not installed; skipping GCS upload")
                return None
            except Exception as ge:
                logger.warning("GCS direct client upload failed: %s", ge)
                return None

        return await asyncio.to_thread(_sync_gcs_upload)

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

            # Upload latest pointers to S3
            latest_gz = local_file.parent / "credence_latest.db.gz"
            if latest_gz.exists():
                await s3.put_blob(
                    "backups/credence_latest.db.gz", latest_gz.read_bytes(), content_type="application/gzip"
                )
            latest_manifest = latest_gz.with_suffix(".manifest.json")
            if latest_manifest.exists():
                await s3.put_blob(
                    f"backups/{latest_manifest.name}",
                    latest_manifest.read_bytes(),
                    content_type="application/json",
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

        def _sync_gcs_download() -> bool:
            try:
                from google.cloud import storage as gcs_storage  # type: ignore[import-not-found]

                client = gcs_storage.Client()
                bucket = client.bucket(clean_bucket)
                blob = bucket.blob(f"backups/{remote_filename}")

                if not blob.exists():
                    logger.info(
                        "File gs://%s/backups/%s not found; scanning for newest backup snapshot...",
                        clean_bucket,
                        remote_filename,
                    )
                    blobs = list(client.list_blobs(clean_bucket, prefix="backups/credence_"))
                    gz_blobs = [b for b in blobs if b.name.endswith(".db.gz")]
                    if not gz_blobs:
                        logger.info("No backup snapshots found in gs://%s/backups/", clean_bucket)
                        return False
                    gz_blobs.sort(key=lambda b: b.updated or b.time_created or 0, reverse=True)
                    blob = gz_blobs[0]
                    logger.info("Found newest timestamped cloud backup: gs://%s/%s", clean_bucket, blob.name)

                target_local_path.parent.mkdir(parents=True, exist_ok=True)
                blob.download_to_filename(str(target_local_path))
                logger.info("Successfully downloaded backup from gs://%s/%s", clean_bucket, blob.name)
                return True
            except ImportError:
                logger.debug("google-cloud-storage not installed for download")
                return False
            except Exception as ge:
                logger.warning("GCS download failed: %s", ge)
                return False

        return await asyncio.to_thread(_sync_gcs_download)

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
