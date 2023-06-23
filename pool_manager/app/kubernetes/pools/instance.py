from __future__ import annotations

from pool_manager.app.database.abstract import IDatabase
from pool_manager.app.settings import AppSettings
from pool_manager.app.util.pool_health import pool_health

from .pool_registry import PoolRegistry


async def pool_registry_init(
    db: IDatabase,
    settings: AppSettings,
):
    registry = PoolRegistry()
    async for pool in await db.pools.list_internal():
        registry.create_pool(pool.id)
        pool.resources.nodes_total = 1
        pool.resources.nodes_avail = 1
        pool.resources.cpu_avail = pool.resources.cpu_total
        pool.resources.ram_avail = pool.resources.ram_total

        registry.find_pool(pool.id).add_node(
            node_name=pool.name + "_node",
            cpu=pool.resources.cpu_total,
            ram=pool.resources.ram_total,
        )

    async for pool in await db.pools.list_no_operations():
        pool.health = pool_health(registry.find_pool(pool.id), pool)
        await db.pools.update(pool)

    return registry
