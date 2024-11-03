from typing import List, Optional, Dict, Any

from ell.api.client.abc import EllClient
from ell.stores.sql import PostgresStore
from ell.stores.studio import SerializedLMP
from ell.types.serialize import LMP, WriteLMPInput, WriteInvocationInput


# Nb: these are async clients. maybe we want separate sync ones?
class EllPostgresClient(EllClient):
    def __init__(self, db_uri: str):
        self.store = PostgresStore(db_uri)

    async def get_lmp(self, lmp_id: str):
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
        invocation, consumes = input.to_serialized_invocation_input()
        self.store.write_invocation(
            invocation,
            set(consumes)
        )
        return None

    async def store_blob(self, blob: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        if self.store.blob_store is None:
            raise ValueError("Blob store is not enabled")
        return self.store.blob_store.store_blob(blob, metadata)

    async def retrieve_blob(self, blob_id: str) -> bytes:
        if self.store.blob_store is None:
            raise ValueError("Blob store is not enabled")
        return self.store.blob_store.retrieve_blob(blob_id)

    async def close(self):
        # todo. Do we have a close method?
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self):
        await self.close()
