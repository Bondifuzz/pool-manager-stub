from typing import Any, List

from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError


class QueryBaseModel(BaseModel):
    """
    Handle ValueError/ValidationError/... raised from
    @validator and @root_validator(FastAPI doesn't handle it by default)
    Solution: Convert pydantic ValidationError to fastapi RequestValidationError
    """

    def __init__(self, **data):
        try:
            super().__init__(**data)
        except ValidationError as e:
            raise RequestValidationError(e.raw_errors) from e


class ItemCountResponseModel(BaseModel):
    pg_size: int
    pg_total: int
    cnt_total: int


class BasePaginatorResponseModel(BaseModel):
    pg_num: int
    pg_size: int
    # TODO: add offset
    items: List[Any]
