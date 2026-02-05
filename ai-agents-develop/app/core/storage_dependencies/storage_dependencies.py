from __future__ import annotations

import json
import os
import uuid
from contextlib import asynccontextmanager, contextmanager
from functools import lru_cache
from typing import AsyncGenerator, Generator

import logfire
import redis as sync_redis
import redis.asyncio as redis
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import Session, SQLModel

from app.core.storage_dependencies.repositories.providers import (
    RedisProvider,
    RepositoryProvider,
    SQLProvider,
    SyncRedisProvider,
    SyncRepositoryProvider,
    SyncSQLProvider,
)
from config import STORAGE_BACKEND


# --- Custom JSON Serializer ---
def custom_json_serializer(obj):
    """
    A custom JSON default serializer that handles UUID objects.
    """
    if isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


json_dumps = lambda d: json.dumps(d, default=custom_json_serializer)


@lru_cache
def get_sqlite_engine(url: str):
    """
    Creates and returns a SQLite engine.
    The @lru_cache decorator ensures this function only runs once.
    """
    if not url:
        raise ValueError(
            "SQLITE_DATABASE_URL environment variable must be set for sqlite backend"
        )
    logfire.info(f"Creating new SQLite engine")
    return create_async_engine(
        url, json_serializer=json_dumps, connect_args={"check_same_thread": False}
    )


@lru_cache
def get_postgres_engine(url: str):
    """
    Creates and returns a PostgreSQL engine.
    The @lru_cache decorator ensures this function only runs once.
    """
    if not url:
        raise ValueError(
            "POSTGRES_DATABASE_URL environment variable must be set for postgres backend"
        )
    logfire.info(f"Creating new PostgreSQL engine")
    return create_async_engine(url, json_serializer=json_dumps)


@lru_cache
def get_sync_sqlite_engine(url: str):
    """
    Creates and returns a sync SQLite engine.
    The @lru_cache decorator ensures this function only runs once.
    """
    if url.startswith("sqlite+aiosqlite://"):
        sync_url = url.replace("sqlite+aiosqlite://", "sqlite://")
    else:
        sync_url = url

    if not sync_url:
        raise ValueError(
            "SQLITE_DATABASE_URL environment variable must be set for sqlite backend"
        )
    logfire.info(f"Creating new sync SQLite engine")
    logfire.info(f"Sync URL: {sync_url}")
    return create_engine(
        sync_url, json_serializer=json_dumps, connect_args={"check_same_thread": False}
    )


@lru_cache
def get_sync_postgres_engine(url: str):
    """
    Creates and returns a sync PostgreSQL engine.
    The @lru_cache decorator ensures this function only runs once.
    """
    sync_url = url.replace("postgresql+asyncpg://", "postgresql://")
    if not sync_url:
        raise ValueError(
            "POSTGRES_DATABASE_URL environment variable must be set for postgres backend"
        )
    logfire.info(f"Creating new sync PostgreSQL engine")
    return create_engine(sync_url, json_serializer=json_dumps)


# Redis Client (Redis clients are generally safe to create once as a global object)
@lru_cache
def get_redis_client(url: str) -> redis.Redis:
    """Creates and returns a Redis client."""
    if not url:
        raise ValueError("REDIS_URL environment variable must be set for redis backend")
    logfire.info(f"Creating new Redis client")
    return redis.from_url(url, decode_responses=True)


@lru_cache
def get_sync_redis_client(url: str) -> sync_redis.Redis:
    """Creates and returns a sync Redis client."""
    if not url:
        raise ValueError("REDIS_URL environment variable must be set for redis backend")
    logfire.info(f"Creating new sync Redis client")
    return sync_redis.from_url(url, decode_responses=True)


async def create_db_and_tables(engine):
    """Asynchronously initializes the database and creates tables."""
    logfire.info(f"Asynchronously running create_all for engine: {engine}")
    # THE FIX: Use `engine.connect()` for an async context
    async with engine.connect() as conn:
        # Then use run_sync to run the synchronous create_all method.
        await conn.run_sync(SQLModel.metadata.create_all)
    logfire.info("Tables created successfully.")


