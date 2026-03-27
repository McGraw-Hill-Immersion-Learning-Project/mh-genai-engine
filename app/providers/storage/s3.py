"""AWS S3 storage provider."""

from __future__ import annotations

import asyncio


class S3StorageProvider:
    """Read and write documents from/to an S3 bucket."""

    def __init__(self, bucket: str, region: str = "us-east-1") -> None:
        import boto3

        self._bucket = bucket
        self._client = boto3.client("s3", region_name=region)

    async def get(self, key: str) -> bytes:
        """Download a file from S3 and return its bytes."""
        def _get() -> bytes:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
            return response["Body"].read()

        return await asyncio.to_thread(_get)

    async def put(self, key: str, data: bytes) -> None:
        """Upload bytes to S3 under the given key."""
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=data,
        )

    async def list_files(self, prefix: str = "") -> list[str]:
        """List object keys in the bucket with an optional prefix filter."""
        def _list() -> list[str]:
            paginator = self._client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self._bucket, Prefix=prefix)
            keys: list[str] = []
            for page in pages:
                for obj in page.get("Contents", []):
                    keys.append(obj["Key"])
            return keys

        return await asyncio.to_thread(_list)

    async def delete(self, key: str) -> None:
        """Delete an object from S3."""
        await asyncio.to_thread(
            self._client.delete_object,
            Bucket=self._bucket,
            Key=key,
        )
