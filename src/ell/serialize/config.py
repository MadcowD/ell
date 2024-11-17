import json
from typing import Any, Optional
from pydantic import BaseModel, Field, computed_field

import logging

logger = logging.getLogger(__name__)


class SerializeConfig(BaseModel):
    storage_dir: Optional[str] = Field(default=None, description="Filesystem path used for SQLite and local blob storage")
    api_url: Optional[str] = Field(default=None, description="ell API server endpoint")
    pg_connection_string: Optional[str] = None
    minio_endpoint: Optional[str] = None
    minio_access_key: Optional[str] = None
    minio_secret_key: Optional[str] = None
    minio_bucket: Optional[str] = None
    log_level: int = logging.INFO


    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

    def model_post_init(self, __context: Any):
        # Enforce that we use 1 storage backend (for now)
        if self.pg_connection_string is not None and self.storage_dir is not None:
            raise ValueError("Cannot use both sqlite and postgres")
        logger.debug(f"Resolved config: {json.dumps(self.model_dump(exclude_none=True), indent=2)}")

    @computed_field
    def is_enabled(self) -> bool:
        return bool(self.api_url or self.pg_connection_string or self.storage_dir or self.minio_endpoint)

