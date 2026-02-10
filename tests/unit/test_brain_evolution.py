"""Tests for brain_evolution: cognitive metrics layer."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from neural_memory.engine.brain_evolution import (
    BrainEvolution,
    EvolutionEngine,
    ProficiencyLevel,
    _compute_proficiency,
    _maturity_signal,
)
from neural_memory.engine.memory_stages import MaturationRecord, MemoryStage
from neural_memory.utils.timeutils import utcnow


def _mock_synapse(
    source_id: str = "a",
    target_id: str = "b",
    created_at: datetime | None = None,
    last_activated: datetime | None = None,
    reinforced_count: int = 0,
) -> MagicMock:
    s = MagicMock()
    s.source_id = source_id
    s.target_id = target_id
    s.created_at = created_at or utcnow()
    s.last_activated = last_activated
    s.reinforced_count = reinforced_count
    s.metadata = {}
    return s


def _mock_fiber(
    last_conducted: datetime | None = None,
    frequency: int = 0,
    conductivity: float = 1.0,
    created_at: datetime | None = None,
) -> MagicMock:
    f = MagicMock()
    f.last_conducted = last_conducted
    f.frequency = frequency
    f.conductivity = conductivity
    f.created_at = created_at or utcnow()
    return f


@pytest.fixture
def mock_storage() -> AsyncMock:
    """Storage with empty brain."""
    storage = AsyncMock()
    brain = MagicMock()
    brain.name = "test-brain"
    brain.id = "brain-1"
    storage.get_brain = AsyncMock(return_value=brain)
    storage.get_stats = AsyncMock(
        return_value={"neuron_count": 0, "synapse_count": 0, "fiber_count": 0}
    )
    storage.get_all_synapses = AsyncMock(return_value=[])
    storage.get_neighbors = AsyncMock(return_value=[])
    storage.find_maturations = AsyncMock(return_value=[])
    storage.get_fibers = AsyncMock(return_value=[])
    storage._current_brain_id = "brain-1"
    return storage


class TestBrainEvolutionDataclass:
    """Tests for BrainEvolution immutability."""

    def test_frozen(self) -> None:
        """BrainEvolution is immutable."""
        evo = BrainEvolution(
            brain_id="brain-1",
            brain_name="test",
            computed_at=utcnow(),
            semantic_ratio=0.0,
            reinforcement_days=0.0,
            topology_coherence=0.0,
            plasticity_index=0.0,
            knowledge_density=0.0,
            maturity_level=0.0,
            plasticity=0.0,
            density=0.0,
            proficiency_index=0,
            proficiency_level=ProficiencyLevel.JUNIOR,
            activity_score=0.0,
            total_fibers=0,
            total_synapses=0,
            total_neurons=0,
            fibers_at_semantic=0,
            fibers_at_episodic=0,
        )
        with pytest.raises(AttributeError):
            evo.proficiency_index = 99  # type: ignore[misc]


class TestProficiencyLevel:
    """Tests for proficiency level enum."""

    def test_values(self) -> None:
        assert ProficiencyLevel.JUNIOR.value == "junior"
        assert ProficiencyLevel.SENIOR.value == "senior"
        assert ProficiencyLevel.EXPERT.value == "expert"


class TestProficiencyComputation:
    """Tests for _compute_proficiency pure function."""

    def test_junior_low_metrics(self) -> None:
        """Low metrics → JUNIOR."""
        index, level = _compute_proficiency(
            semantic_ratio=0.0,
            reinforcement_days=0.0,
            topology_coherence=0.0,
            plasticity_index=0.0,
            decay_factor=1.0,
        )
        assert level == ProficiencyLevel.JUNIOR
        assert index < 25

    def test_senior_medium_metrics(self) -> None:
        """Medium metrics + 5 reinforcement days → SENIOR."""
        index, level = _compute_proficiency(
            semantic_ratio=0.3,
            reinforcement_days=5.0,
            topology_coherence=0.5,
            plasticity_index=0.1,
            decay_factor=1.0,
        )
        assert level == ProficiencyLevel.SENIOR
        assert 25 <= index <= 55

    def test_expert_high_metrics(self) -> None:
        """High metrics + 12 reinforcement days → EXPERT."""
        index, level = _compute_proficiency(
            semantic_ratio=0.8,
            reinforcement_days=12.0,
            topology_coherence=0.8,
            plasticity_index=0.3,
            decay_factor=1.0,
        )
        assert level == ProficiencyLevel.EXPERT
        assert index > 55

    def test_senior_needs_reinforcement_days(self) -> None:
        """High semantic but low reinforcement days → stays JUNIOR (AND condition)."""
        index, level = _compute_proficiency(
            semantic_ratio=0.5,
            reinforcement_days=2.0,  # Below 4
            topology_coherence=0.5,
            plasticity_index=0.2,
            decay_factor=1.0,
        )
        assert level == ProficiencyLevel.JUNIOR

    def test_expert_needs_reinforcement_days(self) -> None:
        """High index but low reinforcement → SENIOR not EXPERT."""
        index, level = _compute_proficiency(
            semantic_ratio=0.9,
            reinforcement_days=6.0,  # Above 4, below 10
            topology_coherence=0.9,
            plasticity_index=0.5,
            decay_factor=1.0,
        )
        assert level == ProficiencyLevel.SENIOR

    def test_decay_reduces_proficiency(self) -> None:
        """Low decay factor reduces proficiency index."""
        index_full, _ = _compute_proficiency(
            semantic_ratio=0.5,
            reinforcement_days=5.0,
            topology_coherence=0.5,
            plasticity_index=0.1,
            decay_factor=1.0,
        )
        index_decayed, _ = _compute_proficiency(
            semantic_ratio=0.5,
            reinforcement_days=5.0,
            topology_coherence=0.5,
            plasticity_index=0.1,
            decay_factor=0.3,
        )
        assert index_decayed < index_full

    def test_index_clamped(self) -> None:
        """Proficiency index stays in 0-100 range."""
        index, _ = _compute_proficiency(
            semantic_ratio=1.0,
            reinforcement_days=20.0,
            topology_coherence=1.0,
            plasticity_index=1.0,
            decay_factor=1.0,
        )
        assert 0 <= index <= 100


class TestMaturitySignal:
    """Tests for _maturity_signal agent-facing function."""

    def test_zero(self) -> None:
        assert _maturity_signal(0.0, 0.0) == 0.0

    def test_full(self) -> None:
        signal = _maturity_signal(0.5, 7.0)
        assert signal == 1.0

    def test_partial(self) -> None:
        signal = _maturity_signal(0.25, 3.5)
        assert 0.0 < signal < 1.0


class TestEvolutionEngine:
    """Tests for EvolutionEngine.analyze()."""

    @pytest.mark.asyncio
    async def test_empty_brain(self, mock_storage: AsyncMock) -> None:
        """Empty brain → JUNIOR with zero metrics."""
        engine = EvolutionEngine(mock_storage)
        evo = await engine.analyze("brain-1")

        assert evo.proficiency_level == ProficiencyLevel.JUNIOR
        assert evo.semantic_ratio == 0.0
        assert evo.reinforcement_days == 0.0
        assert evo.plasticity_index == 0.0
        assert evo.fibers_at_semantic == 0
        assert evo.fibers_at_episodic == 0
        assert evo.brain_name == "test-brain"

    @pytest.mark.asyncio
    async def test_with_semantic_maturations(self, mock_storage: AsyncMock) -> None:
        """Fibers at SEMANTIC → semantic_ratio > 0."""
        maturations = [
            MaturationRecord(
                fiber_id=f"f{i}",
                brain_id="brain-1",
                stage=MemoryStage.SEMANTIC if i < 3 else MemoryStage.EPISODIC,
                reinforcement_timestamps=[
                    "2025-01-01T10:00:00",
                    "2025-01-03T10:00:00",
                    "2025-01-05T10:00:00",
                ],
            )
            for i in range(5)
        ]
        mock_storage.find_maturations = AsyncMock(return_value=maturations)

        engine = EvolutionEngine(mock_storage)
        evo = await engine.analyze("brain-1")

        assert evo.semantic_ratio == 0.6  # 3/5
        assert evo.fibers_at_semantic == 3
        assert evo.fibers_at_episodic == 2
        assert evo.reinforcement_days == 3.0  # 3 distinct days

    @pytest.mark.asyncio
    async def test_plasticity_recent_synapses(self, mock_storage: AsyncMock) -> None:
        """Recently created/reinforced synapses → plasticity > 0."""
        now = utcnow()
        synapses = [
            _mock_synapse(created_at=now - timedelta(days=1)),  # new
            _mock_synapse(
                created_at=now - timedelta(days=30),
                last_activated=now - timedelta(days=2),
            ),  # reinforced
            _mock_synapse(created_at=now - timedelta(days=60)),  # old, inactive
        ]
        mock_storage.get_all_synapses = AsyncMock(return_value=synapses)
        mock_storage.get_stats = AsyncMock(
            return_value={"neuron_count": 3, "synapse_count": 3, "fiber_count": 1}
        )

        engine = EvolutionEngine(mock_storage)
        evo = await engine.analyze("brain-1")

        # 1 new + 1 reinforced out of 3 total = 2/3
        assert evo.plasticity_index > 0.0

    @pytest.mark.asyncio
    async def test_activity_score(self, mock_storage: AsyncMock) -> None:
        """Recently conducted fibers → activity_score > 0."""
        now = utcnow()
        fibers = [
            _mock_fiber(last_conducted=now - timedelta(days=1)),
            _mock_fiber(last_conducted=now - timedelta(days=30)),
            _mock_fiber(last_conducted=now - timedelta(hours=2)),
        ]
        mock_storage.get_fibers = AsyncMock(return_value=fibers)
        mock_storage.get_stats = AsyncMock(
            return_value={"neuron_count": 5, "synapse_count": 10, "fiber_count": 3}
        )

        engine = EvolutionEngine(mock_storage)
        evo = await engine.analyze("brain-1")

        # 2 fibers conducted in last 7 days out of 3 total
        assert abs(evo.activity_score - 2 / 3) < 0.01

    @pytest.mark.asyncio
    async def test_agent_signals_bounded(self, mock_storage: AsyncMock) -> None:
        """Agent-facing signals are bounded 0.0-1.0."""
        engine = EvolutionEngine(mock_storage)
        evo = await engine.analyze("brain-1")

        assert 0.0 <= evo.maturity_level <= 1.0
        assert 0.0 <= evo.plasticity <= 1.0
        assert 0.0 <= evo.density <= 1.0

    @pytest.mark.asyncio
    async def test_decay_old_brain(self, mock_storage: AsyncMock) -> None:
        """Brain not used for 60 days → decay reduces proficiency."""
        now = utcnow()
        old_fibers = [
            _mock_fiber(
                last_conducted=now - timedelta(days=60),
                created_at=now - timedelta(days=90),
            ),
        ]
        mock_storage.get_fibers = AsyncMock(return_value=old_fibers)
        mock_storage.get_stats = AsyncMock(
            return_value={"neuron_count": 5, "synapse_count": 10, "fiber_count": 1}
        )

        # Add some maturations to give non-zero base score
        maturations = [
            MaturationRecord(
                fiber_id="f1",
                brain_id="brain-1",
                stage=MemoryStage.SEMANTIC,
                reinforcement_timestamps=[
                    "2024-01-01T10:00:00",
                    "2024-01-05T10:00:00",
                    "2024-01-10T10:00:00",
                    "2024-01-15T10:00:00",
                    "2024-01-20T10:00:00",
                ],
            ),
        ]
        mock_storage.find_maturations = AsyncMock(return_value=maturations)

        engine = EvolutionEngine(mock_storage)
        evo = await engine.analyze("brain-1")

        # Decay should significantly reduce proficiency
        assert evo.proficiency_index < 50
