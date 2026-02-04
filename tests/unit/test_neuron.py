"""Unit tests for Neuron model."""

from __future__ import annotations

from datetime import datetime

import pytest

from neural_memory.core.neuron import Neuron, NeuronState, NeuronType


class TestNeuron:
    """Tests for Neuron class."""

    def test_create_neuron(self) -> None:
        """Test creating a neuron with factory method."""
        neuron = Neuron.create(
            type=NeuronType.ENTITY,
            content="Alice",
            metadata={"entity_type": "person"},
        )

        assert neuron.type == NeuronType.ENTITY
        assert neuron.content == "Alice"
        assert neuron.metadata == {"entity_type": "person"}
        assert neuron.id  # Should have generated ID
        assert isinstance(neuron.created_at, datetime)

    def test_create_neuron_with_explicit_id(self) -> None:
        """Test creating a neuron with explicit ID."""
        neuron = Neuron.create(
            type=NeuronType.TIME,
            content="3pm",
            neuron_id="custom-id",
        )

        assert neuron.id == "custom-id"

    def test_neuron_is_frozen(self) -> None:
        """Test that Neuron is immutable."""
        neuron = Neuron.create(type=NeuronType.CONCEPT, content="test")

        with pytest.raises(AttributeError):
            neuron.content = "new content"  # type: ignore

    def test_with_metadata(self) -> None:
        """Test creating new neuron with updated metadata."""
        original = Neuron.create(
            type=NeuronType.ENTITY,
            content="Alice",
            metadata={"role": "user"},
        )

        updated = original.with_metadata(status="active", priority=1)

        # Original unchanged
        assert original.metadata == {"role": "user"}

        # New neuron has merged metadata
        assert updated.metadata == {"role": "user", "status": "active", "priority": 1}
        assert updated.id == original.id
        assert updated.content == original.content

    def test_all_neuron_types(self) -> None:
        """Test all neuron types can be created."""
        for neuron_type in NeuronType:
            neuron = Neuron.create(type=neuron_type, content=f"test_{neuron_type}")
            assert neuron.type == neuron_type


class TestNeuronState:
    """Tests for NeuronState class."""

    def test_create_state(self) -> None:
        """Test creating neuron state."""
        state = NeuronState(neuron_id="test-1")

        assert state.neuron_id == "test-1"
        assert state.activation_level == 0.0
        assert state.access_frequency == 0
        assert state.last_activated is None
        assert state.decay_rate == 0.1

    def test_activate(self) -> None:
        """Test activating a neuron state."""
        state = NeuronState(neuron_id="test-1")
        activated = state.activate(level=0.8)

        # Original unchanged
        assert state.activation_level == 0.0
        assert state.access_frequency == 0

        # New state updated
        assert activated.activation_level == 0.8
        assert activated.access_frequency == 1
        assert activated.last_activated is not None

    def test_activate_clamps_level(self) -> None:
        """Test activation level is clamped to 0.0-1.0."""
        state = NeuronState(neuron_id="test-1")

        # Test upper bound
        high = state.activate(level=1.5)
        assert high.activation_level == 1.0

        # Test lower bound
        low = state.activate(level=-0.5)
        assert low.activation_level == 0.0

    def test_decay(self) -> None:
        """Test decay over time."""
        state = NeuronState(neuron_id="test-1", activation_level=1.0, decay_rate=0.1)

        # Decay over 1 day
        decayed = state.decay(time_delta_seconds=86400)

        assert decayed.activation_level < 1.0
        assert decayed.activation_level > 0.0

    def test_is_active(self) -> None:
        """Test is_active property."""
        inactive = NeuronState(neuron_id="test-1", activation_level=0.05)
        active = NeuronState(neuron_id="test-2", activation_level=0.5)

        assert not inactive.is_active
        assert active.is_active

    def test_multiple_activations_increment_frequency(self) -> None:
        """Test that multiple activations increment frequency."""
        state = NeuronState(neuron_id="test-1")
        state = state.activate(0.5)
        state = state.activate(0.7)
        state = state.activate(0.9)

        assert state.access_frequency == 3
