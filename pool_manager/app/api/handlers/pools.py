from dataclasses import dataclass
from math import ceil
from typing import Any, Awaitable, Callable, List, Optional, Type

from fastapi import APIRouter, Depends, Path, Query, Response
from pydantic import BaseModel, ConstrainedStr, Field, PositiveInt, validator
from sse_starlette import EventSourceResponse
from starlette.status import *

from pool_manager.app.api.errors.model import ErrorModel
from pool_manager.app.constants import *
from pool_manager.app.database.abstract import IDatabase
from pool_manager.app.database.errors import DBPoolNotFoundError
from pool_manager.app.database.orm import (
    ORMNodeGroup,
    ORMOperation,
    ORMPool,
    ORMPoolHealth,
    Paginator,
)
from pool_manager.app.kubernetes.pools import PoolRegistry
from pool_manager.app.kubernetes.pools.errors import PoolNotFoundError
from pool_manager.app.kubernetes.pools.resource_pool import ResourcePool
from pool_manager.app.util.datetime import validate_rfc3339
from pool_manager.app.util.delay import delay

from ...constants import *
from ..base import BasePaginatorResponseModel, ItemCountResponseModel
from ..depends import Operation, get_db, get_pool_registry
from ..errors import error_model, error_msg
from ..errors.codes import *
from ..util import (
    BaseModelPartial,
    QueryPageNum,
    QueryPageSize,
    log_operation_debug_info_to,
    log_operation_error_to,
    log_operation_success_to,
)

router = APIRouter(
    prefix="/pools",
    tags=["pools"],
)

########################################
# Models
########################################


class TObjectID(ConstrainedStr):
    min_length = 1
    max_length = 64


class TUserID(TObjectID):
    pass


class TPoolID(TObjectID):
    pass


class TNodeCount(PositiveInt):
    pass


class TNodeCpuCores(PositiveInt):
    pass


class TNodeRamGb(PositiveInt):
    pass


class TPoolName(ConstrainedStr):
    strip_whitespace = True
    min_length = 1
    max_length = 32


class TPoolDesc(ConstrainedStr):
    min_length = 1
    max_length = 1000


class TNodeGroup(BaseModel):
    node_count: TNodeCount
    node_cpu: TNodeCpuCores
    node_ram: TNodeRamGb


########################################


class TPoolNode(BaseModel):
    name: str
    cpu: int
    ram: int


class GetPoolResourcesResponseModel(BaseModel):
    cpu_total: int
    ram_total: int
    node_count: int
    nodes: List[TPoolNode]


class PoolResources(BaseModel):
    cpu_total: int = Field(0)  # fuzzer_max_cpu * nodes_total # cached on init
    ram_total: int = Field(0)  # fuzzer_max_ram * nodes_total # cached on init
    nodes_total: int = Field(0)  # settings.node_count

    cpu_avail: int = Field(0)  # sum(nodes[*].cpu)
    ram_avail: int = Field(0)  # sum(nodes[*].ram)
    nodes_avail: int = Field(0)  # len(nodes) # maybe delete this?

    fuzzer_max_cpu: int = Field(0)  # min(nodes[*].cpu) # cached on init
    fuzzer_max_ram: int = Field(0)  # min(nodes[*].ram) # cached on init

    nodes: List[TPoolNode] = Field(default_factory=list)


class GetPoolResponseModel(BaseModel):
    id: str
    name: str
    description: str
    user_id: Optional[str]
    exp_date: Optional[str]
    node_group: ORMNodeGroup
    operation: Optional[ORMOperation]
    health: ORMPoolHealth
    created_at: str
    resources: PoolResources
    rs_avail: GetPoolResourcesResponseModel


########################################

DBPoolIterator = Callable[[Paginator], Awaitable[List[ORMPool]]]


class ListPoolsResponseModel(BasePaginatorResponseModel):
    items: List[GetPoolResponseModel]


########################################


def nullable_values(values: List[str]):
    def decorator(cls: Type[BaseModelPartial]):
        cls._nullable_values.extend(values)
        return cls

    return decorator


@nullable_values(["exp_date"])
class UpdatePoolInfoRequestModel(BaseModelPartial):
    name: Optional[TPoolName]
    description: Optional[TPoolDesc]
    exp_date: Optional[str]

    @validator("exp_date")
    def validate_date(value: Optional[str]):
        if value is not None:
            validate_rfc3339(value)
        return value


########################################


class UpdatePoolNodeGroupRequestModel(BaseModel):
    node_count: TNodeCount
    node_cpu: TNodeCpuCores
    node_ram: TNodeRamGb

    class Config:
        schema_extra = {
            "example": {
                "node_cpu": 2,
                "node_ram": 2,
                "node_count": 1,
            }
        }


########################################
# Utils
########################################


