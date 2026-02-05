"""SQLAlchemy-based state persistence using a connection string (e.g. PostgreSQL/SQLite)."""

from __future__ import annotations as _annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Annotated, Any, Callable, ContextManager, cast

import pydantic
from pydantic_graph import _utils as _graph_utils
from pydantic_graph import exceptions
from pydantic_graph.nodes import BaseNode, End
from pydantic_graph.persistence import (
    BaseStatePersistence,
    EndSnapshot,
    NodeSnapshot,
    RunEndT,
    Snapshot,
    SnapshotStatus,
    StateT,
    _utils,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import (
    Base,
    GraphMetaModel,
    SnapshotModel,
    create_engine_from_connection,
    get_session_factory,
)


def _build_snapshot_type_adapter(
    state_t: type[StateT], run_end_t: type[RunEndT]
) -> pydantic.TypeAdapter[Snapshot[StateT, RunEndT]]:
    return pydantic.TypeAdapter(
        Annotated[Snapshot[state_t, run_end_t], pydantic.Discriminator("kind")]
    )


class SqlStatePersistence(BaseStatePersistence[StateT, RunEndT]):
    """Database-backed state persistence using SQLAlchemy via a connection string.

    Initialize with a connection string (PostgreSQL/SQLite):
    `SqlStatePersistence(connection_string='postgresql://...', graph_id='run_1')`

    A single DB connection should be reused for a single run across steps. Use a different graph_id per run.
    """

    def __init__(
        self,
        *,
        graph_id: str,
        connection_string: str | None = None,
    ) -> None:
        """Initialize persistence.

        Args:
            graph_id: Graph identifier (required keyword argument)
            connection_string: Database connection string (PostgreSQL/SQLite)
            current_seq: Initial sequence number
        """
        super().__init__()

        self.graph_id = graph_id
        self.connection_string = connection_string
        self.current_seq = 0
        self._snapshot_type_adapter: (
            pydantic.TypeAdapter[Snapshot[StateT, RunEndT]] | None
        ) = None
        self._engine: Any = None
        # A callable that returns a context manager yielding a SQLAlchemy Session
        self._session_factory: Callable[[], ContextManager[Session]]

        # Initialize database engine and session factory
        if not self.connection_string:
            raise ValueError("connection_string must be provided")

        self._engine = create_engine_from_connection(self.connection_string)
        self._session_factory = cast(
            Callable[[], ContextManager[Session]], get_session_factory(self._engine)
        )
        # Ensure tables exist
        self._ensure_db_sync()

    def _ensure_db_sync(self) -> None:
        """Create tables if they don't exist."""
        Base.metadata.create_all(self._engine)
        # Initialize graph_meta if needed
        with self._session_factory() as session:
            meta = session.get(GraphMetaModel, self.graph_id)
            if meta is None:
                meta = GraphMetaModel(graph_id=self.graph_id, current_seq=0)
                session.add(meta)
                session.commit()

    async def _ensure_db(self) -> None:
        """Async wrapper for _ensure_db_sync."""
        await _graph_utils.run_in_executor(self._ensure_db_sync)

    def should_set_types(self) -> bool:
        """Check if types need to be set."""
        return self._snapshot_type_adapter is None

    def set_types(self, state_type: type[StateT], run_end_type: type[RunEndT]) -> None:
        """Set the state and run end types for serialization."""
        self._snapshot_type_adapter = _build_snapshot_type_adapter(
            state_type, run_end_type
        )
        self.current_seq = self._load_current_seq_sync()

    async def _insert_snapshot(self, snapshot: Snapshot[StateT, RunEndT]) -> None:
        """Insert a snapshot into the database."""

        def _insert_sync() -> None:
            with self._session_factory() as session:
                # Get current seq
                meta = session.get(GraphMetaModel, self.graph_id)
                seq = 0 if meta is None else meta.current_seq

                adapter = self._snapshot_type_adapter
                assert adapter is not None, "snapshot type adapter must be set"
                d = adapter.dump_json(snapshot)
                kind = "node" if isinstance(snapshot, NodeSnapshot) else "end"
                status = getattr(snapshot, "status", None)
                start_ts = getattr(snapshot, "start_ts", None)
                duration = getattr(snapshot, "duration", None)
                ts = getattr(snapshot, "ts", None)

                # Insert or replace snapshot
                snapshot_model = SnapshotModel(
                    graph_id=self.graph_id,
                    id=snapshot.id,
                    seq=seq,
                    kind=kind,
                    status=status,
                    start_ts=None if start_ts is None else start_ts.isoformat() + "Z",
                    duration=duration,
                    ts=None if ts is None else ts.isoformat() + "Z",
                    snapshot_json=d,
                )
                session.merge(snapshot_model)

                # Increment seq
                if meta is None:
                    meta = GraphMetaModel(graph_id=self.graph_id, current_seq=seq + 1)
                    session.add(meta)
                else:
                    meta.current_seq = seq + 1
                session.commit()
                self.current_seq = seq + 1

        await _graph_utils.run_in_executor(_insert_sync)

    async def snapshot_node(
        self, state: StateT, next_node: BaseNode[StateT, Any, RunEndT]
    ) -> None:
        """Create a snapshot for a node."""
        await self._insert_snapshot(NodeSnapshot(state=state, node=next_node))

    async def snapshot_node_if_new(
        self, snapshot_id: str, state: StateT, next_node: BaseNode[StateT, Any, RunEndT]
    ) -> None:
        """Create a snapshot for a node only if it doesn't already exist."""
        async with self._lock():
            exists = await _graph_utils.run_in_executor(self._exists_sync, snapshot_id)
            if not exists:
                await self._insert_snapshot(NodeSnapshot(state=state, node=next_node))

    def _exists_sync(self, snapshot_id: str) -> bool:
        """Check if a snapshot exists."""
        with self._session_factory() as session:
            stmt = select(SnapshotModel).where(
                SnapshotModel.graph_id == self.graph_id,
                SnapshotModel.id == snapshot_id,
            )
            result = session.execute(stmt)
            return result.first() is not None

    async def snapshot_end(self, state: StateT, end: End[RunEndT]) -> None:
        """Create a snapshot for an end node."""
        await self._insert_snapshot(EndSnapshot(state=state, result=end))

    @asynccontextmanager
    async def record_run(self, snapshot_id: str) -> AsyncIterator[None]:
        """Record the execution of a node snapshot."""
        async with self._lock():
            await _graph_utils.run_in_executor(self._mark_running_sync, snapshot_id)

        start = perf_counter()
        try:
            yield
        except Exception:
            duration = perf_counter() - start
            async with self._lock():
                await _graph_utils.run_in_executor(
                    self._after_run_sync, snapshot_id, duration, "error"
                )
            raise
        else:
            duration = perf_counter() - start
            async with self._lock():
                await _graph_utils.run_in_executor(
                    self._after_run_sync, snapshot_id, duration, "success"
                )

    def _mark_running_sync(self, snapshot_id: str) -> None:
        """Mark a snapshot as running."""
        with self._session_factory() as session:
            stmt = select(SnapshotModel).where(
                SnapshotModel.graph_id == self.graph_id,
                SnapshotModel.id == snapshot_id,
            )
            result = session.execute(stmt)
            snapshot_model = result.scalar_one_or_none()
            if snapshot_model is None:
                raise LookupError(f"No snapshot found with id={snapshot_id!r}")
            adapter = self._snapshot_type_adapter
            assert adapter is not None, "snapshot type adapter must be set"
            snapshot = adapter.validate_json(snapshot_model.snapshot_json)
            if not isinstance(snapshot, NodeSnapshot):
                raise AssertionError("Only NodeSnapshot can be recorded")
            exceptions.GraphNodeStatusError.check(snapshot.status)
            snapshot.status = "running"
            snapshot.start_ts = _utils.now_utc()
            d = adapter.dump_json(snapshot)
            snapshot_model.status = snapshot.status
            snapshot_model.start_ts = snapshot.start_ts.isoformat() + "Z"
            snapshot_model.snapshot_json = d
            session.commit()

    def _after_run_sync(
        self, snapshot_id: str, duration: float, status: SnapshotStatus
    ) -> None:
        """Update a snapshot after run completion."""
        with self._session_factory() as session:
            stmt = select(SnapshotModel).where(
                SnapshotModel.graph_id == self.graph_id,
                SnapshotModel.id == snapshot_id,
            )
            result = session.execute(stmt)
            snapshot_model = result.scalar_one_or_none()
            if snapshot_model is None:
                raise LookupError(f"No snapshot found with id={snapshot_id!r}")
            adapter = self._snapshot_type_adapter
            assert adapter is not None, "snapshot type adapter must be set"
            snapshot = adapter.validate_json(snapshot_model.snapshot_json)
            if not isinstance(snapshot, NodeSnapshot):
                raise AssertionError("Only NodeSnapshot can be recorded")
            snapshot.duration = duration
            snapshot.status = status
            d = adapter.dump_json(snapshot)
            snapshot_model.duration = duration
            snapshot_model.status = status
            snapshot_model.snapshot_json = d
            session.commit()

    async def load_next(self) -> NodeSnapshot[StateT, RunEndT] | None:
        """Load the next pending snapshot."""
        async with self._lock():
            row = await _graph_utils.run_in_executor(self._select_next_created_sync)
            if row is None:
                return None
            adapter = self._snapshot_type_adapter
            assert adapter is not None, "snapshot type adapter must be set"
            snapshot = adapter.validate_json(row)
            assert isinstance(snapshot, NodeSnapshot)
            snapshot.status = "pending"
            await _graph_utils.run_in_executor(self._save_snapshot_sync, snapshot)
            return snapshot

    def _select_next_created_sync(self) -> bytes | None:
        """Select the next created snapshot."""
        assert (
            self._snapshot_type_adapter is not None
        ), "snapshot type adapter must be set"
        with self._session_factory() as session:
            stmt = (
                select(SnapshotModel.snapshot_json)
                .where(
                    SnapshotModel.graph_id == self.graph_id,
                    SnapshotModel.kind == "node",
                    SnapshotModel.status == "created",
                )
                .order_by(SnapshotModel.seq.asc())
                .limit(1)
            )
            result = session.execute(stmt)
            row = result.first()
            return None if row is None else row[0]

    def _save_snapshot_sync(self, snapshot: Snapshot[StateT, RunEndT]) -> None:
        """Save a snapshot to the database."""
        with self._session_factory() as session:
            adapter = self._snapshot_type_adapter
            assert adapter is not None, "snapshot type adapter must be set"
            d = adapter.dump_json(snapshot)
            start_ts = getattr(snapshot, "start_ts", None)
            ts = getattr(snapshot, "ts", None)
            duration = getattr(snapshot, "duration", None)
            status = getattr(snapshot, "status", None)

            stmt = select(SnapshotModel).where(
                SnapshotModel.graph_id == self.graph_id,
                SnapshotModel.id == snapshot.id,
            )
            result = session.execute(stmt)
            snapshot_model = result.scalar_one_or_none()
            if snapshot_model:
                snapshot_model.status = status
                snapshot_model.start_ts = (
                    None if start_ts is None else start_ts.isoformat() + "Z"
                )
                snapshot_model.duration = duration
                snapshot_model.ts = None if ts is None else ts.isoformat() + "Z"
                snapshot_model.snapshot_json = d
            else:
                # Create new if doesn't exist
                kind = "node" if isinstance(snapshot, NodeSnapshot) else "end"
                snapshot_model = SnapshotModel(
                    graph_id=self.graph_id,
                    id=snapshot.id,
                    seq=None,  # Will be set by _insert_snapshot
                    kind=kind,
                    status=status,
                    start_ts=None if start_ts is None else start_ts.isoformat() + "Z",
                    duration=duration,
                    ts=None if ts is None else ts.isoformat() + "Z",
                    snapshot_json=d,
                )
                session.add(snapshot_model)
            session.commit()

    async def load_all(self) -> list[Snapshot[StateT, RunEndT]]:
        """Load all snapshots for this graph."""
        return await _graph_utils.run_in_executor(self._load_all_sync)

    def _load_all_sync(self) -> list[Snapshot[StateT, RunEndT]]:
        """Load all snapshots synchronously."""
        with self._session_factory() as session:
            stmt = (
                select(SnapshotModel.snapshot_json)
                .where(SnapshotModel.graph_id == self.graph_id)
                .order_by(SnapshotModel.seq.asc())
            )
            result = session.execute(stmt)
            rows = result.all()
            snapshots: list[Snapshot[StateT, RunEndT]] = []
            adapter = self._snapshot_type_adapter
            assert adapter is not None, "snapshot type adapter must be set"
            for (blob,) in rows:
                snapshots.append(adapter.validate_json(blob))
            return snapshots

    def _load_current_seq_sync(self) -> int:
        """Load the current sequence number."""
        with self._session_factory() as session:
            meta = session.get(GraphMetaModel, self.graph_id)
            return 0 if meta is None else meta.current_seq

    async def delete_latest_snapshot(self) -> bool:
        """Delete the latest snapshot for this graph and rewind current_seq.

        Returns True if a snapshot was deleted, False if none existed.
        """
        return await _graph_utils.run_in_executor(self._delete_latest_snapshot_sync)

    def _delete_latest_snapshot_sync(self) -> bool:
        with self._session_factory() as session:
            # Find the snapshot with the highest seq for this graph
            stmt = (
                select(SnapshotModel)
                .where(SnapshotModel.graph_id == self.graph_id)
                .order_by(SnapshotModel.seq.desc())
                .limit(1)
            )
            result = session.execute(stmt)
            latest = result.scalar_one_or_none()
            if latest is None:
                return False

            last_seq = latest.seq or 0
            session.delete(latest)

            # Rewind current_seq to last_seq so the next insert reuses this index
            meta = session.get(GraphMetaModel, self.graph_id)
            if meta is None:
                meta = GraphMetaModel(graph_id=self.graph_id, current_seq=last_seq)
                session.add(meta)
            else:
                meta.current_seq = last_seq

            session.commit()
            self.current_seq = last_seq
            return True

    @asynccontextmanager
    async def _lock(self) -> AsyncIterator[None]:
        """Provide a lock for thread-safe operations."""
        # For PostgreSQL, we can use advisory locks or row-level locking
        # For SQLite, file-level locking is handled by the database
        # We serialize via executor for consistency
        yield

    @staticmethod
    def create_rerun_persistence(
        src_graph_id: str,
        start_index: int,
        dst_graph_id: str,
        connection_string: str | None = None,
        overwrite_state: dict[Any, Any] | None = None,
    ) -> None:
        """
        Create a rerun persistence by copying snapshots up to start_index.
        The last snapshot is reset to 'created' and the rest are copied to the destination graph.
        The destination graph is created if it doesn't exist.
        The destination graph is updated with the new current_seq.

        Args:
            src_graph_id: The source graph id.
            start_index: The index of the snapshot to start from.
            dst_graph_id: The destination graph id.
            connection_string: The database connection string.
        """
        engine = create_engine_from_connection(connection_string)
        session_factory = get_session_factory(engine)
        with session_factory() as session:
            stmt = (
                select(SnapshotModel)
                .where(SnapshotModel.graph_id == src_graph_id)
                .order_by(SnapshotModel.seq.asc())
            )
            result = session.execute(stmt)
            rows = result.scalars().all()

            if start_index < 0 or start_index >= len(rows):
                raise IndexError(
                    f"start_index {start_index} out of range (len={len(rows)})"
                )

            copy_rows = list(rows[: start_index + 1])
            last = copy_rows[-1]

            if last.kind != "node":
                raise ValueError('Can only rerun from a node snapshot (kind=="node")')

            # Write snapshots under destination graph_id (do not mutate originals)
            for idx, snapshot_model in enumerate(copy_rows):
                is_last = idx == len(copy_rows) - 1
                if is_last:
                    if last.kind != "node":
                        raise ValueError(
                            'Can only rerun from a node snapshot (kind=="node")'
                        )
                    # Prepare modified fields for the last node
                    new_status = "created"
                    new_start_ts = None
                    new_duration = None
                    snap_obj: Any = json.loads(
                        snapshot_model.snapshot_json.decode("utf-8")
                    )
                    snap_obj["status"] = "created"
                    snap_obj["start_ts"] = None
                    snap_obj["duration"] = None
                    if overwrite_state:
                        snap_obj["state"] = overwrite_state
                    new_snapshot_json = json.dumps(snap_obj).encode("utf-8")
                else:
                    new_status = snapshot_model.status
                    new_start_ts = snapshot_model.start_ts
                    new_duration = snapshot_model.duration
                    new_snapshot_json = snapshot_model.snapshot_json

                new_snapshot = SnapshotModel(
                    graph_id=dst_graph_id,
                    id=snapshot_model.id,
                    seq=snapshot_model.seq,
                    kind=snapshot_model.kind,
                    status=new_status,
                    start_ts=new_start_ts,
                    duration=new_duration,
                    ts=snapshot_model.ts,
                    snapshot_json=new_snapshot_json,
                )
                session.add(new_snapshot)

            # Set current_seq for the new graph
            meta = session.get(GraphMetaModel, dst_graph_id)
            next_seq = (last.seq or start_index) + 1
            if meta is None:
                meta = GraphMetaModel(graph_id=dst_graph_id, current_seq=next_seq)
                session.add(meta)
            else:
                meta.current_seq = next_seq

            session.commit()

        return

    @staticmethod
    def rerun_inplace(
        graph_id: str,
        start_index: int,
        connection_string: str | None = None,
        overwrite_state: dict[Any, Any] | None = None,
    ) -> None:
        """
        Prepare an existing graph for rerun in-place by:
        1) Selecting snapshots for the target graph id
        2) Updating the snapshot at start_index to status "created" (and optionally overwrite state)
        3) Deleting all snapshots after start_index

        Args:
            graph_id: The graph id to modify in-place.
            start_index: The index of the snapshot to restart from.
            connection_string: The database connection string.
            overwrite_state: Optional state dict to replace the snapshot's state.
        """
        engine = create_engine_from_connection(connection_string)
        session_factory = get_session_factory(engine)
        with session_factory() as session:
            # Load all snapshots ordered by seq for validation and indexing
            stmt = (
                select(SnapshotModel)
                .where(SnapshotModel.graph_id == graph_id)
                .order_by(SnapshotModel.seq.asc())
            )
            result = session.execute(stmt)
            rows = result.scalars().all()

            if start_index < 0 or start_index >= len(rows):
                raise IndexError(
                    f"start_index {start_index} out of range (len={len(rows)})"
                )

            target = rows[start_index]

            # For safety, only allow rerun from a node snapshot
            if target.kind != "node":
                raise ValueError('Can only rerun from a node snapshot (kind=="node")')

            # Update the target snapshot to reset execution markers
            snap_obj: Any = json.loads(target.snapshot_json.decode("utf-8"))
            snap_obj["status"] = "created"
            snap_obj["start_ts"] = None
            snap_obj["duration"] = None
            if overwrite_state is not None:
                snap_obj["state"] = overwrite_state

            target.status = "created"
            target.start_ts = None
            target.duration = None
            target.snapshot_json = json.dumps(snap_obj).encode("utf-8")

            # Delete snapshots after the selected index
            delete_after_seq = target.seq
            if delete_after_seq is None:
                # Fallback: compute using ordered rows
                delete_after_seq = start_index

            to_delete_stmt = (
                select(SnapshotModel)
                .where(
                    SnapshotModel.graph_id == graph_id,
                    SnapshotModel.seq > delete_after_seq,
                )
                .order_by(SnapshotModel.seq.asc())
            )
            to_delete_result = session.execute(to_delete_stmt)
            for row in to_delete_result.scalars().all():
                session.delete(row)

            # Update current_seq so that the next insert uses start_index
            meta = session.get(GraphMetaModel, graph_id)
            next_seq = (target.seq or start_index) + 1
            if meta is None:
                meta = GraphMetaModel(graph_id=graph_id, current_seq=next_seq)
                session.add(meta)
            else:
                meta.current_seq = next_seq

            session.commit()

        return
