from typing import List

from pydantic import BaseModel

from .codes import *

API_ERROR_MESSAGES = {
    E_NO_ERROR: "No error. Operation successful",
    E_INTERNAL_ERROR: "Internal error occurred. Please, try again later or contact support service",
    E_POOL_NOT_FOUND: "Pool was not found",
    E_POOL_ALREADY_EXISTS: "Pool with this name already exists",
    E_POOL_IN_TRANSITION: "Pool is in transition, so it can't be modified",
    E_POOL_NODE_GROUP_INVALID: "Provided parameters for pool node group are invalid",
    E_POOL_UNHEALTHY: "Unhealthy pool can not be modified",
    E_NOT_IMPLEMENTED: "E_NOT_IMPLEMENTED",
}


class ErrorModel(BaseModel):
    code: str
    message: str
    details: List[str] = None


def error_msg(*error_codes):
    messages = [API_ERROR_MESSAGES[ec] for ec in error_codes]
    return "<br>".join(messages)


def error_model(error_code: str, details: List[str] = []):
    return ErrorModel(
        message=API_ERROR_MESSAGES[error_code],
        code=error_code,
        details=details,
    )


def error_body(error_code: str, details: List[str] = []):
    return {
        "code": error_code,
        "message": API_ERROR_MESSAGES[error_code],
        "details": details,
    }
