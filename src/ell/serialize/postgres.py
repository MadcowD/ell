from typing import List, Optional, Dict, Any

from ell.stores.sql import PostgresStore
from ell.stores.store import BlobStore, AsyncBlobStore
from ell.stores.studio import Invocation, SerializedLMP
from ell.types.serialize import LMP, WriteLMPInput, WriteInvocationInput
from ell.serialize.protocol import EllSerializer, EllAsyncSerializer


class PostgresSerializer(EllSerializer):
    def __init__(self, db_uri: str, blob_store: Optional[BlobStore] = None):
        self.store = PostgresStore(db_uri, blob_store)
        self.supports_blobs = blob_store is not None

    def get_lmp(self, lmp_id: str):
        lmp = self.store.get_lmp(lmp_id)
        if lmp:
            return LMP(**lmp.model_dump())
        return None

    def get_lmp_versions(self, fqn: str) -> List[LMP]:
        slmps = self.store.get_versions_by_fqn(fqn)
        return [LMP(**slmp.model_dump()) for slmp in slmps]

    def write_lmp(self, lmp: WriteLMPInput, uses: List[str]) -> None:
        model = SerializedLMP.from_api(lmp)
        self.store.write_lmp(model, uses)

    def write_invocation(self, input: WriteInvocationInput) -> None:
        invocation = Invocation.from_api(input.invocation)
        self.store.write_invocation(invocation, set(input.consumes))
        return None

    def store_blob(self, blob_id: str, blob: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        if self.store.blob_store is None:
            raise ValueError("Blob store is not enabled")
        return self.store.blob_store.store_blob(blob=blob, blob_id=blob_id)

    def retrieve_blob(self, blob_id: str) -> bytes:
        if self.store.blob_store is None:
            raise ValueError("Blob store is not enabled")
        return self.store.blob_store.retrieve_blob(blob_id)

    def close(self):
        pass


# todo(async): the underlying store is not async-aware
class AsyncPostgresSerializer(EllAsyncSerializer):
    def __init__(self, db_uri: str, blob_store: Optional[AsyncBlobStore] = None):
        self.store = PostgresStore(db_uri, blob_store)
        self.blob_store = blob_store
        self.supports_blobs = blob_store is not None

    async def get_lmp(self, lmp_id: str) -> Optional[LMP]:
        lmp = self.store.get_lmp(lmp_id)
        if lmp:
            return LMP(**lmp.model_dump())
        return None

    async def get_lmp_versions(self, fqn: str) -> List[LMP]:
        slmps = self.store.get_versions_by_fqn(fqn)
        return [LMP(**slmp.model_dump()) for slmp in slmps]

    async def write_lmp(self, lmp: WriteLMPInput, uses: List[str]) -> None:
        model = SerializedLMP.from_api(lmp)
        self.store.write_lmp(model, uses)

    async def write_invocation(self, input: WriteInvocationInput) -> None:
        invocation = Invocation.from_api(input.invocation)
        self.store.write_invocation(
            invocation,
            set(input.consumes)
        )
        return None

    async def store_blob(self, blob_id: str, blob: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        if self.blob_store is None:
            raise ValueError("Blob store is not enabled")
        return await self.blob_store.store_blob(blob=blob, blob_id=blob_id)

    async def retrieve_blob(self, blob_id: str) -> bytes:
        if self.blob_store is None:
            raise ValueError("Blob store is not enabled")
        return await self.blob_store.retrieve_blob(blob_id)

    async def close(self):
        # todo. Do we have a close method?
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self):
        await self.close()
