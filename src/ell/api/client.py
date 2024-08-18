import httpx
from typing import Dict, Any, Protocol, List
from ell.api.types import LMP, GetLMPResponse, WriteLMPInput, WriteInvocationInput
from ell.stores.sql import SQLiteStore
from ell.types import SerializedLMP


class EllClient(Protocol):
    async def get_lmp(self, lmp_id: str) -> GetLMPResponse:
        ...

    async def write_lmp(self, lmp: WriteLMPInput, uses: Dict[str, Any]) -> None:
        ...

    async def write_invocation(self, input: WriteInvocationInput) -> None:
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

    async def write_lmp(self, lmp: WriteLMPInput, uses: Dict[str, Any]) -> None:
        response = await self.client.post("/lmp", json={
            "lmp": lmp.model_dump(),
            "uses": uses
        })
        response.raise_for_status()

    async def write_invocation(self, input: WriteInvocationInput) -> None:
        response = await self.client.post("/invocation", json=input.model_dump())
        response.raise_for_status()
        return None

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

    async def write_lmp(self, lmp: WriteLMPInput, uses: Dict[str, Any]) -> None:
        serialized_lmp = SerializedLMP(**lmp.model_dump())
        self.store.write_lmp(serialized_lmp, uses)

    async def write_invocation(self, input: WriteInvocationInput) -> None:
        invocation, results, consumes = input.to_serialized_invocation_input()
        self.store.write_invocation(
            invocation,
            results,
            consumes  # type: ignore
        )
        return None

    async def close(self):
        # SQLiteStore doesn't have a close method, so this is a no-op
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