def create_sync_db_and_tables(engine):
    """Synchronously initializes the database and creates tables."""
    logfire.info(f"Synchronously running create_all for engine: {engine}")
    SQLModel.metadata.create_all(engine)
    logfire.info("Tables created successfully.")


@contextmanager
def get_session(engine):
    """Provides a SQLAlchemy Session within a context."""
    with Session(engine) as session:
        yield session


@asynccontextmanager
async def get_async_session(engine):
    """Provides an async SQLAlchemy Session within a context."""
    async with AsyncSession(engine) as session:
        yield session


@asynccontextmanager
async def get_provider(
    backend: str = STORAGE_BACKEND,
) -> AsyncGenerator[RepositoryProvider, None]:
    """
    The single, abstract entry point for getting a repository provider.
    This context manager handles all backend-specific setup, including sessions.
    """
    if backend == "redis":
        # TODO: Use Alltrue parameter manager to get the url
        # For Redis, create the provider and yield it directly.
        url = os.getenv("REDIS_URL", "")
        redis_client = get_redis_client(url)
        yield RedisProvider(client=redis_client)

    elif backend in ["postgres", "sqlite"]:
        # For SQL, get the engine and manage the session scope.
        if backend == "postgres":
            # TODO: Use Alltrue parameter manager to get the url
            url = os.getenv("POSTGRES_DATABASE_URL", "")
            engine = get_postgres_engine(url)
        else:
            # TODO: Use Alltrue parameter manager to get the url
            default_url = "sqlite+aiosqlite:///./database.db"
            url = os.getenv("SQLITE_DATABASE_URL", default_url)
            engine = get_sqlite_engine(url)

        # This one-time setup should be here
        logfire.info(f"Initializing {backend} tables (if they don't exist)...")
        await create_db_and_tables(engine)

        async with get_async_session(engine) as session:
            # Create the provider with the live session and yield it.
            # The provider is only valid inside this `with` block.
            yield SQLProvider(session)
    else:
        raise ValueError(f"Unsupported storage backend: {backend}")


@contextmanager
def get_sync_provider(
    backend: str = STORAGE_BACKEND,
) -> Generator[SyncRepositoryProvider, None]:
    """
    The single, abstract entry point for getting a sync repository provider.
    This context manager handles all backend-specific setup, including sessions.
    """
    if backend == "redis":
        # For Redis, create the provider and yield it directly.
        url = os.getenv("REDIS_URL", "")
        redis_client = get_sync_redis_client(url)
        yield SyncRedisProvider(client=redis_client)

    elif backend in ["postgres", "sqlite"]:
        # For SQL, get the engine and manage the session scope.
        if backend == "postgres":
            url = os.getenv("POSTGRES_DATABASE_URL", "")
            engine = get_sync_postgres_engine(url)
        else:
            default_url = "sqlite:///./database.db"
            url = os.getenv("SQLITE_DATABASE_URL", default_url)
            engine = get_sync_sqlite_engine(url)

        # This one-time setup should be here
        logfire.info(f"Initializing {backend} tables (if they don't exist)...")
        create_sync_db_and_tables(engine)

        with get_session(engine) as session:
            # Create the provider with the live session and yield it.
            # The provider is only valid inside this `with` block.
            yield SyncSQLProvider(session)
    else:
        raise ValueError(f"Unsupported storage backend: {backend}")


# --- FastAPI Dependency ---
# FastAPI dependency no need context manager
async def get_provider_dependency() -> AsyncGenerator[RepositoryProvider, None]:
    """
    FastAPI dependency that provides a repository provider.
    """

    async with get_provider(STORAGE_BACKEND) as provider:
        yield provider


def get_sync_provider_dependency() -> Generator[SyncRepositoryProvider, None]:
    """
    Dependency that provides a sync repository provider.
    """

    with get_sync_provider(STORAGE_BACKEND) as provider:
        yield provider