def log_operation_debug_info(operation: str, info: Any):
    log_operation_debug_info_to("api.pools", operation, info)


def log_operation_success(operation: str, **kwargs):
    log_operation_success_to("api.pools", operation, **kwargs)


def log_operation_error(operation: str, reason: str, **kwargs):
    log_operation_error_to("api.pools", operation, reason, **kwargs)


def pool_response_model(db_pool: ORMPool, rs_pool: ResourcePool):
    return GetPoolResponseModel(
        rs_avail=GetPoolResourcesResponseModel(
            cpu_total=rs_pool.cpu_total,
            ram_total=rs_pool.ram_total,
            node_count=rs_pool.node_count,
            nodes=[node.dict() for node in rs_pool.nodes],
        ),
        **db_pool.dict(),
    )


########################################
# Create resource pool
########################################


@router.post(
    path="",
    status_code=HTTP_202_ACCEPTED,
    responses={
        HTTP_501_NOT_IMPLEMENTED: {
            "model": ErrorModel,
            "description": error_msg(
                E_NOT_IMPLEMENTED,
            ),
        },
    },
)
async def create_pool(
    response: Response,
    operation: str = Depends(Operation("Create pool")),
):
    def error_response(status_code: int, error_code: str, details: List[str] = []):
        rfail = error_model(error_code, details)
        log_operation_error(operation, rfail)
        response.status_code = status_code
        return rfail

    return error_response(HTTP_501_NOT_IMPLEMENTED, E_NOT_IMPLEMENTED)


########################################
# Get pools count
########################################


@dataclass
class FilterPoolsRequestModel:
    user_id: Optional[str] = Query(None)


@router.get(
    path="/count",
    status_code=HTTP_200_OK,
    responses={
        HTTP_200_OK: {
            "model": ItemCountResponseModel,
            "description": "Successful response",
        },
    },
)
async def count_pools(
    pg_size: int = QueryPageSize(),
    filters: FilterPoolsRequestModel = Depends(),
    operation: str = Depends(Operation("Get pools count")),
    db: IDatabase = Depends(get_db),
):
    total_cnt = await db.pools.count(
        user_id=filters.user_id,
    )
    total_pages = ceil(total_cnt / pg_size)

    response_data = ItemCountResponseModel(
        pg_size=pg_size, pg_total=total_pages, cnt_total=total_cnt
    )

    log_operation_success(
        operation=operation,
    )

    return response_data


@router.get(
    path="/available/count",
    status_code=HTTP_200_OK,
    responses={
        HTTP_200_OK: {
            "model": ItemCountResponseModel,
            "description": "Successful response",
        },
    },
)
async def count_available_pools(
    pg_size: int = QueryPageSize(),
    user_id: str = Query(...),
    operation: str = Depends(Operation("Get available pools count")),
    db: IDatabase = Depends(get_db),
):
    total_cnt = await db.pools.count_available(
        user_id=user_id,
    )
    total_pages = ceil(total_cnt / pg_size)

    response_data = ItemCountResponseModel(
        pg_size=pg_size, pg_total=total_pages, cnt_total=total_cnt
    )

    log_operation_success(
        operation=operation,
    )

    return response_data


########################################
# List pools
########################################


async def _generic_route_handler_list_pools(
    list_pool_coro: DBPoolIterator,
    pool_registry: PoolRegistry,
    operation: str,
    pg_num: int,
    pg_size: int,
):
    paginator = Paginator(pg_num, pg_size)
    db_pools = await list_pool_coro(paginator)

    result = []
    for db_pool in db_pools:
        rs_pool = pool_registry.find_pool(db_pool.id)
        result.append(pool_response_model(db_pool, rs_pool))

    response_data = ListPoolsResponseModel(
        pg_num=pg_num,
        pg_size=pg_size,
        items=result,
    )

    log_operation_success(
        operation=operation,
    )

    return response_data


@router.get(
    path="",
    status_code=HTTP_200_OK,
    responses={
        HTTP_200_OK: {
            "model": ListPoolsResponseModel,
            "description": "Successful response",
        },
    },
)
async def list_pools(
    pg_num: int = QueryPageNum(),
    pg_size: int = QueryPageSize(),
    filters: FilterPoolsRequestModel = Depends(),
    operation: str = Depends(Operation("List pools")),
    pool_registry: PoolRegistry = Depends(get_pool_registry),
    db: IDatabase = Depends(get_db),
):
    return await _generic_route_handler_list_pools(
        list_pool_coro=lambda pgn: db.pools.list(
            paginator=pgn,
            user_id=filters.user_id,
        ),
        pool_registry=pool_registry,
        operation=operation,
        pg_num=pg_num,
        pg_size=pg_size,
    )


