"""
## Configuration module
"""

from contextlib import suppress
from typing import Any, Dict, Optional

from pydantic import AnyHttpUrl, BaseModel
from pydantic import BaseSettings as _BaseSettings
from pydantic import Field, root_validator

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


class AppSettings(BaseModel):
    database: DatabaseSettings
    collections: CollectionSettings
    environment: EnvironmentSettings


_app_settings = None


def get_app_settings() -> AppSettings:

    global _app_settings

    if _app_settings is None:
        _app_settings = AppSettings(
            database=DatabaseSettings(),
            collections=CollectionSettings(),
            environment=EnvironmentSettings(),
        )

    return _app_settings
