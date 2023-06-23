import prometheus_client
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from ..util import log_operation_error_to, log_operation_success_to

router = APIRouter(
    tags=["metrics"],
)


def log_operation_success(operation: str, **kwargs):
    log_operation_success_to("api.metrics", operation, **kwargs)


def log_operation_error(operation: str, reason: str, **kwargs):
    log_operation_error_to("api.metrics", operation, reason, **kwargs)


@router.get("/metrics")
async def metrics(
    # operation: str = Depends(Operation("Get metrics")),
):
    # log_operation_success(operation)
    latest_metrics = prometheus_client.generate_latest()
    return PlainTextResponse(content=latest_metrics)
