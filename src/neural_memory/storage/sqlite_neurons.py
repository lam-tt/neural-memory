"""SQLite neuron and neuron state operations mixin."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import TYPE_CHECKING, Any

from neural_memory.core.neuron import Neuron, NeuronState, NeuronType
from neural_memory.storage.sqlite_row_mappers import row_to_neuron, row_to_neuron_state

if TYPE_CHECKING:
    import aiosqlite


class SQLiteNeuronMixin:
    """Mixin providing neuron and neuron state CRUD operations."""

    def _ensure_conn(self) -> aiosqlite.Connection: ...
    def _get_brain_id(self) -> str: ...

    # ========== Neuron Operations ==========

    async def add_neuron(self, neuron: Neuron) -> str:
        conn = self._ensure_conn()
        brain_id = self._get_brain_id()

        try:
            await conn.execute(
                """INSERT INTO neurons (id, brain_id, type, content, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    neuron.id,
                    brain_id,
                    neuron.type.value,
                    neuron.content,
                    json.dumps(neuron.metadata),
                    neuron.created_at.isoformat(),
                ),
            )

            # Initialize state
            await conn.execute(
                """INSERT INTO neuron_states (neuron_id, brain_id, created_at)
                   VALUES (?, ?, ?)""",
                (neuron.id, brain_id, datetime.utcnow().isoformat()),
            )

            await conn.commit()
            return neuron.id
        except sqlite3.IntegrityError:
            raise ValueError(f"Neuron {neuron.id} already exists")

    async def get_neuron(self, neuron_id: str) -> Neuron | None:
        conn = self._ensure_conn()
        brain_id = self._get_brain_id()

        async with conn.execute(
            "SELECT * FROM neurons WHERE id = ? AND brain_id = ?",
            (neuron_id, brain_id),
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return row_to_neuron(row)

    async def find_neurons(
        self,
        type: NeuronType | None = None,
        content_contains: str | None = None,
        content_exact: str | None = None,
        time_range: tuple[datetime, datetime] | None = None,
        limit: int = 100,
    ) -> list[Neuron]:
        conn = self._ensure_conn()
        brain_id = self._get_brain_id()

        query = "SELECT * FROM neurons WHERE brain_id = ?"
        params: list[Any] = [brain_id]

        if type is not None:
            query += " AND type = ?"
            params.append(type.value)

        if content_contains is not None:
            query += " AND content LIKE ?"
            params.append(f"%{content_contains}%")

        if content_exact is not None:
            query += " AND content = ?"
            params.append(content_exact)

        if time_range is not None:
            start, end = time_range
            query += " AND created_at >= ? AND created_at <= ?"
            params.append(start.isoformat())
            params.append(end.isoformat())

        query += " LIMIT ?"
        params.append(limit)

        async with conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [row_to_neuron(row) for row in rows]

    async def update_neuron(self, neuron: Neuron) -> None:
        conn = self._ensure_conn()
        brain_id = self._get_brain_id()

        cursor = await conn.execute(
            """UPDATE neurons SET type = ?, content = ?, metadata = ?
               WHERE id = ? AND brain_id = ?""",
            (
                neuron.type.value,
                neuron.content,
                json.dumps(neuron.metadata),
                neuron.id,
                brain_id,
            ),
        )

        if cursor.rowcount == 0:
            raise ValueError(f"Neuron {neuron.id} does not exist")

        await conn.commit()

    async def delete_neuron(self, neuron_id: str) -> bool:
        conn = self._ensure_conn()
        brain_id = self._get_brain_id()

        cursor = await conn.execute(
            "DELETE FROM neurons WHERE id = ? AND brain_id = ?",
            (neuron_id, brain_id),
        )
        await conn.commit()

        return cursor.rowcount > 0

    # ========== Neuron State Operations ==========

    async def get_neuron_state(self, neuron_id: str) -> NeuronState | None:
        conn = self._ensure_conn()
        brain_id = self._get_brain_id()

        async with conn.execute(
            "SELECT * FROM neuron_states WHERE neuron_id = ? AND brain_id = ?",
            (neuron_id, brain_id),
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return row_to_neuron_state(row)

    async def update_neuron_state(self, state: NeuronState) -> None:
        conn = self._ensure_conn()
        brain_id = self._get_brain_id()

        await conn.execute(
            """INSERT OR REPLACE INTO neuron_states
               (neuron_id, brain_id, activation_level, access_frequency,
                last_activated, decay_rate, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                state.neuron_id,
                brain_id,
                state.activation_level,
                state.access_frequency,
                state.last_activated.isoformat() if state.last_activated else None,
                state.decay_rate,
                state.created_at.isoformat(),
            ),
        )
        await conn.commit()

    async def get_all_neuron_states(self) -> list[NeuronState]:
        """Get all neuron states for current brain."""
        conn = self._ensure_conn()
        brain_id = self._get_brain_id()

        async with conn.execute(
            "SELECT * FROM neuron_states WHERE brain_id = ?",
            (brain_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [row_to_neuron_state(row) for row in rows]
