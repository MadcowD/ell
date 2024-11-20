from typing import List, Optional, Dict, Any

from ell.stores.store import Store
from ell.stores.studio import Invocation, SerializedLMP
from ell.types.serialize import LMP, WriteLMPInput, WriteInvocationInput
from ell.serialize.protocol import EllSerializer, EllAsyncSerializer


class SQLSerializer(EllSerializer):
    def __init__(self, store: Store):
        self.store = store
        self.supports_blobs = store.has_blob_storage

    def get_lmp(self, lmp_id: str):
        lmp = self.store.get_lmp(lmp_id)
        if lmp:
            return LMP(**lmp.model_dump())
        return None

    def get_lmp_versions(self, fqn: str) -> List[LMP]:
        slmps = self.store.get_versions_by_fqn(fqn)
        return [LMP(**slmp.model_dump()) for slmp in slmps]

    def write_lmp(self, lmp: WriteLMPInput) -> None:
        model = SerializedLMP.coerce(lmp)
        self.store.write_lmp(model, lmp.uses)

    def write_invocation(self, input: WriteInvocationInput) -> None:
        invocation = Invocation.coerce(input.invocation)
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


# todo(async): the underlying store and blob store is not async-aware
class AsyncSQLSerializer(EllAsyncSerializer):
    def __init__(self, store: Store):
        self.store = store
        self.supports_blobs = store.has_blob_storage

    async def get_lmp(self, lmp_id: str) -> Optional[LMP]:
        lmp = self.store.get_lmp(lmp_id)
        if lmp:
            return LMP(**lmp.model_dump())
        return None

    async def get_lmp_versions(self, fqn: str) -> List[LMP]:
        slmps = self.store.get_versions_by_fqn(fqn)
        return [LMP(**slmp.model_dump()) for slmp in slmps]

    async def write_lmp(self, lmp: WriteLMPInput) -> None:
        model = SerializedLMP.coerce(lmp)
        self.store.write_lmp(model, lmp.uses)

    async def write_invocation(self, input: WriteInvocationInput) -> None:
        invocation = Invocation.coerce(input.invocation)
        self.store.write_invocation(
            invocation,
            set(input.consumes)
        )
        return None

    async def store_blob(self, blob_id: str, blob: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        if self.store.blob_store is None:
            raise ValueError("Blob store is not enabled")
        return self.store.blob_store.store_blob(blob=blob, blob_id=blob_id)

    async def retrieve_blob(self, blob_id: str) -> bytes:
        if self.store.blob_store is None:
            raise ValueError("Blob store is not enabled")
        return self.store.blob_store.retrieve_blob(blob_id)

    async def close(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self):
        await self.close()
