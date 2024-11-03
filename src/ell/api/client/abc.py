from typing import Any, Dict, Optional, Protocol, List
# todo. check this does not cause circularity
from ell.types.serialize import LMP, GetLMPResponse, WriteLMPInput, WriteInvocationInput


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



