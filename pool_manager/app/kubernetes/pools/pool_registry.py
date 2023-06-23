from logging import getLogger
from typing import Dict

from .errors import PoolAlreadyExistsError, PoolNotFoundError
from .resource_pool import ResourcePool


class PoolRegistry:

    _pools: Dict[str, ResourcePool]

    def __init__(self):
        self._pools = {}
        self._logger = getLogger("pool.registry")

    def create_pool(self, pool_id: str):

        if pool_id in self._pools:
            msg = f"Pool '{pool_id}' already exists"
            raise PoolAlreadyExistsError(msg)

        pool = ResourcePool(pool_id)
        self._pools[pool_id] = pool

    def remove_pool(self, pool_id: str):
        try:
            self._pools.pop(pool_id)
        except KeyError as e:
            msg = f"Pool '{pool_id}' not found"
            raise PoolNotFoundError(msg) from e

    def find_pool(self, pool_id: str):

        try:
            res = self._pools[pool_id]
        except KeyError as e:
            msg = f"Pool '{pool_id}' not found"
            raise PoolNotFoundError(msg) from e

        return res

    def has_pool(self, pool_id: str):
        return self._pools.get(pool_id) is not None

    @property
    def pools(self):
        return list(self._pools.values())
