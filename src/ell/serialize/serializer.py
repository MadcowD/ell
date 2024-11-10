from typing import Optional

from ell.serialize.protocol import EllSerializer, EllAsyncSerializer
from ell.stores.store import AsyncBlobStore, BlobStore
from ell.serialize.config import SerializeConfig
from ell.util.errors import missing_ell_extras



def get_blob_store(config: SerializeConfig) -> Optional[BlobStore]:
    if config.minio_endpoint is not None:
        try:
            from ell.stores.minio import MinioBlobStore, MinioConfig
            minio_config = MinioConfig(
                endpoint=config.minio_endpoint,
                access_key=config.minio_access_key, # type: ignore
                secret_key=config.minio_secret_key, # type: ignore
                bucket=config.minio_bucket # type: ignore
            )
            return MinioBlobStore(minio_config)
        except ImportError:
            raise missing_ell_extras(message="MinIO storage is not enabled.", extras=["minio"])
    return None


def get_serializer(config: SerializeConfig) -> EllSerializer:
    blob_store = get_blob_store(config)
    if config.pg_connection_string:
        try:
            from ell.serialize.postgres import PostgresSerializer
            return PostgresSerializer(config.pg_connection_string, blob_store) # type: ignore
        except ImportError:
            raise missing_ell_extras(message="Postgres storage is not enabled.", extras=["postgres"])
    if config.storage_dir:
        try:
            from ell.serialize.sqlite import SQLiteSerializer
            return SQLiteSerializer(config.storage_dir, blob_store)
        except ImportError:
            raise missing_ell_extras(message="SQLite storage is not enabled.", extras=["sqlite"])
    raise ValueError("No storage configuration found.")


def get_async_blob_store(config: SerializeConfig) -> Optional[AsyncBlobStore]:
    if config.minio_endpoint is not None:
        try:
            from ell.stores.minio import AsyncMinioBlobStore, MinioConfig
            minio_config = MinioConfig(
                endpoint=config.minio_endpoint,
                access_key=config.minio_access_key, # type: ignore
                secret_key=config.minio_secret_key, # type: ignore
                bucket=config.minio_bucket # type: ignore
            )
            return AsyncMinioBlobStore(minio_config)
        except ImportError:
            raise missing_ell_extras(message="MinIO storage is not enabled.", extras=["minio"])
    return None


def get_async_serializer(config: SerializeConfig) -> EllAsyncSerializer:
    blob_store = get_async_blob_store(config)
    if config.pg_connection_string:
        try:
            from ell.serialize.postgres import AsyncPostgresSerializer
            return AsyncPostgresSerializer(config.pg_connection_string, blob_store)
        except ImportError:
            raise missing_ell_extras(message="Postgres storage is not enabled.", extras=["postgres"])
    if config.storage_dir:
        try:
            from ell.serialize.sqlite import AsyncSQLiteSerializer
            return AsyncSQLiteSerializer(config.storage_dir, blob_store)
        except ImportError:
            raise missing_ell_extras(message="SQLite storage is not enabled.", extras=["sqlite"])
    raise ValueError("No storage configuration found.")
