import logging
from dataclasses import dataclass
from typing import Dict

from pool_manager.app.util.logging import PrefixedLogger

from .errors import PoolNodeAlreadyExistsError, PoolNodeNotFoundError


@dataclass
class PoolNode:
    name: str
    cpu: int
    ram: int

    def dict(self):
        return self.__dict__


class ResourcePool:

    _id: str
    _logger: logging.Logger

    _cpu_total: int
    _ram_total: int
    _nodes: Dict[str, PoolNode]

    def _setup_logging(self):
        logger = logging.getLogger("pool")
        extra = {"prefix": f"[Pool <id='{self._id}'>]"}
        self._logger = PrefixedLogger(logger, extra)

    def __init__(self, pool_id: str):
        self._id = pool_id
        self._cpu_total = 0
        self._ram_total = 0
        self._nodes = {}
        self._setup_logging()

    def add_node(self, node_name: str, cpu: int, ram: int):

        assert cpu > 0, "cpu must be greater than zero"
        assert ram > 0, "ram must be greater than zero"

        if node_name in self._nodes:
            msg = f"Node '{node_name}' already exists in pool '{self._id}'"
            raise PoolNodeAlreadyExistsError(msg)

        self._cpu_total += cpu
        self._ram_total += ram
        self._nodes[node_name] = PoolNode(node_name, cpu, ram)

        msg = "Node added: <name='%s', cpu=%dm, ram=%dMi>"
        self._logger.debug(msg, node_name, cpu, ram)

        msg = "Summary: <cpu_total=%dm, ram_total=%dMi, node_count=%d>"
        args = self._cpu_total, self._ram_total, self.node_count
        self._logger.debug(msg, *args)

    def remove_node(self, node_name: str):

        try:
            node = self._nodes.pop(node_name)
        except KeyError as e:
            msg = f"Node '{node_name}' not found in pool '{self._id}'"
            raise PoolNodeNotFoundError(msg) from e

        self._cpu_total -= node.cpu
        self._ram_total -= node.ram
        assert self._cpu_total >= 0
        assert self._ram_total >= 0

        msg = "Node removed: <name='%s', cpu=%dm, ram=%dMi>"
        self._logger.debug(msg, node.name, node.cpu, node.ram)

        msg = "Summary: <cpu_total=%dm, ram_total=%dMi, node_count=%d>"
        args = self._cpu_total, self._ram_total, self.node_count
        self._logger.debug(msg, *args)

    @property
    def id(self):
        return self._id

    @property
    def cpu_total(self):
        return self._cpu_total

    @property
    def ram_total(self):
        return self._ram_total

    @property
    def node_count(self):
        return len(self._nodes)

    @property
    def nodes(self):
        return list(self._nodes.values())
