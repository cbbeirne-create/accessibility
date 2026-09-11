"""Optional object storage for scan screenshots with a development fallback."""
import base64
import io
import uuid
from typing import Optional

import boto3

from ..core.config import settings


def _client():
    if not settings.S3_BUCKET:
        return None
    return boto3.client('s3', region_name=settings.S3_REGION, endpoint_url=settings.S3_ENDPOINT_URL)


def store_png_base64(data: Optional[str], prefix: str) -> dict:
    if not data:
        return {'base64': None, 'key': None, 'url': None}
    client = _client()
    if not client:
        return {'base64': data, 'key': None, 'url': None}
    key = f"scan-evidence/{prefix}/{uuid.uuid4().hex}.png"
    client.upload_fileobj(io.BytesIO(base64.b64decode(data)), settings.S3_BUCKET, key, ExtraArgs={'ContentType': 'image/png'})
    url = f"{settings.S3_PUBLIC_BASE_URL.rstrip('/')}/{key}" if settings.S3_PUBLIC_BASE_URL else None
    return {'base64': None, 'key': key, 'url': url}


def load_png_bytes(*, base64_data: Optional[str], key: Optional[str]) -> Optional[bytes]:
    if base64_data:
        return base64.b64decode(base64_data)
    client = _client()
    if client and key:
        response = client.get_object(Bucket=settings.S3_BUCKET, Key=key)
        return response['Body'].read()
    return None
