"""Unit tests for spreading activation."""

from __future__ import annotations

import pytest

from neural_memory.core.brain import BrainConfig
from neural_memory.core.neuron import Neuron, NeuronType
from neural_memory.core.synapse import Synapse, SynapseType
from neural_memory.engine.activation import ActivationResult, SpreadingActivation
from neural_memory.storage.memory_store import InMemoryStorage


class TestSpreadingActivation:
    """Tests for SpreadingActivation class."""

    @pytest.fixture
    def config(self) -> BrainConfig:
        """Create test config."""
        return BrainConfig(
            activation_threshold=0.1,
            max_spread_hops=3,
        )

    @pytest.fixture
    async def storage_with_graph(self, config: BrainConfig) -> InMemoryStorage:
        """Create storage with a simple graph for testing."""
        from neural_memory.core.brain import Brain

        storage = InMemoryStorage()
        brain = Brain.create(name="test", config=config)
        await storage.save_brain(brain)
        storage.set_brain(brain.id)

        # Create a simple graph:
        # A -> B -> C -> D
        # |         |
        # +----E----+
        neurons = [
            Neuron.create(type=NeuronType.CONCEPT, content="A", neuron_id="a"),
            Neuron.create(type=NeuronType.CONCEPT, content="B", neuron_id="b"),
            Neuron.create(type=NeuronType.CONCEPT, content="C", neuron_id="c"),
            Neuron.create(type=NeuronType.CONCEPT, content="D", neuron_id="d"),
            Neuron.create(type=NeuronType.CONCEPT, content="E", neuron_id="e"),
        ]

        for n in neurons:
            await storage.add_neuron(n)

        synapses = [
            Synapse.create("a", "b", SynapseType.RELATED_TO, weight=0.8, synapse_id="ab"),
            Synapse.create("b", "c", SynapseType.RELATED_TO, weight=0.8, synapse_id="bc"),
            Synapse.create("c", "d", SynapseType.RELATED_TO, weight=0.8, synapse_id="cd"),
            Synapse.create("a", "e", SynapseType.RELATED_TO, weight=0.5, synapse_id="ae"),
            Synapse.create("e", "c", SynapseType.RELATED_TO, weight=0.5, synapse_id="ec"),
        ]

        for s in synapses:
            await storage.add_synapse(s)

        return storage

    @pytest.mark.asyncio
    async def test_activate_single_anchor(
        self, storage_with_graph: InMemoryStorage, config: BrainConfig
    ) -> None:
        """Test activation from a single anchor."""
        activator = SpreadingActivation(storage_with_graph, config)

        results = await activator.activate(["a"])

        # Anchor should have full activation
        assert "a" in results
        assert results["a"].activation_level == 1.0
        assert results["a"].hop_distance == 0

        # Direct neighbor should have decayed activation
        assert "b" in results
        assert results["b"].activation_level < 1.0
        assert results["b"].hop_distance == 1

    @pytest.mark.asyncio
    async def test_activation_decays_with_distance(
        self, storage_with_graph: InMemoryStorage, config: BrainConfig
    ) -> None:
        """Test that activation decays with distance."""
        activator = SpreadingActivation(storage_with_graph, config)

        results = await activator.activate(["a"], max_hops=4)

        # Each hop should have lower activation
        if "b" in results and "c" in results:
            assert results["b"].activation_level > results["c"].activation_level

        if "c" in results and "d" in results:
            assert results["c"].activation_level > results["d"].activation_level

    @pytest.mark.asyncio
    async def test_activate_respects_max_hops(
        self, storage_with_graph: InMemoryStorage, config: BrainConfig
    ) -> None:
        """Test that activation respects max_hops."""
        activator = SpreadingActivation(storage_with_graph, config)

        results = await activator.activate(["a"], max_hops=1)

        # Should only reach 1-hop neighbors
        assert "a" in results
        assert "b" in results or "e" in results

        # D is 3 hops away, should not be reached
        assert "d" not in results or results.get("d", ActivationResult("", 0, 0, [], "")).hop_distance <= 1

    @pytest.mark.asyncio
    async def test_activate_multiple_anchors(
        self, storage_with_graph: InMemoryStorage, config: BrainConfig
    ) -> None:
        """Test activation from multiple anchors."""
        activator = SpreadingActivation(storage_with_graph, config)

        results = await activator.activate(["a", "d"])

        # Both anchors should be activated
        assert "a" in results
        assert "d" in results

        # C should be reachable from both
        assert "c" in results

    @pytest.mark.asyncio
    async def test_activate_from_multiple_sets_finds_intersection(
        self, storage_with_graph: InMemoryStorage, config: BrainConfig
    ) -> None:
        """Test that activating from multiple sets finds intersections."""
        activator = SpreadingActivation(storage_with_graph, config)

        results, intersections = await activator.activate_from_multiple(
            [["a"], ["d"]], max_hops=4
        )

        # C is reachable from both A and D
        assert "c" in intersections or len(intersections) > 0

    @pytest.mark.asyncio
    async def test_get_activated_subgraph(
        self, storage_with_graph: InMemoryStorage, config: BrainConfig
    ) -> None:
        """Test extracting subgraph from activations."""
        activator = SpreadingActivation(storage_with_graph, config)

        activations = await activator.activate(["a"])
        neuron_ids, synapse_ids = await activator.get_activated_subgraph(
            activations, min_activation=0.1
        )

        assert len(neuron_ids) > 0
        assert "a" in neuron_ids

    @pytest.mark.asyncio
    async def test_empty_anchors(
        self, storage_with_graph: InMemoryStorage, config: BrainConfig
    ) -> None:
        """Test activation with empty anchor list."""
        activator = SpreadingActivation(storage_with_graph, config)

        results = await activator.activate([])

        assert results == {}

    @pytest.mark.asyncio
    async def test_nonexistent_anchor(
        self, storage_with_graph: InMemoryStorage, config: BrainConfig
    ) -> None:
        """Test activation with nonexistent anchor."""
        activator = SpreadingActivation(storage_with_graph, config)

        results = await activator.activate(["nonexistent"])

        assert results == {}
