import uuid
from typing import Optional

from sqlalchemy import Column, ForeignKey, String, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from config import IS_SQLITE


class GUID(TypeDecorator):
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """
        Called before a value is sent to the database.
        """
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)

        try:
            return str(uuid.UUID(value))  # force convert
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid UUID: {value}") from e

    def process_result_value(self, value, dialect):
        """
        Called after a value is retrieved from the database.
        """
        if value is None:
            return None
        try:
            return uuid.UUID(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid UUID: {value}") from e


def uuid_column(
    *,
    foreign_key: Optional[str] = None,
    primary_key: bool = False,
    nullable: bool = False,
):
    """
    Platform-independent UUID type.
    SQLite uses a string column, Postgres uses a UUID column.
    """
    column_type = GUID() if IS_SQLITE else PG_UUID(as_uuid=True)

    kwargs = {
        "primary_key": primary_key,
        "nullable": nullable,
    }

    if foreign_key:
        return Column(column_type, ForeignKey(foreign_key), **kwargs)
    else:
        return Column(column_type, **kwargs)
