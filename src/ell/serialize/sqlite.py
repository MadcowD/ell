from typing import List, Optional, Dict, Any

from ell.serialize.protocol import EllSerializer, EllAsyncSerializer
from ell.stores.sql import SQLiteStore
from ell.stores.store import AsyncBlobStore, BlobStore
from ell.stores.studio import SerializedLMP, Invocation
from ell.types.serialize import WriteLMPInput, WriteInvocationInput, LMP



class SQLiteSerializer(EllSerializer):
    def __init__(self, storage_dir: str, blob_store: Optional[BlobStore] = None):
        self.store = SQLiteStore(storage_dir, blob_store)
        self.supports_blobs = True

    def get_lmp(self, lmp_id: str):
        lmp = self.store.get_lmp(lmp_id)
        if lmp:
            return LMP(**lmp.model_dump())
        return None

    def get_lmp_versions(self, fqn: str) -> List[LMP]:
        slmps = self.store.get_versions_by_fqn(fqn)
        return [LMP(**slmp.model_dump()) for slmp in slmps]

    def write_lmp(self, lmp: WriteLMPInput, uses: List[str]) -> None:
        serialized_lmp = SerializedLMP.from_api(lmp)
        self.store.write_lmp(serialized_lmp, uses)

    def write_invocation(self, input: WriteInvocationInput) -> None:
        invocation = Invocation.from_api(input.invocation)
        self.store.write_invocation(invocation, set(input.consumes))
        return None

    def store_blob(self, blob_id: str, blob: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        return self.store.blob_store.store_blob(blob, blob_id) # type: ignore

    def retrieve_blob(self, blob_id: str) -> bytes:
        return self.store.blob_store.retrieve_blob(blob_id) # type: ignore

    def close(self):
        pass



# todo(async). underlying store is not async-aware
class AsyncSQLiteSerializer(EllAsyncSerializer):
    def __init__(self, storage_dir: str, blob_store: Optional[AsyncBlobStore] = None):
        self.store = SQLiteStore(storage_dir, blob_store)
        self.blob_store = blob_store
        self.supports_blobs = True

    async def get_lmp(self, lmp_id: str):
        lmp = self.store.get_lmp(lmp_id)
        if lmp:
            return LMP(**lmp.model_dump())
        return None

    async def get_lmp_versions(self, fqn: str) -> List[LMP]:
        slmps = self.store.get_versions_by_fqn(fqn)
        return [LMP(**slmp.model_dump()) for slmp in slmps]

    async def write_lmp(self, lmp: WriteLMPInput, uses: List[str]) -> None:
        serialized_lmp = SerializedLMP.from_api(lmp)
        self.store.write_lmp(serialized_lmp, uses)

    async def write_invocation(self, input: WriteInvocationInput) -> None:
        invocation = Invocation.from_api(input.invocation)
        self.store.write_invocation(invocation, set(input.consumes))
        return None

    async def store_blob(self, blob_id: str, blob: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        return await self.blob_store.store_blob(blob, blob_id) # type: ignore

    async def retrieve_blob(self, blob_id: str) -> bytes:
        return await self.blob_store.retrieve_blob(blob_id) # type: ignore

    async def close(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self):
        await self.close()

