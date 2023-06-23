from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List

from devtools import debug
from fastapi import Query
from pydantic import BaseModel, root_validator

if TYPE_CHECKING:
    from .errors import ErrorModel


class BaseModelPartial(BaseModel):
    _nullable_values: List[str] = []

    @root_validator(pre=True)
    def nullable_values_validator(cls, data: Dict[str, Any]):
        for k, v in data.items():
            if v is None and k not in cls._nullable_values:
                raise ValueError(f"{k} can't be null")

        return data

    @root_validator
    def check_at_least_one_field_set(cls, data: Dict[str, Any]):

        if len(list(filter(lambda x: x is not None, data.values()))) == 0:
            raise ValueError("At least one field must be set")

        return data


def log_operation_debug_info_to(
    logger_name: str,
    operation: str,
    info: Any,
):
    logger = logging.getLogger(logger_name)
    if not logger.isEnabledFor(logging.DEBUG):
        return

    text = "Debug info for operation '%s':\n%s"
    output = debug.format(info).str(highlight=True)
    logger.debug(text, operation, output)


def log_operation_success_to(
    logger_name: str,
    operation: str,
    **kwargs,
):
    logger = logging.getLogger(logger_name)
    kw_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info("[OK] Operation='%s', %s", operation, kw_str)


def log_operation_error_to(
    logger_name: str,
    operation: str,
    error: ErrorModel,
    **kwargs,
):
    logger = logging.getLogger(logger_name)
    kw_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])

    msg = "[FAILED] Operation='%s', reason='%s', %s"
    logger.info(msg, operation, error.message, kw_str)


def QueryPageNum():
    return Query(ge=0, default=0)


def QueryPageSize():
    return Query(ge=10, le=200, default=100)
