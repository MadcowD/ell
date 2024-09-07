import httpx
from typing import Any, Dict, Optional, Protocol, List
from ell.api.types import LMP, GetLMPResponse, WriteLMPInput, WriteInvocationInput
from ell.stores.sql import SQLiteStore
from ell.types import SerializedLMP


class EllClient(Protocol):
    async def get_lmp(self, lmp_id: str) -> GetLMPResponse:
        ...

    async def write_lmp(self, lmp: WriteLMPInput, uses: List[str]) -> None:
        ...

    async def write_invocation(self, input: WriteInvocationInput) -> None:
        ...

    async def store_blob(self, blob: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        ...

    async def retrieve_blob(self, blob_id: str) -> bytes:
        ...

    async def close(self):
        ...

    async def get_lmp_versions(self, fqn: str) -> List[LMP]:
        ...


class EllAPIClient(EllClient):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)

    async def get_lmp(self, lmp_id: str) -> GetLMPResponse:
        response = await self.client.get(f"/lmp/{lmp_id}")
        response.raise_for_status()
        data = response.json()
        if data is None:
            return None
        return LMP(**data)

    async def write_lmp(self, lmp: WriteLMPInput, uses: List[str]) -> None:
        response = await self.client.post("/lmp", json={
            "lmp": lmp.model_dump(mode="json"),
            "uses": uses
        })
        response.raise_for_status()

    async def write_invocation(self, input: WriteInvocationInput) -> None:
        response = await self.client.post(
            "/invocation",
            json=input.model_dump(mode="json")
        )
        response.raise_for_status()
        return None

    async def store_blob(self, blob: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        response = await self.client.post("/blob", data={
            "blob": blob,
            "metadata": metadata
        })
        response.raise_for_status()
        return response.json()["blob_id"]

    async def retrieve_blob(self, blob_id: str) -> bytes:
        response = await self.client.get(f"/blob/{blob_id}")
        response.raise_for_status()
        return response.content

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self):
        await self.close()

    async def get_lmp_versions(self, fqn: str) -> List[LMP]:
        response = await self.client.get("/lmp/versions", params={"fqn": fqn})
        response.raise_for_status()
        data = response.json()
        return [LMP(**lmp_data) for lmp_data in data]


class EllSqliteClient(EllClient):
    def __init__(self, storage_dir: str):
        self.store = SQLiteStore(storage_dir)

    async def get_lmp(self, lmp_id: str):
        lmp = self.store.get_lmp(lmp_id)
        if lmp:
            return LMP(**lmp.model_dump())
        return None

    async def get_lmp_versions(self, fqn: str) -> List[LMP]:
        slmps = self.store.get_versions_by_fqn(fqn)
        return [LMP(**slmp.model_dump()) for slmp in slmps]

    async def write_lmp(self, lmp: WriteLMPInput, uses: List[str]) -> None:
        serialized_lmp = SerializedLMP(**lmp.model_dump())
        self.store.write_lmp(serialized_lmp, uses)

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
        # SQLiteStore doesn't have a close method, so this is a no-op
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self):
        await self.close()
