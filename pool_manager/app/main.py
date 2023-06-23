from __future__ import annotations

import logging
import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRoute
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from pool_manager.app.api.errors import error_model
from pool_manager.app.api.errors.codes import E_INTERNAL_ERROR
from pool_manager.app.database.errors import DatabaseError
from pool_manager.app.kubernetes.pools import PoolRegistry
from pool_manager.app.kubernetes.pools.instance import pool_registry_init

from . import api
from .database.instance import db_init
from .settings import AppSettings, get_app_settings
from .util.speedup.json import JSONResponse
from .util.speedup.json import dumps as json_dumps

if TYPE_CHECKING:
    from .database.abstract import IDatabase


def configure_exception_handlers(app):

    # Common error response format
    def error_response():

        content = {
            "status": "FAILED",
            "error": error_model(E_INTERNAL_ERROR),
        }

        return JSONResponse(content, HTTP_500_INTERNAL_SERVER_ERROR)

    @app.exception_handler(DatabaseError)
    async def db_exception_handler(request: Request, e: DatabaseError):
        operation = request.state.operation
        route = f"{request.method} {request.url.path}"
        msg = "Unexpected DB error: %s. Operation: '%s'. Route: '%s'"
        logging.getLogger("db").error(msg, e, operation, route)
        return error_response()


class AppState:
    pool_registry: PoolRegistry
    settings: AppSettings
    db: IDatabase


def configure_startup_events(app: FastAPI, settings: AppSettings):

    logger = logging.getLogger("main")

    @contextmanager
    def startup_helper(msg: str) -> Iterator[AppState]:
        logger.info(f"{msg}...")
        yield app.state
        logger.info(f"{msg}... OK")

    @app.on_event("startup")
    async def init_database():
        with startup_helper("Configuring database") as state:
            state.db = await db_init(settings)

    @app.on_event("startup")
    async def init_pool_registry():
        with startup_helper("Creating pool registry") as state:
            state.pool_registry = await pool_registry_init(
                state.db,
                settings,
            )


def configure_shutdown_events(app: FastAPI):

    logger = logging.getLogger("main")

    @contextmanager
    def shutdown_helper(msg: str) -> Iterator[AppState]:
        logger.info(f"{msg}...")
        yield app.state
        logger.info(f"{msg}... OK")

    @app.on_event("shutdown")
    async def exit_database():
        with shutdown_helper("Closing database") as state:
            await state.db.close()


def configure_routes(app: FastAPI):

    logger = logging.getLogger("main")
    logger.info("Configuring routes...")

    pfx = "/api/v1"
    app.include_router(api.pools.router, prefix=pfx)
    app.include_router(api.metrics.router)

    with open("index.html") as f:
        index_html = f.read()

    @app.get("/")
    async def index():
        return HTMLResponse(index_html)

    # Simplify openapi.json
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name

    logger.info("Configuring routes... OK")


def generate_api_spec():

    app = FastAPI()
    configure_routes(app)

    print("Generating openapi.json...")

    with open("openapi.json", "w") as f:
        f.write(json_dumps(app.openapi()))

    print("Generating openapi.json... OK")
    sys.exit(0)


class EmptyJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        if content is None:
            content = dict()
        return super().render(content)


def create_app():

    app = FastAPI(default_response_class=EmptyJSONResponse)
    state: AppState = app.state

    settings = get_app_settings()
    logging.info("%-16s %s", "ENVIRONMENT", settings.environment.name)
    logging.info("%-16s %s", "SERVICE_NAME", settings.environment.service_name)
    logging.info("%-16s %s", "SERVICE_VERSION", settings.environment.service_version)
    logging.info("%-16s %s", "COMMIT_ID", settings.environment.commit_id)
    logging.info("%-16s %s", "BUILD_DATE", settings.environment.build_date)
    logging.info("%-16s %s", "COMMIT_DATE", settings.environment.commit_date)
    logging.info("%-16s %s", "GIT_BRANCH", settings.environment.git_branch)

    configure_routes(app)
    configure_startup_events(app, settings)
    configure_shutdown_events(app)
    configure_exception_handlers(app)

    state.settings = settings
    return app
