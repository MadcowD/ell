from typing import Optional

from ell.serialize.sql import SQLSerializer, AsyncSQLSerializer
from ell.stores.sql import SQLiteStore
from ell.stores.store import AsyncBlobStore, BlobStore



class SQLiteSerializer(SQLSerializer):
    def __init__(self, storage_dir: str, blob_store: Optional[BlobStore] = None):
        super().__init__(SQLiteStore(storage_dir, blob_store))


# todo(async). underlying store is not async
class AsyncSQLiteSerializer(AsyncSQLSerializer):
    def __init__(self, storage_dir: str, blob_store: Optional[AsyncBlobStore] = None):
        super().__init__(SQLiteStore(storage_dir, blob_store))

