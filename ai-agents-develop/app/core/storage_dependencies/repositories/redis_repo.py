import json
from typing import Any, List, Optional, Type

import redis
import redis.asyncio as async_redis

from app.core.storage_dependencies.repositories.base import (
    BaseRepository,
    BaseSyncRepository,
    T,
)


class RedisRepository(BaseRepository[T]):
    # UPDATED: The client is now an async client
    def __init__(self, client: async_redis.Redis, model_cls: Type[T]):
        self.client = client
        self.model_cls = model_cls
        self.prefix = model_cls.__name__.lower()

    def _get_key(self, id: Any) -> str:
        return f"{self.prefix}:{id}"

    async def get(self, id: Any) -> Optional[T]:
        key = self._get_key(id)
        # UPDATED: The client call is awaited
        raw_data = await self.client.get(key)
        if raw_data is None:
            return None
        return self.model_cls.model_validate(json.loads(raw_data))

    async def get_many(self, ids: List[Any]) -> List[T]:
        keys = [self._get_key(id) for id in ids]
        raw_data = await self.client.mget(keys)
        return [self.model_cls.model_validate(json.loads(d)) for d in raw_data if d]

    async def create(self, model: T) -> T:
        # UPDATED: The update call is now awaited
        return await self.update(model)

    async def update(self, model: T) -> T:
        if not hasattr(model, "id") or model.id is None:
            raise ValueError("Model must have an id to be saved in Redis")
        key = self._get_key(model.id)
        # UPDATED: The client call is awaited
        await self.client.set(key, model.model_dump_json())
        return model

    async def delete(self, id: Any) -> bool:
        key = self._get_key(id)
        # UPDATED: The client call is awaited
        deleted_count = await self.client.delete(key)
        return deleted_count > 0

    async def list(self) -> List[T]:
        """
        WARNING: In production environments, SCAN is an expensive operation.
        This async version iterates without blocking the event loop.
        """
        objects = []
        # UPDATED: Use `async for` with scan_iter
        async for key in self.client.scan_iter(f"{self.prefix}:*"):
            # UPDATED: The get call inside the loop is awaited
            raw_data = await self.client.get(key)
            if raw_data:
                objects.append(self.model_cls.model_validate(json.loads(raw_data)))
        return objects

    async def append_json_field(self, id: Any, field_name: str, data: Any) -> bool:
        """
        Atomically append data to a JSON array field using Redis WATCH + retry.

        Uses Redis WATCH to detect concurrent modifications and retries on conflicts
        to ensure true atomicity without race conditions.

        Args:
            id: Primary key of the record to update
            field_name: Name of the JSON field to append to
            data: Data to append to the JSON array

        Returns:
            True if the update was successful, False if the record was not found
        """
        key = self._get_key(id)
        max_retries = 10

        for attempt in range(max_retries):
            try:
                # Start watching the key for changes
                await self.client.watch(key)

                # Get current data within the watch
                raw_data = await self.client.get(key)
                if raw_data is None:
                    await self.client.unwatch()
                    return False

                # Parse current model
                current_model = self.model_cls.model_validate(json.loads(raw_data))

                # Get current field value
                current_field = getattr(current_model, field_name, [])
                if current_field is None:
                    current_field = []

                # Append new data
                current_field.append(data)
                setattr(current_model, field_name, current_field)

                # Start transaction
                pipe = self.client.pipeline()
                pipe.multi()
                pipe.set(key, current_model.model_dump_json())

                # Execute transaction - this will fail if key was modified
                result = await pipe.execute()

                # If we get here, the transaction succeeded
                return True

            except Exception as e:
                # If it's a WatchError, retry; otherwise re-raise
                if "WATCH" in str(e) or "EXECABORT" in str(e):
                    if attempt < max_retries - 1:
                        # Brief delay before retry
                        import asyncio

                        await asyncio.sleep(0.001 * (attempt + 1))
                        continue
                    else:
                        raise Exception(
                            f"Failed to update after {max_retries} attempts due to concurrent modifications"
                        )
                else:
                    # Other errors, unwatch and re-raise
                    try:
                        await self.client.unwatch()
                    except:
                        pass
                    raise e
        raise RuntimeError(
            "Internal logic error: should have returned or raised an exception."
        )  # raise outside the loop tofix mypy error


