from __future__ import annotations

from typing import Protocol, Type

import redis
import redis.asyncio as async_redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session

from app.core.storage_dependencies.repositories.base import (
    BaseRepository,
    BaseSyncRepository,
    T,
)
from app.core.storage_dependencies.repositories.postgres_repo import (
    PostgresRepository,
    SyncPostgresRepository,
)
from app.core.storage_dependencies.repositories.redis_repo import (
    RedisRepository,
    SyncRedisRepository,
)
from app.core.storage_dependencies.repositories.sqlite_repo import (
    SQLiteRepository,
    SyncSQLiteRepository,
)


# This protocol defines the abstract contract.
# Any class that has a `get_repository` method with this signature will satisfy the contract.
class RepositoryProvider(Protocol):
    """An abstract interface for an object that can provide async repositories."""

    def get_repository(self, model_cls: Type[T]) -> BaseRepository[T]: ...


class SyncRepositoryProvider(Protocol):
    """An abstract interface for an object that can provide sync repositories."""

    def get_repository(self, model_cls: Type[T]) -> BaseSyncRepository[T]: ...


class RedisProvider:
    """A concrete provider for Redis. It fulfills the RepositoryProvider contract."""

    def __init__(self, client: async_redis.Redis):
        self.client = client

    def get_repository(self, model_cls: Type[T]) -> RedisRepository[T]:
        return RedisRepository(self.client, model_cls)


class SyncRedisProvider:
    """A concrete provider for sync Redis. It fulfills the SyncRepositoryProvider contract."""

    def __init__(self, client: redis.Redis):
        self.client = client

    def get_repository(self, model_cls: Type[T]) -> SyncRedisRepository[T]:
        return SyncRedisRepository(self.client, model_cls)


class SQLProvider:
    """A concrete provider for SQL backends. It fulfills the RepositoryProvider contract."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def get_repository(self, model_cls: Type[T]) -> BaseRepository[T]:
        if self.session.bind is None:
            raise ValueError("Session is not bound to any engine")
        backend = self.session.bind.dialect.name
        if backend == "postgresql":
            return PostgresRepository(self.session, model_cls)
        elif backend == "sqlite":
            return SQLiteRepository(self.session, model_cls)
        else:
            raise ValueError(f"Unsupported SQL backend dialect: {backend}")


class SyncSQLProvider:
    """A concrete provider for sync SQL backends. It fulfills the SyncRepositoryProvider contract."""

    def __init__(self, session: Session):
        self.session = session

    def get_repository(self, model_cls: Type[T]) -> BaseSyncRepository[T]:
        if self.session.bind is None:
            raise ValueError("Session is not bound to any engine")
        backend = self.session.bind.dialect.name
        if backend == "postgresql":
            return SyncPostgresRepository(self.session, model_cls)
        elif backend == "sqlite":
            return SyncSQLiteRepository(self.session, model_cls)
        else:
            raise ValueError(f"Unsupported SQL backend dialect: {backend}")
