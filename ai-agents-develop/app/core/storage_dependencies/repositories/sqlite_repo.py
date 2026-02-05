# file: repositories/sqlite_repo.py

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from app.core.storage_dependencies.repositories.base import (
    BaseRepository,
    BaseSyncRepository,
    T,
)


class SQLiteRepository(BaseRepository[T]):
    """
    The repository implementation for SQLite with SQLite-specific JSON operations.
    """

    def __init__(self, session, model_cls):
        self.session = session
        self.model_cls = model_cls

    async def get(self, id: Any):
        return await self.session.get(self.model_cls, id)

    async def get_many(self, ids: list):
        from sqlmodel import select

        statement = select(self.model_cls).where(self.model_cls.id.in_(ids))
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def create(self, model: T) -> T:
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        self.session.expunge(model)
        return model

    async def update(self, model: T) -> T:
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        self.session.expunge(model)
        return model

    async def delete(self, id: Any) -> bool:
        obj = await self.get(id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
            return True
        return False

    async def list(self):
        from sqlmodel import select

        statement = select(self.model_cls)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def append_json_field(self, id: Any, field_name: str, data: Any) -> bool:
        """
        Atomically append data to a JSON array field using SQLite JSON functions.

        Args:
            id: Primary key of the record to update
            field_name: Name of the JSON field to append to
            data: Data to append to the JSON array

        Returns:
            True if the update was successful, False if the record was not found
        """
        try:
            # Convert data to JSON string
            json_data = json.dumps(data)

            # SQLite JSON functions
            append_query = text(
                f"""
                UPDATE {self.model_cls.__tablename__}
                SET {field_name} = CASE
                    WHEN {field_name} IS NULL THEN json_array(json(:data))
                    ELSE json_insert({field_name}, '$[#]', json(:data))
                END,
                updated_at = :updated_at
                WHERE id = :record_id
            """
            )

            result = await self.session.execute(
                append_query,
                {
                    "record_id": str(id),
                    "data": json_data,
                    "updated_at": datetime.now(timezone.utc),
                },
            )

            # Check if any rows were affected
            if result.rowcount == 0:
                return False

            # Commit the transaction
            await self.session.commit()
            return True

        except Exception as e:
            # Rollback on error
            await self.session.rollback()
            raise e


class SyncSQLiteRepository(BaseSyncRepository[T]):
    """
    The sync repository implementation for SQLite with SQLite-specific JSON operations.
    """

    def __init__(self, session, model_cls):
        self.session = session
        self.model_cls = model_cls

    def get(self, id: Any):
        return self.session.get(self.model_cls, id)

    def get_many(self, ids: list):
        from sqlmodel import select

        statement = select(self.model_cls).where(self.model_cls.id.in_(ids))
        result = self.session.exec(statement)
        return result.all()

    def create(self, model: T) -> T:
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        self.session.expunge(model)
        return model

    def update(self, model: T) -> T:
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        self.session.expunge(model)
        return model

    def delete(self, id: Any) -> bool:
        obj = self.get(id)
        if obj:
            self.session.delete(obj)
            self.session.commit()
            return True
        return False

    def list(self):
        from sqlmodel import select

        statement = select(self.model_cls)
        result = self.session.exec(statement)
        return result.all()

    def append_json_field(self, id: Any, field_name: str, data: Any) -> bool:
        """
        Atomically append data to a JSON array field using SQLite JSON functions (sync version).

        Args:
            id: Primary key of the record to update
            field_name: Name of the JSON field to append to
            data: Data to append to the JSON array

        Returns:
            True if the update was successful, False if the record was not found
        """
        try:
            # Convert data to JSON string
            json_data = json.dumps(data)

            # SQLite JSON functions
            append_query = text(
                f"""
                UPDATE {self.model_cls.__tablename__}
                SET {field_name} = CASE
                    WHEN {field_name} IS NULL THEN json_array(json(:data))
                    ELSE json_insert({field_name}, '$[#]', json(:data))
                END,
                updated_at = :updated_at
                WHERE id = :record_id
            """
            )

            result = self.session.execute(
                append_query,
                {
                    "record_id": str(id),
                    "data": json_data,
                    "updated_at": datetime.now(timezone.utc),
                },
            )

            # Check if any rows were affected
            if result.rowcount == 0:
                return False

            # Commit the transaction
            self.session.commit()
            return True

        except Exception as e:
            # Rollback on error
            self.session.rollback()
            raise e