class SyncRedisRepository(BaseSyncRepository[T]):
    """A sync generic repository for Redis backends."""

    def __init__(self, client: redis.Redis, model_cls: Type[T]):
        self.client = client
        self.model_cls = model_cls
        self.prefix = model_cls.__name__.lower()

    def _get_key(self, id: Any) -> str:
        return f"{self.prefix}:{id}"

    def get(self, id: Any) -> Optional[T]:
        key = self._get_key(id)
        raw_data = self.client.get(key)
        if raw_data is None:
            return None
        return self.model_cls.model_validate(json.loads(raw_data))

    def get_many(self, ids: List[Any]) -> List[T]:
        keys = [self._get_key(id) for id in ids]
        raw_data = self.client.mget(keys)
        return [self.model_cls.model_validate(json.loads(d)) for d in raw_data if d]

    def create(self, model: T) -> T:
        return self.update(model)

    def update(self, model: T) -> T:
        if not hasattr(model, "id") or model.id is None:
            raise ValueError("Model must have an id to be saved in Redis")
        key = self._get_key(model.id)
        self.client.set(key, model.model_dump_json())
        return model

    def delete(self, id: Any) -> bool:
        key = self._get_key(id)
        deleted_count = self.client.delete(key)
        return deleted_count > 0

    def list(self) -> List[T]:
        """
        WARNING: In production environments, SCAN is an expensive operation.
        This sync version blocks until all keys are retrieved.
        """
        objects = []
        for key in self.client.scan_iter(f"{self.prefix}:*"):
            raw_data = self.client.get(key)
            if raw_data:
                objects.append(self.model_cls.model_validate(json.loads(raw_data)))
        return objects

    def append_json_field(self, id: Any, field_name: str, data: Any) -> bool:
        """
        Atomically append data to a JSON array field using Redis WATCH + retry (sync version).

        Uses Redis WATCH to detect concurrent modifications and retries on conflicts
        to ensure true atomicity without race conditions.

        Args:
            id: Primary key of the record to update
            field_name: Name of the JSON field to append to
            data: Data to append to the JSON array

        Returns:
            True if the update was successful, False if the record was not found
        """
        key = self._get_key(id)
        max_retries = 10

        for attempt in range(max_retries):
            try:
                # Start watching the key for changes
                self.client.watch(key)

                # Get current data within the watch
                raw_data = self.client.get(key)
                if raw_data is None:
                    self.client.unwatch()
                    return False

                # Parse current model
                current_model = self.model_cls.model_validate(json.loads(raw_data))

                # Get current field value
                current_field = getattr(current_model, field_name, [])
                if current_field is None:
                    current_field = []

                # Append new data
                current_field.append(data)
                setattr(current_model, field_name, current_field)

                # Start transaction
                pipe = self.client.pipeline()
                pipe.multi()
                pipe.set(key, current_model.model_dump_json())

                # Execute transaction - this will fail if key was modified
                result = pipe.execute()

                # If we get here, the transaction succeeded
                return True

            except Exception as e:
                # If it's a WatchError, retry; otherwise re-raise
                if "WATCH" in str(e) or "EXECABORT" in str(e):
                    if attempt < max_retries - 1:
                        # Brief delay before retry
                        import time

                        time.sleep(0.001 * (attempt + 1))
                        continue
                    else:
                        raise Exception(
                            f"Failed to update after {max_retries} attempts due to concurrent modifications"
                        )
                else:
                    # Other errors, unwatch and re-raise
                    try:
                        self.client.unwatch()
                    except:
                        pass
                    raise e
        raise RuntimeError(
            "Internal logic error: should have returned or raised an exception."
        )  # raise outside the loop tofix mypy error
