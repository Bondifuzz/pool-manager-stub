from pool_manager.app.database.orm import ORMPool, ORMPoolHealth
from pool_manager.app.kubernetes.pools import ResourcePool


def pool_health(rs_pool: ResourcePool, db_pool: ORMPool):

    nodes_current = rs_pool.node_count
    nodes_expected = db_pool.node_group.node_count

    if nodes_current == 0:
        return ORMPoolHealth.error
    elif nodes_current != nodes_expected:
        return ORMPoolHealth.warning
    else:  # nodes_current == nodes_expected:
        return ORMPoolHealth.ok
