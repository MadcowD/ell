from functools import lru_cache
import json
import os
from typing import Optional
from pydantic import BaseModel

import logging

logger = logging.getLogger(__name__)


# todo. maybe we default storage dir and other things in the future to a well-known location
# like ~/.ell or something
@lru_cache(maxsize=1)
def ell_home() -> str:
    return os.path.join(os.path.expanduser("~"), ".ell")


class Config(BaseModel):
    pg_connection_string: Optional[str] = None
    storage_dir: Optional[str] = None
    mqtt_connection_string: Optional[str] = None
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def model_post_init(self, __context):
        # Storage
        self.pg_connection_string = self.pg_connection_string or os.getenv(
            "ELL_PG_CONNECTION_STRING")
        self.storage_dir = self.storage_dir or os.getenv("ELL_STORAGE_DIR")
        
        # Enforce that we use either sqlite or postgres, but not both
        if self.pg_connection_string is not None and self.storage_dir is not None:
            raise ValueError("Cannot use both sqlite and postgres")

        # For now, fall back to sqlite if no PostgreSQL connection string is provided
        if self.pg_connection_string is None and self.storage_dir is None:
            # This intends to honor the default we had set in the CLI
            # todo. better default?
            self.storage_dir = os.getcwd()
        
        # Pubsub
        self.mqtt_connection_string = self.mqtt_connection_string or os.getenv("ELL_MQTT_CONNECTION_STRING")

        logger.info(f"Resolved config: {json.dumps(self.model_dump(), indent=2)}")

