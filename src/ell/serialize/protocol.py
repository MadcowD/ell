from typing import Protocol, Optional, List, Dict, Any, runtime_checkable

from ell.types.serialize import GetLMPOutput, WriteLMPInput, WriteInvocationInput, LMP


@runtime_checkable
class EllSerializer(Protocol):
    supports_blobs: bool

    def get_lmp(self, lmp_id: str) -> GetLMPOutput:
        ...

    def write_lmp(self, lmp: WriteLMPInput, uses: List[str]) -> None:
        ...

    def write_invocation(self, input: WriteInvocationInput) -> None:
        ...

    def store_blob(self, blob_id: str, blob: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        ...

    def retrieve_blob(self, blob_id: str) -> bytes:
        ...

    def close(self):
        ...

    def get_lmp_versions(self, fqn: str) -> List[LMP]:
        ...


@runtime_checkable
class EllAsyncSerializer(Protocol):
    supports_blobs: bool

    async def get_lmp(self, lmp_id: str) -> GetLMPOutput:
        ...

    async def write_lmp(self, lmp: WriteLMPInput, uses: List[str]) -> None:
        ...

    async def write_invocation(self, input: WriteInvocationInput) -> None:
        ...

    async def store_blob(self, blob_id: str, blob: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        ...

    async def retrieve_blob(self, blob_id: str) -> bytes:
        ...

    async def close(self):
        ...

    async def get_lmp_versions(self, fqn: str) -> List[LMP]:
        ...
