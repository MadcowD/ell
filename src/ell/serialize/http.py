import logging
from typing import List, Optional, Dict, Any

import httpx
from httpx import HTTPStatusError

from ell.serialize.protocol import EllAsyncSerializer, EllSerializer
from ell.types.serialize import GetLMPOutput, WriteLMPInput, LMP, WriteInvocationInput


class EllHTTPSerializer(EllSerializer):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url)
        self.supports_blobs = True  # we assume the server does, if not will find out later

    def get_lmp(self, lmp_id: str) -> GetLMPOutput:
        response = self.client.get(f"/lmp/{lmp_id}")
        response.raise_for_status()
        data = response.json()
        if data is None:
            return None
        return LMP(**data)

    def write_lmp(self, lmp: WriteLMPInput, uses: List[str]) -> None:
        try:
            response = self.client.post("/lmp", json={
                "lmp": lmp.model_dump(mode="json"),
                "uses": uses
            })
            response.raise_for_status()
        except HTTPStatusError as e:
            if e.response.status_code == 422:
                error_detail = e.response.json().get("detail", "No detailed error message provided")
                logging.error(f"Unprocessable Entity (422) Error: {error_detail}")
                raise ValueError(f"Invalid input: {error_detail}") from e
            raise

    def write_invocation(self, input: WriteInvocationInput) -> None:
        response = self.client.post(
            "/invocation",
            json=input.model_dump(mode="json")
        )
        response.raise_for_status()
        return None

    def store_blob(self, blob_id: str, blob: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        response = self.client.post("/blob", data={
            "blob_id": blob_id,
            "blob": blob,
            "metadata": metadata
        })
        response.raise_for_status()
        return response.json()["blob_id"]

    def retrieve_blob(self, blob_id: str) -> bytes:
        response = self.client.get(f"/blob/{blob_id}")
        response.raise_for_status()
        return response.content

    def close(self):
        self.client.close()

    def get_lmp_versions(self, fqn: str) -> List[LMP]:
        response = self.client.get("/lmp/versions", params={"fqn": fqn})
        response.raise_for_status()
        data = response.json()
        return [LMP(**lmp_data) for lmp_data in data]


class EllAsyncHTTPSerializer(EllAsyncSerializer):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
        self.supports_blobs = True  # we assume the server does, if not will find out later

    async def get_lmp(self, lmp_id: str) -> GetLMPOutput:
        response = await self.client.get(f"/lmp/{lmp_id}")
        response.raise_for_status()
        data = response.json()
        if data is None:
            return None
        return LMP(**data)

    async def write_lmp(self, lmp: WriteLMPInput, uses: List[str]) -> None:
        try:
            response = await self.client.post("/lmp", json={
                "lmp": lmp.model_dump(mode="json"),
                "uses": uses
            })
            response.raise_for_status()
        except HTTPStatusError as e:
            if e.response.status_code == 422:
                error_detail = e.response.json().get("detail", "No detailed error message provided")
                logging.error(f"Unprocessable Entity (422) Error: {error_detail}")
                raise ValueError(f"Invalid input: {error_detail}") from e
            raise

    async def write_invocation(self, input: WriteInvocationInput) -> None:
        response = await self.client.post(
            "/invocation",
            json=input.model_dump(mode="json")
        )
        response.raise_for_status()
        return None

    async def store_blob(self, blob_id: str, blob: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
        response = await self.client.post("/blob", data={
            "blob_id": blob_id,
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
