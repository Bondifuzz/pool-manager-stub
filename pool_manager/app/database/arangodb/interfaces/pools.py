from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, List, Optional, Tuple

from aioarangodb.cursor import Cursor

from pool_manager.app.database.abstract import IPools
from pool_manager.app.database.errors import DBPoolNotFoundError
from pool_manager.app.database.orm import (
    BaseModel,
    ORMNodeGroup,
    ORMOperation,
    ORMPool,
    ORMPoolHealth,
    Paginator,
)

from .base import DBBase
from .util import dbkey_to_id, id_to_dbkey, maybe_unknown_error

if TYPE_CHECKING:
    from aioarangodb.collection import StandardCollection
    from aioarangodb.database import StandardDatabase

    from pool_manager.app.settings import CollectionSettings


class DBPools(DBBase, IPools):

    _col_pools: StandardCollection

    def __init__(self, db: StandardDatabase, collections: CollectionSettings):
        self._col_pools = db[collections.pools]
        super().__init__(db, collections)

    @maybe_unknown_error
    async def create(
        self,
        name: str,
        description: str,
        user_id: Optional[str],
        exp_date: Optional[str],
        node_group: ORMNodeGroup,
        yc_node_group_id: Optional[str],
        operation: Optional[ORMOperation],
        health: ORMPoolHealth,
        created_at: str,
    ) -> ORMPool:

        # Converts model to dict, if it present
        def model_to_dict(model: Optional[BaseModel]):
            return model.dict() if model else None

        doc = {
            "name": name,
            "description": description,
            "user_id": user_id,
            "exp_date": exp_date,
            "node_group": model_to_dict(node_group),
            "yc_node_group_id": yc_node_group_id,
            "operation": model_to_dict(operation),
            "health": health.value,
            "created_at": created_at,
        }

        res = await self._col_pools.insert(doc)

        return ORMPool(
            id=res["_key"],
            **doc,
        )

    @maybe_unknown_error
    async def get_by_id(self, pool_id: str) -> ORMPool:

        doc = await self._col_pools.get(pool_id)

        if doc is None:
            raise DBPoolNotFoundError()

        return ORMPool(**dbkey_to_id(doc))

    @maybe_unknown_error
    async def get_by_name(self, pool_name: str, user_id: str) -> ORMPool:

        if user_id == "shared":
            user_id = None

        filters = {"name": pool_name, "user_id": user_id}
        cursor: Cursor = await self._col_pools.find(filters, limit=1)

        if cursor.empty():
            raise DBPoolNotFoundError()

        return ORMPool(**dbkey_to_id(cursor.pop()))

    @maybe_unknown_error
    async def update(self, pool: ORMPool):
        await self._col_pools.replace(
            id_to_dbkey(pool.dict()),
            silent=True,
        )

    @maybe_unknown_error
    async def update_partial(self, pool_id: str, **kwargs):
        assert ORMPool.fields_match(kwargs.keys())
        await self._col_pools.update(
            {"_key": pool_id, **kwargs},
            silent=True,
        )

    @maybe_unknown_error
    async def delete(self, pool_id: str):
        await self._col_pools.delete(pool_id)

    @maybe_unknown_error
    async def count_available(self, user_id: str) -> int:

        # fmt: off
        query, variables = """
            FOR pool in @@collection
                FILTER pool.user_id == null OR pool.user_id == @user_id
                COLLECT WITH COUNT INTO length
                RETURN length
        """, {
            "@collection": self._col_pools.name,
            "user_id": user_id,
        }
        # fmt: on

        cursor: Cursor = await self._db.aql.execute(query, bind_vars=variables)
        return cursor.pop()

    @maybe_unknown_error
    async def count(
        self,
        user_id: Optional[str] = None,
    ) -> int:

        # fmt: off
        query, variables = """
            FOR pool in @@collection
                <filters>
                COLLECT WITH COUNT INTO length
                RETURN length
        """, {
            "@collection": self._col_pools.name,
        }
        # fmt: on

        if user_id is None:
            filter = ""

        elif user_id == "shared":
            filter = "FILTER pool.user_id == null"

        else:
            filter = "FILTER pool.user_id == @user_id"
            variables["user_id"] = user_id

        query = query.replace("<filters>", filter)

        cursor: Cursor = await self._db.aql.execute(query, bind_vars=variables)
        return cursor.pop()

    def _base_list_query(self, paginator: Paginator) -> Tuple[str, Dict[str, Any]]:
        # TODO: doing sort by (pool.user_id, pool.name)?
        # this must be faster if we create such index for unique name check
        # and by doing so we will group projects by owner
        return """
            FOR pool in @@collection
                <filter-options>
                SORT pool.name DESC
                LIMIT @offset, @limit
                RETURN MERGE(pool, {
                    "id": pool._key,
                })
        """, {
            "@collection": self._col_pools.name,
            "offset": paginator.offset,
            "limit": paginator.limit,
        }

    @maybe_unknown_error
    async def list_available(self, paginator: Paginator, user_id: str) -> List[ORMPool]:
        query, variables = self._base_list_query(paginator)
        filter_query = "FILTER pool.user_id == null OR pool.user_id == @user_id"
        variables["user_id"] = user_id
        query = query.replace("<filter-options>", filter_query)

        cursor = await self._db.aql.execute(query, bind_vars=variables)
        return [ORMPool(**doc) async for doc in cursor]

    @maybe_unknown_error
    async def list(
        self,
        paginator: Paginator,
        user_id: Optional[str] = None,
    ) -> List[ORMPool]:

        query, variables = self._base_list_query(paginator)

        if user_id is None:
            filter = ""

        elif user_id == "shared":
            filter = "FILTER pool.user_id == null"

        else:
            filter = "FILTER pool.user_id == @user_id"
            variables["user_id"] = user_id

        query = query.replace("<filter-options>", filter)

        cursor = await self._db.aql.execute(query, bind_vars=variables)
        return [ORMPool(**doc) async for doc in cursor]

    @staticmethod
    async def _async_pool_iter(cursor: Cursor):
        async for doc in cursor:
            yield ORMPool(**doc)

    @maybe_unknown_error
    async def list_internal(self) -> AsyncIterator[ORMPool]:

        # fmt: off
        query, variables  ="""
            FOR pool in @@collection
                RETURN MERGE(pool, {
                    "id": pool._key,
                })
        """, {
            "@collection": self._collections.pools,
        }
        # fmt: on

        cursor = await self._db.aql.execute(query, bind_vars=variables)
        return self._async_pool_iter(cursor)

    @maybe_unknown_error
    async def list_expired(self) -> AsyncIterator[ORMPool]:

        # fmt: off
        query, variables  ="""
            FOR pool in @@collection
                FILTER pool.exp_date != null
                FILTER pool.operation == null
                FILTER DATE_ISO8601(DATE_NOW()) > pool.exp_date
                RETURN MERGE(pool, {"id": pool._key})
        """, {
            "@collection": self._collections.pools,
        }
        # fmt: on

        cursor = await self._db.aql.execute(query, bind_vars=variables)
        return self._async_pool_iter(cursor)

    @maybe_unknown_error
    async def list_operations_in_progress(self):

        # fmt: off
        query, variables = """
            FOR pool in @@collection
                FILTER pool.operation != null
                FILTER pool.operation.yc_operation_id != null
                FILTER pool.operation.error_msg == null
                RETURN MERGE(pool, {"id": pool._key})
        """, {
            "@collection": self._col_pools.name,
        }
        # fmt: on

        cursor = await self._db.aql.execute(query, bind_vars=variables)
        return self._async_pool_iter(cursor)

    @maybe_unknown_error
    async def list_operations_scheduled(self):

        # fmt: off
        query, variables = """
            FOR pool in @@collection
                FILTER pool.operation != null
                FILTER pool.operation.yc_operation_id == null
                FILTER pool.operation.error_msg == null
                FILTER DATE_ISO8601(DATE_NOW()) > pool.operation.scheduled_for
                RETURN MERGE(pool, {"id": pool._key})
        """, {
            "@collection": self._col_pools.name,
        }
        # fmt: on

        cursor = await self._db.aql.execute(query, bind_vars=variables)
        return self._async_pool_iter(cursor)

    @maybe_unknown_error
    async def list_no_operations(self):

        # fmt: off
        query, variables = """
            FOR pool in @@collection
                FILTER pool.operation == null
                RETURN MERGE(pool, {"id": pool._key})
        """, {
            "@collection": self._col_pools.name,
        }
        # fmt: on

        cursor = await self._db.aql.execute(query, bind_vars=variables)
        return self._async_pool_iter(cursor)
