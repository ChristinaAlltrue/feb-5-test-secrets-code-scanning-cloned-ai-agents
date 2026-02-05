"""SQLAlchemy models for state persistence."""

from __future__ import annotations

from sqlalchemy import Float, Index, Integer, LargeBinary, String, Text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    """Base class for all models."""


class SnapshotModel(Base):
    """SQLAlchemy model for snapshot storage."""

    __tablename__ = "snapshots"

    graph_id: Mapped[str] = mapped_column(String(255), primary_key=True, nullable=False)
    id: Mapped[str] = mapped_column(String(255), primary_key=True, nullable=False)
    seq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    start_ts: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    ts: Mapped[str | None] = mapped_column(Text, nullable=True)
    snapshot_json: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    __table_args__ = (
        Index("idx_snapshots_graph_status", "graph_id", "status"),
        Index("idx_snapshots_graph_kind", "graph_id", "kind"),
        Index("idx_snapshots_graph_seq", "graph_id", "seq"),
    )


class GraphMetaModel(Base):
    """SQLAlchemy model for graph metadata."""

    __tablename__ = "graph_meta"

    graph_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    current_seq: Mapped[int] = mapped_column(Integer, nullable=False)


def create_engine_from_connection(
    connection_string: str | None = None, db_file: str | None = None
) -> Engine:
    """Create SQLAlchemy engine from connection string or file path.

    Args:
        connection_string: Database connection string (e.g., postgresql://user:pass@host/db)
                           If None and db_file provided, creates SQLite connection.
        db_file: Path to SQLite database file (used if connection_string is None)

    Returns:
        Configured SQLAlchemy Engine
    """
    if connection_string:
        # PostgreSQL or other databases via connection string
        return create_engine(connection_string, echo=False)
    elif db_file:
        # SQLite with file path
        # Use StaticPool for SQLite to handle concurrent access better
        return create_engine(
            f"sqlite:///{db_file}",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=False,
        )
    else:
        raise ValueError("Either connection_string or db_file must be provided")


def get_session_factory(engine: Engine) -> sessionmaker:
    """Create a session factory for the given engine."""
    return sessionmaker(bind=engine, expire_on_commit=False)
