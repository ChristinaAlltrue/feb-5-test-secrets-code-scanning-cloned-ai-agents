import json
from datetime import datetime, timezone
from typing import Any, List, Optional, Type

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session, select

from app.core.storage_dependencies.repositories.base import (
    BaseRepository,
    BaseSyncRepository,
    T,
)


class PostgresRepository(BaseRepository[T]):
    """
    An async generic repository for SQL-based backends using SQLModel.
    """

    # UPDATED: The session is now an AsyncSession
    def __init__(self, session: AsyncSession, model_cls: Type[T]):
        self.session = session
        self.model_cls = model_cls

    async def get(self, id: Any) -> Optional[T]:

        return await self.session.get(self.model_cls, id)

    async def get_many(self, ids: List[Any]) -> List[T]:
        statement = select(self.model_cls).where(self.model_cls.id.in_(ids))
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def create(self, model: T) -> T:
        # 1. Add the object to the session
        self.session.add(model)
        # 2. Commit to save it to the database
        await self.session.commit()
        # 3. Refresh to load any database-defaults and get the final state
        await self.session.refresh(model)
        # 4. Expunge the object from the session. This is the crucial step.
        # It detaches the object, preventing any future lazy-loading attempts.
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

    async def list(self) -> List[T]:
        statement = select(self.model_cls)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def append_json_field(self, id: Any, field_name: str, data: Any) -> bool:
        """
        Atomically append data to a JSON array field to prevent race conditions.

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

            # PostgreSQL JSON functions - cast to jsonb to parse the JSON string
            append_query = text(
                f"""
                UPDATE {self.model_cls.__tablename__}
                SET {field_name} = CASE
                    WHEN {field_name} IS NULL THEN jsonb_build_array(:data::jsonb)
                    ELSE {field_name} || jsonb_build_array(:data::jsonb)
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


class SyncPostgresRepository(BaseSyncRepository[T]):
    """
    A sync generic repository for SQL-based backends using SQLModel.
    """

    def __init__(self, session: Session, model_cls: Type[T]):
        self.session = session
        self.model_cls = model_cls

    def get(self, id: Any) -> Optional[T]:
        return self.session.get(self.model_cls, id)

    def get_many(self, ids: List[Any]) -> List[T]:
        statement = select(self.model_cls).where(self.model_cls.id.in_(ids))
        result = self.session.exec(statement)
        return result.all()

    def create(self, model: T) -> T:
        # 1. Add the object to the session
        self.session.add(model)
        # 2. Commit to save it to the database
        self.session.commit()
        # 3. Refresh to load any database-defaults and get the final state
        self.session.refresh(model)
        # 4. Expunge the object from the session
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

    def list(self) -> List[T]:
        statement = select(self.model_cls)
        result = self.session.exec(statement)
        return result.all()

    def append_json_field(self, id: Any, field_name: str, data: Any) -> bool:
        """
        Atomically append data to a JSON array field to prevent race conditions (sync version).

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

            # PostgreSQL JSON functions - cast to jsonb to parse the JSON string
            append_query = text(
                f"""
                UPDATE {self.model_cls.__tablename__}
                SET {field_name} = CASE
                    WHEN {field_name} IS NULL THEN jsonb_build_array(:data::jsonb)
                    ELSE {field_name} || jsonb_build_array(:data::jsonb)
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