@router.get(
    path="/available",
    status_code=HTTP_200_OK,
    responses={
        HTTP_200_OK: {
            "model": ListPoolsResponseModel,
            "description": "Successful response",
        },
    },
)
async def list_available_pools(
    user_id: str = Query(...),
    pg_num: int = QueryPageNum(),
    pg_size: int = QueryPageSize(),
    operation: str = Depends(Operation("List available pools")),
    pool_registry: PoolRegistry = Depends(get_pool_registry),
    db: IDatabase = Depends(get_db),
):
    return await _generic_route_handler_list_pools(
        list_pool_coro=lambda pgn: db.pools.list_available(
            paginator=pgn, user_id=user_id
        ),
        pool_registry=pool_registry,
        operation=operation,
        pg_num=pg_num,
        pg_size=pg_size,
    )


########################################
# Get resource pool by name
########################################


@router.get(
    path="/lookup",
    status_code=HTTP_200_OK,
    responses={
        HTTP_200_OK: {
            "model": GetPoolResponseModel,
            "description": "Successful response",
        },
        HTTP_404_NOT_FOUND: {
            "model": ErrorModel,
            "description": error_msg(E_POOL_NOT_FOUND),
        },
    },
)
async def get_pool_by_name(
    response: Response,
    name: str = Query(...),
    user_id: str = Query(...),
    operation: str = Depends(Operation("Get pool by name")),
    pool_registry: PoolRegistry = Depends(get_pool_registry),
    db: IDatabase = Depends(get_db),
):
    def error_response(status_code: int, error_code: str, details: List[str] = []):
        rfail = error_model(error_code, details)
        kw = {"pool_name": name, "user_id": user_id}
        log_operation_error(operation, rfail, **kw)
        response.status_code = status_code
        return rfail

    try:
        db_pool = await db.pools.get_by_name(name, user_id)
    except DBPoolNotFoundError:
        return error_response(HTTP_404_NOT_FOUND, E_POOL_NOT_FOUND)

    rs_pool = pool_registry.find_pool(db_pool.id)

    log_operation_success(
        operation=operation,
        pool_name=db_pool.name,
        user_id=db_pool.user_id,
    )

    return pool_response_model(db_pool, rs_pool)


########################################
# Pool event stream
########################################


@router.get(
    path="/event-stream",
    status_code=HTTP_200_OK,
    responses={
        HTTP_200_OK: {
            "description": "SSE event stream",
        },
    },
)
async def pool_event_stream(
    operation: str = Depends(Operation("Pool event stream")),
):
    async def event_publisher():
        while True:  # No pool events in this version
            await delay()

    log_operation_success(operation)
    return EventSourceResponse(event_publisher())


########################################
# Get resource pool by id
########################################


@router.get(
    path="/{pool_id}",
    status_code=HTTP_200_OK,
    responses={
        HTTP_200_OK: {
            "model": GetPoolResponseModel,
            "description": "Successful response",
        },
        HTTP_404_NOT_FOUND: {
            "model": ErrorModel,
            "description": error_msg(E_POOL_NOT_FOUND),
        },
    },
)
async def get_pool_by_id(
    response: Response,
    pool_id: str = Path(...),
    user_id: Optional[str] = Query(None),  # Filter param for user API
    operation: str = Depends(Operation("Get pool by id")),
    pool_registry: PoolRegistry = Depends(get_pool_registry),
    db: IDatabase = Depends(get_db),
):
    def error_response(status_code: int, error_code: str, details: List[str] = []):
        rfail = error_model(error_code, details)
        log_operation_error(operation, rfail, pool_id=pool_id)
        response.status_code = status_code
        return rfail

    try:
        rs_pool = pool_registry.find_pool(pool_id)
    except PoolNotFoundError:
        return error_response(HTTP_404_NOT_FOUND, E_POOL_NOT_FOUND)

    db_pool = await db.pools.get_by_id(pool_id)

    # Every user is allowed to get shared pool info
    if user_id is not None and db_pool.user_id not in {None, user_id}:
        return error_response(HTTP_404_NOT_FOUND, E_POOL_NOT_FOUND)

    log_operation_success(
        operation=operation,
        pool_id=rs_pool.id,
    )

    return pool_response_model(db_pool, rs_pool)


########################################
# Get pool resources (directly from k8s)
########################################


