"""Fiber data structures - memory clusters of related neurons."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass
class Fiber:
    """
    A fiber represents a memory cluster - a subgraph of related neurons.

    Fibers bundle together neurons and synapses that form a coherent
    memory or concept. They act as retrieval units and can be
    compressed into summaries over time.

    Attributes:
        id: Unique identifier
        neuron_ids: Set of neuron IDs in this fiber
        synapse_ids: Set of synapse IDs connecting neurons in this fiber
        anchor_neuron_id: Primary entry point neuron for this fiber
        time_start: Earliest timestamp in this memory
        time_end: Latest timestamp in this memory
        coherence: How tightly connected the neurons are (0.0 - 1.0)
        salience: Importance/relevance score (0.0 - 1.0)
        frequency: Number of times this fiber has been accessed
        summary: Optional compressed text summary
        tags: Optional tags for categorization
        metadata: Additional fiber-specific data
        created_at: When this fiber was created
    """

    id: str
    neuron_ids: set[str]
    synapse_ids: set[str]
    anchor_neuron_id: str
    time_start: datetime | None = None
    time_end: datetime | None = None
    coherence: float = 0.0
    salience: float = 0.0
    frequency: int = 0
    summary: str | None = None
    tags: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        neuron_ids: set[str],
        synapse_ids: set[str],
        anchor_neuron_id: str,
        time_start: datetime | None = None,
        time_end: datetime | None = None,
        summary: str | None = None,
        tags: set[str] | None = None,
        metadata: dict[str, Any] | None = None,
        fiber_id: str | None = None,
    ) -> Fiber:
        """
        Factory method to create a new Fiber.

        Args:
            neuron_ids: Set of neuron IDs
            synapse_ids: Set of synapse IDs
            anchor_neuron_id: Primary entry point
            time_start: Optional start time
            time_end: Optional end time
            summary: Optional text summary
            tags: Optional tags
            metadata: Optional metadata
            fiber_id: Optional explicit ID

        Returns:
            A new Fiber instance
        """
        if anchor_neuron_id not in neuron_ids:
            raise ValueError(f"Anchor neuron {anchor_neuron_id} must be in neuron_ids")

        return cls(
            id=fiber_id or str(uuid4()),
            neuron_ids=neuron_ids,
            synapse_ids=synapse_ids,
            anchor_neuron_id=anchor_neuron_id,
            time_start=time_start,
            time_end=time_end,
            summary=summary,
            tags=tags or set(),
            metadata=metadata or {},
            created_at=datetime.utcnow(),
        )

    def access(self) -> Fiber:
        """
        Create a new Fiber with incremented access frequency.

        Returns:
            New Fiber with frequency + 1
        """
        return Fiber(
            id=self.id,
            neuron_ids=self.neuron_ids,
            synapse_ids=self.synapse_ids,
            anchor_neuron_id=self.anchor_neuron_id,
            time_start=self.time_start,
            time_end=self.time_end,
            coherence=self.coherence,
            salience=self.salience,
            frequency=self.frequency + 1,
            summary=self.summary,
            tags=self.tags,
            metadata=self.metadata,
            created_at=self.created_at,
        )

    def with_salience(self, salience: float) -> Fiber:
        """
        Create a new Fiber with updated salience.

        Args:
            salience: New salience value (clamped to 0.0-1.0)

        Returns:
            New Fiber with updated salience
        """
        return Fiber(
            id=self.id,
            neuron_ids=self.neuron_ids,
            synapse_ids=self.synapse_ids,
            anchor_neuron_id=self.anchor_neuron_id,
            time_start=self.time_start,
            time_end=self.time_end,
            coherence=self.coherence,
            salience=max(0.0, min(1.0, salience)),
            frequency=self.frequency,
            summary=self.summary,
            tags=self.tags,
            metadata=self.metadata,
            created_at=self.created_at,
        )

    def with_summary(self, summary: str) -> Fiber:
        """
        Create a new Fiber with a summary.

        Args:
            summary: The summary text

        Returns:
            New Fiber with summary
        """
        return Fiber(
            id=self.id,
            neuron_ids=self.neuron_ids,
            synapse_ids=self.synapse_ids,
            anchor_neuron_id=self.anchor_neuron_id,
            time_start=self.time_start,
            time_end=self.time_end,
            coherence=self.coherence,
            salience=self.salience,
            frequency=self.frequency,
            summary=summary,
            tags=self.tags,
            metadata=self.metadata,
            created_at=self.created_at,
        )

    def add_tags(self, *new_tags: str) -> Fiber:
        """
        Create a new Fiber with additional tags.

        Args:
            *new_tags: Tags to add

        Returns:
            New Fiber with merged tags
        """
        return Fiber(
            id=self.id,
            neuron_ids=self.neuron_ids,
            synapse_ids=self.synapse_ids,
            anchor_neuron_id=self.anchor_neuron_id,
            time_start=self.time_start,
            time_end=self.time_end,
            coherence=self.coherence,
            salience=self.salience,
            frequency=self.frequency,
            summary=self.summary,
            tags=self.tags | set(new_tags),
            metadata=self.metadata,
            created_at=self.created_at,
        )

    @property
    def neuron_count(self) -> int:
        """Number of neurons in this fiber."""
        return len(self.neuron_ids)

    @property
    def synapse_count(self) -> int:
        """Number of synapses in this fiber."""
        return len(self.synapse_ids)

    @property
    def time_span(self) -> float | None:
        """
        Duration of this memory in seconds.

        Returns None if time bounds are not set.
        """
        if self.time_start and self.time_end:
            return (self.time_end - self.time_start).total_seconds()
        return None

    def contains_neuron(self, neuron_id: str) -> bool:
        """Check if this fiber contains a specific neuron."""
        return neuron_id in self.neuron_ids

    def overlaps_time(self, start: datetime, end: datetime) -> bool:
        """
        Check if this fiber's time range overlaps with given range.

        Args:
            start: Query start time
            end: Query end time

        Returns:
            True if there is any overlap
        """
        if self.time_start is None or self.time_end is None:
            return False

        return self.time_start <= end and self.time_end >= start
