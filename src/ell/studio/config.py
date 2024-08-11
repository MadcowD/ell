from functools import lru_cache
import os
from typing import Optional
from pydantic import BaseModel

import logging

logger = logging.getLogger(__name__)


# todo. maybe we default storage dir and other things in the future to a well-known location
# like ~/.ell or something
@lru_cache
def ell_home() -> str:
    return os.path.join(os.path.expanduser("~"), ".ell")


class Config(BaseModel):
    pg_connection_string: Optional[str] = None
    storage_dir: Optional[str] = None

    @classmethod
    def create(
        cls,
        storage_dir: Optional[str] = None,
        pg_connection_string: Optional[str] = None,
    ) -> 'Config':
        pg_connection_string = pg_connection_string or os.getenv("ELL_PG_CONNECTION_STRING")
        storage_dir = storage_dir or os.getenv("ELL_STORAGE_DIR")

        # Enforce that we use either sqlite or postgres, but not both
        if pg_connection_string is not None and storage_dir is not None:
            raise ValueError("Cannot use both sqlite and postgres")
        
        # For now, fall back to sqlite if no PostgreSQL connection string is provided
        if pg_connection_string is None and storage_dir is None:
            # This intends to honor the default we had set in the CLI
            storage_dir = os.getcwd()

        return cls(pg_connection_string=pg_connection_string, storage_dir=storage_dir)