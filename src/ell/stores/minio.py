import io

from pydantic import BaseModel, Field
import ell.stores.store

import minio


class MinioConfig(BaseModel):
    endpoint: str = Field(description="The endpoint of the minio server")
    access_key: str = Field(description="The access key of the minio server")
    secret_key: str = Field(description="The secret key of the minio server")
    bucket: str = Field(description="The bucket to store the blobs in")


class MinioBlobStore(ell.stores.store.BlobStore):
    def __init__(self, config: MinioConfig):
        self.config = config
        self.client = minio.Minio(
            #todo. support tls with dev vs prod
            secure=False,#False if config.endpoint.startswith("localhost") else True,
            endpoint=config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key)

    def store_blob(self, blob: bytes, blob_id: str, **kwargs):
        self.client.put_object(
            bucket_name=self.config.bucket,
            object_name=blob_id,
            data=io.BytesIO(blob),
            length=len(blob)
        )
        return blob_id

    def retrieve_blob(self, blob_id: str) -> bytes:
        return self.client.get_object(self.config.bucket, blob_id).read()

# todo. make this actually async
class AsyncMinioBlobStore(ell.stores.store.AsyncBlobStore):
    def __init__(self, config: MinioConfig):
        self.config = config
        self.client = minio.Minio(
            config.endpoint, config.access_key, config.secret_key)

    async def store_blob(self, blob: bytes, blob_id: str, **kwargs):
        self.client.put_object(
            bucket_name=self.config.bucket,
            object_name=blob_id,
            data=io.BytesIO(blob),
            length=len(blob)
        )
        return blob_id

    async def retrieve_blob(self, blob_id: str) -> bytes:
        return self.client.get_object(self.config.bucket, blob_id).read()
