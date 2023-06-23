from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel as _BaseModel


class BaseModel(_BaseModel):
    @classmethod
    def fields_match(cls, fields: List[str]):
        keys = cls.__fields__.keys()
        return all(field in keys for field in fields)


class ORMPoolHealth(str, Enum):
    ok = "Ok"
    warning = "Warning"
    error = "Error"


class ORMPoolStatus(str, Enum):
    ready = "Ready"
    creating = "Creating"
    resizing = "Resizing"
    deleting = "Deleting"


class ORMNodeGroup(BaseModel):
    node_count: int


class ORMOperationType(str, Enum):
    create = "Create"
    update = "Update"
    delete = "Delete"


class ORMOperation(BaseModel):
    type: ORMOperationType
    scheduled_for: str
    yc_operation_id: Optional[str]
    error_msg: Optional[str]


class ORMResources(BaseModel):
    cpu_total: int
    ram_total: int
    nodes_total: int

    cpu_avail: int
    ram_avail: int
    nodes_avail: int

    fuzzer_max_cpu: int
    fuzzer_max_ram: int


class ORMPool(BaseModel):
    id: str
    name: str
    description: str
    user_id: Optional[str]
    exp_date: Optional[str]
    node_group: ORMNodeGroup
    operation: Optional[ORMOperation]
    health: ORMPoolHealth
    created_at: str
    resources: ORMResources


class Paginator:
    def __init__(self, pg_num: int, pg_size: int):
        self.pg_num = pg_num
        self.pg_size = pg_size
        self.offset = pg_num * pg_size
        self.limit = pg_size