@router.get(
    path="/{pool_id}/resources/available",
    status_code=HTTP_200_OK,
    responses={
        HTTP_200_OK: {
            "model": GetPoolResourcesResponseModel,
            "description": "Successful response",
        },
        HTTP_404_NOT_FOUND: {
            "model": ErrorModel,
            "description": error_msg(E_POOL_NOT_FOUND),
        },
    },
)
async def get_pool_available_resources(
    response: Response,
    pool_id: str = Path(...),
    user_id: Optional[str] = Query(None),
    operation: str = Depends(Operation("Get pool available resources")),
    pool_registry: PoolRegistry = Depends(get_pool_registry),
    db: IDatabase = Depends(get_db),
):
    def error_response(status_code: int, error_code: str, details: List[str] = []):
        rfail = error_model(error_code, details)
        log_operation_error(operation, rfail, pool_id=pool_id)
        response.status_code = status_code
        return rfail

    try:
        pool = pool_registry.find_pool(pool_id)
    except PoolNotFoundError:
        return error_response(HTTP_404_NOT_FOUND, E_POOL_NOT_FOUND)

    if user_id is not None:
        try:
            db_pool = await db.pools.get_by_id(pool_id)
        except DBPoolNotFoundError:
            return error_response(HTTP_404_NOT_FOUND, E_POOL_NOT_FOUND)

        # Every user is allowed to get shared pool info
        if db_pool.user_id not in {None, user_id}:
            return error_response(HTTP_404_NOT_FOUND, E_POOL_NOT_FOUND)

    log_operation_success(
        operation=operation,
        pool_id=pool.id,
    )

    return GetPoolResourcesResponseModel(
        cpu_total=pool.cpu_total,
        ram_total=pool.ram_total,
        node_count=pool.node_count,
        nodes=[node.dict() for node in pool.nodes],
    )


########################################
# Update pool info
########################################


@router.patch(
    path="/{pool_id}",
    status_code=HTTP_200_OK,
    responses={
        HTTP_200_OK: {
            "model": None,
            "description": "Successful response",
        },
        HTTP_404_NOT_FOUND: {
            "model": ErrorModel,
            "description": error_msg(E_POOL_NOT_FOUND),
        },
    },
)
async def update_pool_info(
    response: Response,
    pool: UpdatePoolInfoRequestModel,
    pool_id: str = Path(...),
    user_id: Optional[str] = Query(None),
    operation: str = Depends(Operation("Update pool info")),
    pool_registry: PoolRegistry = Depends(get_pool_registry),
    db: IDatabase = Depends(get_db),
):
    def error_response(status_code: int, error_code: str, details: List[str] = []):
        rfail = error_model(error_code, details)
        log_operation_error(operation, rfail, pool_id=pool_id)
        response.status_code = status_code
        return rfail

    log_operation_debug_info(operation, pool)

    if not pool_registry.has_pool(pool_id):
        return error_response(HTTP_404_NOT_FOUND, E_POOL_NOT_FOUND)

    try:
        db_pool = await db.pools.get_by_id(pool_id)
    except DBPoolNotFoundError:
        return error_response(HTTP_404_NOT_FOUND, E_POOL_NOT_FOUND)

    if user_id is not None and db_pool.user_id != user_id:
        return error_response(HTTP_404_NOT_FOUND, E_POOL_NOT_FOUND)

    to_update = pool.dict(exclude_unset=True)
    await db.pools.update_partial(pool_id, **to_update)

    log_operation_success(
        operation=operation,
        pool_id=pool_id,
    )


########################################
# Update pool node group
########################################


@router.put(
    path="/{pool_id}/node_group",
    status_code=HTTP_202_ACCEPTED,
    responses={
        HTTP_202_ACCEPTED: {
            "model": None,
            "description": "Successful response",
        },
        HTTP_501_NOT_IMPLEMENTED: {
            "model": ErrorModel,
            "description": error_msg(E_NOT_IMPLEMENTED),
        },
    },
)
async def update_pool_node_group(
    response: Response,
    pool_id: str = Path(...),
    operation: str = Depends(Operation("Update pool resources")),
):
    def error_response(status_code: int, error_code: str, details: List[str] = []):
        rfail = error_model(error_code, details)
        log_operation_error(operation, rfail, pool_id=pool_id)
        response.status_code = status_code
        return rfail

    return error_response(HTTP_501_NOT_IMPLEMENTED, E_NOT_IMPLEMENTED)


########################################
# Delete pool
########################################


@router.delete(
    path="/{pool_id}",
    status_code=HTTP_202_ACCEPTED,
    responses={
        HTTP_202_ACCEPTED: {
            "model": None,
            "description": "Successful response",
        },
        HTTP_404_NOT_FOUND: {
            "model": ErrorModel,
            "description": error_msg(E_POOL_NOT_FOUND),
        },
        HTTP_409_CONFLICT: {
            "model": ErrorModel,
            "description": error_msg(E_POOL_IN_TRANSITION, E_POOL_UNHEALTHY),
        },
    },
)
async def delete_pool(
    response: Response,
    pool_id: str = Path(...),
    operation: str = Depends(Operation("Delete pool")),
):
    def error_response(status_code: int, error_code: str, details: List[str] = []):
        rfail = error_model(error_code, details)
        log_operation_error(operation, rfail, pool_id=pool_id)
        response.status_code = status_code
        return rfail

    return error_response(HTTP_501_NOT_IMPLEMENTED, E_NOT_IMPLEMENTED)
