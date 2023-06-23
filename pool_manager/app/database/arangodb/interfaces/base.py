from aioarangodb.database import StandardDatabase

from pool_manager.app.settings import CollectionSettings


class DBBase:

    _db: StandardDatabase
    _collections: CollectionSettings

    def __init__(self, db, collections):
        self._collections = collections
        self._db = db
