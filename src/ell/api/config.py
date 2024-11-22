# todo. move this under ell.api.server
import json
import os
from typing import Any, Optional
from pydantic import BaseModel

import logging

logger = logging.getLogger(__name__)


class Config(BaseModel):
    storage_dir: Optional[str] = None
    pg_connection_string: Optional[str] = None
    mqtt_connection_string: Optional[str] = None
    minio_endpoint: Optional[str] = None
    minio_access_key: Optional[str] = None
    minio_secret_key: Optional[str] = None
    minio_bucket: Optional[str] = None
    log_level: int = logging.INFO

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

    def model_post_init(self, __context: Any):
        # Storage
        # Enforce that we use either sqlite or postgres, but not both
        if self.pg_connection_string is not None and self.storage_dir is not None:
            raise ValueError("Cannot use both sqlite and postgres")

        # For now, fall back to sqlite if no PostgreSQL connection string is provided
        if self.pg_connection_string is None and self.storage_dir is None:
            # This intends to honor the default we had set in the CLI
            # todo. better default?
            self.storage_dir = os.getcwd()

        logger.info(f"Resolved config: {json.dumps(self.model_dump(exclude_none=True), indent=2)}")

