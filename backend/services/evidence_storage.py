"""Storage abstraction for screenshot evidence.

Without an S3 bucket configured, data remains inline for backwards-compatible local
development. Production can move large PNGs out of Mongo by setting EVIDENCE_S3_BUCKET.
"""
import asyncio
import base64
from typing import Optional

import boto3

from ..core.config import settings


def _client():
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        endpoint_url=settings.S3_ENDPOINT_URL,
    )


async def store_base64_png(data: Optional[str], key: str) -> Optional[str]:
    if not data:
        return None
    if not settings.EVIDENCE_S3_BUCKET:
        return data

    body = base64.b64decode(data)
    object_key = f"{settings.EVIDENCE_S3_PREFIX.strip('/')}/{key.lstrip('/')}"

    def upload():
        _client().put_object(
            Bucket=settings.EVIDENCE_S3_BUCKET,
            Key=object_key,
            Body=body,
            ContentType="image/png",
            ServerSideEncryption="AES256",
        )

    await asyncio.to_thread(upload)
    return f"s3://{settings.EVIDENCE_S3_BUCKET}/{object_key}"


async def load_png(reference: str) -> bytes:
    if reference.startswith("s3://"):
        bucket_and_key = reference[5:]
        bucket, key = bucket_and_key.split("/", 1)

        def download():
            return _client().get_object(Bucket=bucket, Key=key)["Body"].read()

        return await asyncio.to_thread(download)
    return base64.b64decode(reference)
