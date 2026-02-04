"""Integration tests for query flow."""

from __future__ import annotations

from datetime import datetime

import pytest

from neural_memory.core.brain import Brain, BrainConfig
from neural_memory.engine.encoder import MemoryEncoder
from neural_memory.engine.retrieval import DepthLevel, ReflexPipeline
from neural_memory.storage.memory_store import InMemoryStorage


class TestQueryFlow:
    """Integration tests for the full query flow."""

    @pytest.fixture
    async def storage_with_memories(self) -> InMemoryStorage:
        """Create storage populated with test memories."""
        storage = InMemoryStorage()

        config = BrainConfig(
            activation_threshold=0.1,
            max_spread_hops=4,
        )
        brain = Brain.create(name="test_brain", config=config)
        await storage.save_brain(brain)
        storage.set_brain(brain.id)

        encoder = MemoryEncoder(storage, config)

        # Encode several memories
        await encoder.encode(
            "Met with Alice at the coffee shop to discuss API design",
            timestamp=datetime(2024, 2, 3, 15, 0),
        )

        await encoder.encode(
            "Alice suggested adding rate limiting to the API",
            timestamp=datetime(2024, 2, 3, 15, 30),
        )

        await encoder.encode(
            "Completed the authentication module",
            timestamp=datetime(2024, 2, 4, 10, 0),
        )

        return storage

    @pytest.mark.asyncio
    async def test_basic_query(self, storage_with_memories: InMemoryStorage) -> None:
        """Test a basic query returns results."""
        brain = await storage_with_memories.get_brain(
            storage_with_memories._current_brain_id  # type: ignore
        )
        assert brain is not None

        pipeline = ReflexPipeline(storage_with_memories, brain.config)

        result = await pipeline.query(
            "What did Alice suggest?",
            reference_time=datetime(2024, 2, 4, 16, 0),
        )

        assert result.neurons_activated > 0
        assert result.latency_ms >= 0
        assert result.context  # Should have some context

    @pytest.mark.asyncio
    async def test_query_with_time_constraint(self, storage_with_memories: InMemoryStorage) -> None:
        """Test query with temporal constraint."""
        brain = await storage_with_memories.get_brain(
            storage_with_memories._current_brain_id  # type: ignore
        )
        assert brain is not None

        pipeline = ReflexPipeline(storage_with_memories, brain.config)

        result = await pipeline.query(
            "What happened yesterday afternoon?",
            reference_time=datetime(2024, 2, 4, 16, 0),
        )

        # Query should complete without error and return valid structure
        assert result.confidence >= 0
        assert result.latency_ms >= 0
        assert result.depth_used is not None

    @pytest.mark.asyncio
    async def test_query_with_entity(self, storage_with_memories: InMemoryStorage) -> None:
        """Test query mentioning a specific entity."""
        brain = await storage_with_memories.get_brain(
            storage_with_memories._current_brain_id  # type: ignore
        )
        assert brain is not None

        pipeline = ReflexPipeline(storage_with_memories, brain.config)

        result = await pipeline.query(
            "Tell me about Alice",
            reference_time=datetime(2024, 2, 4, 16, 0),
        )

        assert result.neurons_activated > 0

    @pytest.mark.asyncio
    async def test_query_depth_levels(self, storage_with_memories: InMemoryStorage) -> None:
        """Test different depth levels."""
        brain = await storage_with_memories.get_brain(
            storage_with_memories._current_brain_id  # type: ignore
        )
        assert brain is not None

        pipeline = ReflexPipeline(storage_with_memories, brain.config)

        # Instant (shallow)
        instant = await pipeline.query(
            "Who?", depth=DepthLevel.INSTANT, reference_time=datetime(2024, 2, 4, 16, 0)
        )
        assert instant.depth_used == DepthLevel.INSTANT

        # Deep
        deep = await pipeline.query(
            "Why?", depth=DepthLevel.DEEP, reference_time=datetime(2024, 2, 4, 16, 0)
        )
        assert deep.depth_used == DepthLevel.DEEP

    @pytest.mark.asyncio
    async def test_query_returns_context(self, storage_with_memories: InMemoryStorage) -> None:
        """Test that query returns formatted context."""
        brain = await storage_with_memories.get_brain(
            storage_with_memories._current_brain_id  # type: ignore
        )
        assert brain is not None

        pipeline = ReflexPipeline(storage_with_memories, brain.config)

        result = await pipeline.query(
            "What happened?",
            max_tokens=1000,
            reference_time=datetime(2024, 2, 4, 16, 0),
        )

        assert isinstance(result.context, str)
        # Context should have some structure
        assert len(result.context) > 0

    @pytest.mark.asyncio
    async def test_query_subgraph_extraction(self, storage_with_memories: InMemoryStorage) -> None:
        """Test that query extracts relevant subgraph."""
        brain = await storage_with_memories.get_brain(
            storage_with_memories._current_brain_id  # type: ignore
        )
        assert brain is not None

        pipeline = ReflexPipeline(storage_with_memories, brain.config)

        result = await pipeline.query(
            "Coffee shop meeting",
            reference_time=datetime(2024, 2, 4, 16, 0),
        )

        assert result.subgraph is not None
        assert isinstance(result.subgraph.neuron_ids, list)
        assert isinstance(result.subgraph.synapse_ids, list)

    @pytest.mark.asyncio
    async def test_empty_query(self, storage_with_memories: InMemoryStorage) -> None:
        """Test query with minimal content."""
        brain = await storage_with_memories.get_brain(
            storage_with_memories._current_brain_id  # type: ignore
        )
        assert brain is not None

        pipeline = ReflexPipeline(storage_with_memories, brain.config)

        result = await pipeline.query(
            "xyz123",  # Unlikely to match anything
            reference_time=datetime(2024, 2, 4, 16, 0),
        )

        # Should still return a valid result structure
        assert result.confidence >= 0
        assert result.context is not None
