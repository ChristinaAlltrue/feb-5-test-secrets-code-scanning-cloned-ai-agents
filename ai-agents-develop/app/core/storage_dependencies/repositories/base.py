from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, TypeVar

from sqlmodel import SQLModel

# T is a type variable that must be SQLModel or its subclass
T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T], ABC):
    """
    Abstract base class (interface) for a generic repository (Async Version).
    """

    @abstractmethod
    async def get(self, id: Any) -> Optional[T]:
        """Asynchronously retrieve an object by its primary key."""

    @abstractmethod
    async def get_many(self, ids: List[Any]) -> List[T]:
        """Asynchronously retrieve multiple objects by their primary keys."""

    @abstractmethod
    async def create(self, model: T) -> T:
        """Asynchronously create a new object."""

    @abstractmethod
    async def update(self, model: T) -> T:
        """Asynchronously update an existing object."""

    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """Asynchronously delete an object by its primary key, return True if successful."""

    @abstractmethod
    async def list(self) -> List[T]:
        """Asynchronously list all objects."""

    @abstractmethod
    async def append_json_field(self, id: Any, field_name: str, data: Any) -> bool:
        """Atomically append data to a JSON array field to prevent race conditions."""


class BaseSyncRepository(Generic[T], ABC):
    """
    Abstract base class (interface) for a generic repository (Sync Version).
    """

    @abstractmethod
    def get(self, id: Any) -> Optional[T]:
        """Synchronously retrieve an object by its primary key."""

    @abstractmethod
    def get_many(self, ids: List[Any]) -> List[T]:
        """Synchronously retrieve multiple objects by their primary keys."""

    @abstractmethod
    def create(self, model: T) -> T:
        """Synchronously create a new object."""

    @abstractmethod
    def update(self, model: T) -> T:
        """Synchronously update an existing object."""

    @abstractmethod
    def delete(self, id: Any) -> bool:
        """Synchronously delete an object by its primary key, return True if successful."""

    @abstractmethod
    def list(self) -> List[T]:
        """Synchronously list all objects."""

    @abstractmethod
    def append_json_field(self, id: Any, field_name: str, data: Any) -> bool:
        """Atomically append data to a JSON array field to prevent race conditions (sync version)."""
