import logging
from typing import List, Optional, Dict, Any

import httpx
from httpx import HTTPStatusError

from ell.serialize.protocol import EllAsyncSerializer, EllSerializer
from ell.types.serialize import GetLMPOutput, WriteLMPInput, LMP, WriteInvocationInput


# tood. make sure we don't lose any information or end up with malformed stuff relative to what
# the sto4res have been doing for serialization (this function)
# this should probably just be handled by the serialization types to centralize serialization code in one place
# def to_json(obj):
#     """Serializes ell objects to json for writing to the database or wire protocols"""
#     return json.dumps(
#         pydantic_ltype_aware_cattr.unstructure(obj),
#         sort_keys=True, default=repr, ensure_ascii=False)


class EllHTTPSerializer(EllSerializer):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url)
        self.supports_blobs = True  # we assume the server does, if not will find out later
        self.logger = logging.getLogger(
            __name__).getChild(self.__class__.__name__)

    def _handle_http_error(
            self,
            error: HTTPStatusError,
            span: str,
            message: Optional[str] = None,
            extra: Optional[Dict[str, Any]] = None
    ) -> None:
        if error.response.status_code == 422:
            error_detail = error.response.json().get(
                "detail", "No detailed error message provided")
            self.logger.error(
                message or f"HTTP {error.response.status_code} Error in {span}",
                extra={
                    **(extra or {}),
                    "status_code": error.response.status_code,
                    "error_detail": error_detail,
                    "span": span,
                    "url": str(error.response.url),
                    "request_id": error.response.headers.get("x-request-id"),
                }
            )
            raise ValueError(f"Invalid input: {error_detail}") from error
        raise

    def get_lmp(self, lmp_id: str) -> GetLMPOutput:
        try:
            response = self.client.get(f"/lmp/{lmp_id}")
            response.raise_for_status()
            data = response.json()
            return None if data is None else LMP(**data)
        except HTTPStatusError as e:
            self._handle_http_error(e, "get_lmp")
            raise

    def write_lmp(self, lmp: WriteLMPInput, uses: List[str]) -> None:
        try:
            response = self.client.post("/lmp", json={
                # todo. restructure so model_dump_json
                # todo. because pydantic doesn't have a sane default for this we should consider a single place to specify exclude_none, exclude_unset like we had with unstructure for basemodel...
                "lmp": lmp.model_dump(mode='json', exclude_none=True, exclude_unset=True),
                "uses": uses
            })
            response.raise_for_status()
        except HTTPStatusError as e:
            self._handle_http_error(
                error=e,
                span="write_lmp",
                message="Failed to write LMP",
                extra={'lmp_id': lmp.lmp_id, 'lmp_version': lmp.version_number}
            )
            raise

    def write_invocation(self, input: WriteInvocationInput) -> None:
        try:
            response = self.client.post(
                url="/invocation",
                headers={"Content-Type": "application/json"},
                content=input.model_dump_json(exclude_none=True, exclude_unset=True),
            )
            response.raise_for_status()
            return None
        except HTTPStatusError as e:
            self._handle_http_error(
                error=e,
                span="write_invocation",
                message="Failed to write invocation",
                extra={'invocation_id': input.invocation.id}
            )
            raise

    def store_blob(self, blob_id: str, blob: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        try:
            response = self.client.post("/blob", data={
                "blob_id": blob_id,
                "blob": blob,
                "metadata": metadata
            })
            response.raise_for_status()
            return response.json()["blob_id"]
        except HTTPStatusError as e:
            self._handle_http_error(
                error=e,
                span="store_blob",
                message="Failed to store blob",
                extra={'blob_id': blob_id}
            )
            raise

    def retrieve_blob(self, blob_id: str) -> bytes:
        try:
            response = self.client.get(f"/blob/{blob_id}")
            response.raise_for_status()
            return response.content
        except HTTPStatusError as e:
            self._handle_http_error(
                error=e,
                span="retrieve_blob",
                message="Failed to retrieve blob",
                extra={'blob_id': blob_id}
            )
            raise

    def close(self):
        self.client.close()

    def get_lmp_versions(self, fqn: str) -> List[LMP]:
        try:
            response = self.client.get("/lmp/versions", params={"fqn": fqn})
            response.raise_for_status()
            data = response.json()
            return [LMP(**lmp_data) for lmp_data in data]
        except HTTPStatusError as e:
            self._handle_http_error(
                error=e,
                span="get_lmp_versions",
                message="Failed to get LMP versions",
                extra={'fqn': fqn}
            )
            raise


class EllAsyncHTTPSerializer(EllAsyncSerializer):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
        self.supports_blobs = True  # we assume the server does, if not will find out later
        self.logger = logging.getLogger(
            __name__).getChild(self.__class__.__name__)

    def _handle_http_error(
            self,
            error: HTTPStatusError,
            span: str,
            message: Optional[str] = None,
            extra: Optional[Dict[str, Any]] = None
    ) -> None:
        if error.response.status_code == 422:
            error_detail = error.response.json().get(
                "detail", "No detailed error message provided")
            self.logger.error(
                message or f"HTTP {error.response.status_code} Error in {span}",
                extra={
                    **(extra or {}),
                    "status_code": error.response.status_code,
                    "error_detail": error_detail,
                    "span": span,
                    "url": str(error.response.url),
                    "request_id": error.response.headers.get("x-request-id"),
                }
            )
            raise ValueError(f"Invalid input: {error_detail}") from error
        raise

    async def get_lmp(self, lmp_id: str) -> GetLMPOutput:
        try:
            response = await self.client.get(f"/lmp/{lmp_id}")
            response.raise_for_status()
            data = response.json()
            if data is None:
                return None
            return LMP(**data)
        except HTTPStatusError as e:
            self._handle_http_error(
                error=e,
                span="get_lmp",
                message="Failed to get LMP",
                extra={'lmp_id': lmp_id}
            )
            raise

    async def write_lmp(self, lmp: WriteLMPInput, uses: List[str]) -> None:
        try:
            response = await self.client.post("/lmp", json={
                "lmp": lmp.model_dump(mode="json", exclude_none=True, exclude_unset=True),
                "uses": uses
            })
            response.raise_for_status()
        except HTTPStatusError as e:
            self._handle_http_error(
                error=e,
                span="write_lmp",
                message="Failed to write LMP",
                extra={'lmp_id': lmp.lmp_id, 'lmp_version': lmp.version_number}
            )
            raise

    async def write_invocation(self, input: WriteInvocationInput) -> None:
        try:
            response = await self.client.post(
                "/invocation",
                headers={"Content-Type": "application/json"},
                content=input.model_dump_json(exclude_none=True, exclude_unset=True),
            )
            response.raise_for_status()
            return None
        except HTTPStatusError as e:
            self._handle_http_error(
                error=e,
                span="write_invocation",
                message="Failed to write invocation",
                extra={'invocation_id': input.invocation.id}
            )
            raise

    async def store_blob(self, blob_id: str, blob: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        try:
            response = await self.client.post("/blob", data={
                "blob_id": blob_id,
                "blob": blob,
                "metadata": metadata
            })
            response.raise_for_status()
            return response.json()["blob_id"]
        except HTTPStatusError as e:
            self._handle_http_error(
                error=e,
                span="store_blob",
                message="Failed to store blob",
                extra={'blob_id': blob_id}
            )
            raise

    async def retrieve_blob(self, blob_id: str) -> bytes:
        try:
            response = await self.client.get(f"/blob/{blob_id}")
            response.raise_for_status()
            return response.content
        except HTTPStatusError as e:
            self._handle_http_error(
                error=e,
                span="retrieve_blob",
                message="Failed to retrieve blob",
                extra={'blob_id': blob_id}
            )
            raise

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self):
        await self.close()

    async def get_lmp_versions(self, fqn: str) -> List[LMP]:
        try:
            response = await self.client.get("/lmp/versions", params={"fqn": fqn})
            response.raise_for_status()
            data = response.json()
            return [LMP(**lmp_data) for lmp_data in data]
        except HTTPStatusError as e:
            self._handle_http_error(
                error=e,
                span="get_lmp_versions",
                message="Failed to get LMP versions",
                extra={'fqn': fqn}
            )
            raise
