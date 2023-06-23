class ResourcePoolError(Exception):
    pass


class PoolNodeAlreadyExistsError(ResourcePoolError):
    pass


class PoolNodeNotFoundError(ResourcePoolError):
    pass


class PoolRegistryError(Exception):
    pass


class PoolNotFoundError(PoolRegistryError):
    pass


class PoolAlreadyExistsError(PoolRegistryError):
    pass
