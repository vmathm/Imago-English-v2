from google.cloud import storage
from flask import current_app
from urllib.parse import urlparse
import uuid

def upload_file_to_gcs(file_obj, *, prefix: str, content_type: str) -> str:
    client = storage.Client()

    bucket_name = current_app.config.get("GCS_AUDIOBOOK_BUCKET")
    if not bucket_name:
        raise RuntimeError("GCS_AUDIOBOOK_BUCKET is not configured.")

    bucket = client.bucket(bucket_name)

    unique_suffix = uuid.uuid4().hex
    blob_name = f"{prefix}-{unique_suffix}"

    blob = bucket.blob(blob_name)
    blob.upload_from_file(file_obj, content_type=content_type)

    # Bucket itself is public; no make_public() here
    return f"https://storage.googleapis.com/{bucket_name}/{blob_name}"


def _blob_name_from_url(url: str, bucket_name: str) -> str:
    """
    Given a GCS URL, extract the blob name inside the given bucket.

    Handles URLs like:
    - https://storage.googleapis.com/<bucket>/<blob_name>
    - https://<bucket>.storage.googleapis.com/<blob_name>
    """
    parsed = urlparse(url)
    path = parsed.path.lstrip("/")  # e.g. "<bucket>/user_123/file-uuid" OR "user_123/file-uuid"

    # Case 1: storage.googleapis.com/<bucket>/<blob_name>
    if path.startswith(bucket_name + "/"):
        return path[len(bucket_name) + 1 :]

    # Case 2: <bucket>.storage.googleapis.com/<blob_name>
    if parsed.netloc.startswith(bucket_name + "."):
        return path

    # If it doesn't match expected patterns, don't try to delete
    raise ValueError(f"URL does not match expected bucket format: {url}")


def delete_file_from_gcs_by_url(url: str) -> None:
    """
    Delete a GCS object given its URL, if it belongs to the configured audiobook bucket.
    Silently ignores NotFound errors.
    """
    if not url:
        return

    client = storage.Client()
    bucket_name = current_app.config.get("GCS_AUDIOBOOK_BUCKET")
    if not bucket_name:
        raise RuntimeError("GCS_AUDIOBOOK_BUCKET is not configured.")

    try:
        blob_name = _blob_name_from_url(url, bucket_name)
    except ValueError:
        # URL doesn't belong to this bucket / unexpected pattern: skip
        current_app.logger.warning(f"Skipping delete for non-matching URL: {url}")
        return

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    try:
        blob.delete()
        current_app.logger.info(f"Deleted old audiobook blob: {bucket_name}/{blob_name}")
    except Exception as exc:
        # Don't crash the request if deletion fails
        current_app.logger.warning(f"Failed to delete blob {bucket_name}/{blob_name}: {exc}")
