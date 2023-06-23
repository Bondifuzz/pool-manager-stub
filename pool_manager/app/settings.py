"""
## Configuration module
"""

from contextlib import suppress
from typing import Any, Dict, Optional

from pydantic import AnyHttpUrl, BaseModel
from pydantic import BaseSettings as _BaseSettings
from pydantic import Field, NonNegativeInt, PositiveInt, root_validator, validator

from pool_manager.app.util.datetime import duration_in_seconds
from pool_manager.app.util.resources import CpuResources, RamResources

# fmt: off
with suppress(ModuleNotFoundError):
    import dotenv; dotenv.load_dotenv()
# fmt: on


class BaseSettings(_BaseSettings):
    @root_validator
    def check_empty_strings(cls, data: Dict[str, Any]):
        for name, value in data.items():
            if isinstance(value, str):
                if len(value) == 0:
                    var = f"{cls.__name__}.{name}"
                    raise ValueError(f"Variable '{var}': empty string not allowed")

        return data


class CollectionSettings(BaseSettings):
    unsent_messages = "UnsentMessages"
    pools = "Pools"


class DatabaseSettings(BaseSettings):

    engine: str = Field(regex=r"^arangodb$")
    url: AnyHttpUrl
    username: str
    password: str
    name: str

    class Config:
        env_prefix = "DB_"


class EnvironmentSettings(BaseSettings):

    name: str = Field(env="ENVIRONMENT", regex=r"^(dev|prod|test)$")
    shutdown_timeout: int = Field(env="SHUTDOWN_TIMEOUT")
    service_name: Optional[str] = Field(env="SERVICE_NAME")
    service_version: Optional[str] = Field(env="SERVICE_VERSION")
    commit_id: Optional[str] = Field(env="COMMIT_ID")
    build_date: Optional[str] = Field(env="BUILD_DATE")
    commit_date: Optional[str] = Field(env="COMMIT_DATE")
    git_branch: Optional[str] = Field(env="GIT_BRANCH")

    @root_validator(skip_on_failure=True)
    def check_values_for_production(cls, data: Dict[str, Any]):

        if data["name"] != "prod":
            return data

        vars = []
        for name, value in data.items():
            if value is None:
                vars.append(name.upper())

        if vars:
            raise ValueError(f"Variables must be set in production mode: {vars}")

        return data


class PoolOperationDelaySettings(BaseSettings):
    create: NonNegativeInt
    update: NonNegativeInt
    delete: NonNegativeInt

    class Config:
        env_prefix = "POOL_OPERATION_DELAY_"

    @validator("create", "update", "delete", pre=True)
    def validate_delay(value: Optional[str]):
        return duration_in_seconds(value or "")


class PollIntervalSettings(BaseSettings):
    yc_poller: PositiveInt
    scheduled_ops: PositiveInt
    expired_pools: PositiveInt

    class Config:
        env_prefix = "POLL_INTERVAL_"

    @validator("yc_poller", "scheduled_ops", "expired_pools", pre=True)
    def validate_delay(value: Optional[str]):
        return duration_in_seconds(value or "")


class PoolNodeSettings(BaseSettings):
    diverted_cpu: PositiveInt
    diverted_ram: PositiveInt

    class Config:
        env_prefix = "POOL_NODE_"

    @validator("diverted_cpu", pre=True)
    def validate_cpu(value: Optional[str]):
        return CpuResources.from_string(value or "")

    @validator("diverted_ram", pre=True)
    def validate_ram(value: Optional[str]):
        return RamResources.from_string(value or "")


class YCAPIEndpointSettings(BaseSettings):

    operations: AnyHttpUrl
    node_groups: AnyHttpUrl
    auth: AnyHttpUrl

    class Config:
        env_prefix = "YC_API_URL_"


class YandexCloudAPISettings(BaseSettings):

    endpoints: YCAPIEndpointSettings
    service_account_id: str
    public_key_id: str
    private_key_filepath: str

    class Config:
        env_prefix = "YC_API_"


class AppSettings(BaseModel):
    database: DatabaseSettings
    collections: CollectionSettings
    environment: EnvironmentSettings
    poll_interval: PollIntervalSettings
    operation_delay: PoolOperationDelaySettings
    yc_api: YandexCloudAPISettings
    pool_node: PoolNodeSettings


_app_settings = None


def get_app_settings() -> AppSettings:

    global _app_settings

    if _app_settings is None:
        _app_settings = AppSettings(
            database=DatabaseSettings(),
            collections=CollectionSettings(),
            yc_api=YandexCloudAPISettings(endpoints=YCAPIEndpointSettings()),
            operation_delay=PoolOperationDelaySettings(),
            poll_interval=PollIntervalSettings(),
            environment=EnvironmentSettings(),
            pool_node=PoolNodeSettings(),
        )

    return _app_settings
