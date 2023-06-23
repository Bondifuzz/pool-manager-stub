from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, AsyncIterator, Dict, List, Optional

from pool_manager.app.database.orm import (
    ORMNodeGroup,
    ORMOperation,
    ORMPool,
    ORMPoolHealth,
    Paginator,
)
from pool_manager.app.util.developer import testing_only

if TYPE_CHECKING:
    from pool_manager.app.settings import AppSettings


class IUnsentMessages(metaclass=ABCMeta):

    """
    Used for saving/loading MQ unsent messages from database.
    """

    @abstractmethod
    async def save_unsent_messages(self, messages: Dict[str, list]):
        pass

    @abstractmethod
    async def load_unsent_messages(self) -> Dict[str, list]:
        pass


class IPools(metaclass=ABCMeta):

    """
    Resource pools
    """

    @abstractmethod
    async def create(
        self,
        name: str,
        description: str,
        user_id: Optional[str],
        exp_date: Optional[str],
        node_group: ORMNodeGroup,
        yc_node_group_id: Optional[str],
        operation: Optional[ORMOperation],
        health: ORMPoolHealth,
        created_at: str,
    ) -> ORMPool:
        pass

    @abstractmethod
    async def get_by_id(self, pool_id: str) -> ORMPool:
        pass

    @abstractmethod
    async def get_by_name(self, pool_name: str, user_id: str) -> ORMPool:
        pass

    @abstractmethod
    async def update(self, pool: ORMPool):
        pass

    @abstractmethod
    async def update_partial(self, pool_id: str, **kwargs):
        pass

    @abstractmethod
    async def delete(self, pool_id: str):
        pass

    @abstractmethod
    async def count_available(self, user_id: str) -> int:
        pass

    @abstractmethod
    async def list_available(self, paginator: Paginator, user_id: str) -> List[ORMPool]:
        pass

    @abstractmethod
    async def count(
        self,
        user_id: Optional[str] = None,
    ) -> int:
        pass

    @abstractmethod
    async def list(
        self,
        paginator: Paginator,
        user_id: Optional[str] = None,
    ) -> List[ORMPool]:
        pass

    @abstractmethod
    async def list_internal(self) -> AsyncIterator[ORMPool]:
        pass

    @abstractmethod
    async def list_expired(self) -> AsyncIterator[ORMPool]:
        pass

    @abstractmethod
    async def list_operations_in_progress(self) -> AsyncIterator[ORMPool]:
        pass

    @abstractmethod
    async def list_operations_scheduled(self) -> AsyncIterator[ORMPool]:
        pass

    @abstractmethod
    async def list_no_operations(self) -> AsyncIterator[ORMPool]:
        pass


class IDatabase(metaclass=ABCMeta):

    """Used for managing database"""

    @staticmethod
    @abstractmethod
    async def create(cls, settings: AppSettings):
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

    @property
    @abstractmethod
    def unsent_mq(self) -> IUnsentMessages:
        pass

    @property
    @abstractmethod
    def pools(self) -> IPools:
        pass

    @abstractmethod
    @testing_only
    async def truncate_all_collections(self) -> None:
        pass
