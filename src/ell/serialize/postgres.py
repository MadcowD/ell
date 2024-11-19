from typing import Optional

from ell.serialize.sql import SQLSerializer, AsyncSQLSerializer
from ell.stores.sql import PostgresStore
from ell.stores.store import BlobStore, AsyncBlobStore


class PostgresSerializer(SQLSerializer):
    def __init__(self, db_uri: str, blob_store: Optional[BlobStore] = None):
        super().__init__(PostgresStore(db_uri, blob_store))


# todo(async): the underlying store is not async-aware
class AsyncPostgresSerializer(AsyncSQLSerializer):
    def __init__(self, db_uri: str, blob_store: Optional[AsyncBlobStore] = None):
        super().__init__(PostgresStore(db_uri, blob_store))
