#
# Never use 'from __future__ import annotations' here.
# It breaks FastAPI dependency system (name 'Request' is not defined)
# More info: https://github.com/tiangolo/fastapi/issues/1654
#

from fastapi import Request


class Operation:
    def __init__(self, name: str):
        self.name = name

    def __call__(self, request: Request):
        request.state.operation = self.name
        return self.name


def get_db(request: Request):
    return request.app.state.db


def get_settings(request: Request):
    return request.app.state.settings


def get_k8s_client(request: Request):
    return request.app.state.k8s_client


def get_pool_template(request: Request):
    return request.app.state.pool_template


def get_yc_api(request: Request):
    return request.app.state.yc_api


def get_pool_registry(request: Request):
    return request.app.state.pool_registry
