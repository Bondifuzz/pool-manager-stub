from typing import Any

from pydantic import BaseModel

from ..helpers import try_import_module
from ..logger import logger


def _default(obj):
    if isinstance(obj, BaseModel):
        return obj.dict()
    raise TypeError()


if try_import_module("orjson"):

    import orjson  # type: ignore
    from fastapi.responses import ORJSONResponse as JSONResponse  # noqa

    def loads(s: str) -> Any:
        return orjson.loads(s)

    def dumps(obj: Any) -> str:
        return orjson.dumps(obj, default=_default).decode()

    logger.debug("Using JSON fast loader: orjson")

else:
    import json

    from fastapi.responses import JSONResponse  # noqa

    def loads(s: str) -> Any:
        return json.loads(s)

    def dumps(obj: Any) -> str:
        return json.dumps(obj, default=_default)

    logger.debug("Fast loaders not found. Using default JSON loader")
