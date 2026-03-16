"""Crée les buckets MinIO (bronze/silver/gold) au démarrage."""

import os
from minio import Minio

endpoint = os.environ.get("MINIO_ENDPOINT", "minio:9000")
access_key = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
secret_key = os.environ.get("MINIO_SECRET_KEY", "minioadmin123")

client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)

for bucket in ("bronze", "silver", "gold"):
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        print(f"Bucket '{bucket}' créé.")
    else:
        print(f"Bucket '{bucket}' existe déjà.")
