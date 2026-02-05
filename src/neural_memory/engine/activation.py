"""Spreading activation algorithm for memory retrieval."""

from __future__ import annotations

import heapq
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neural_memory.core.brain import BrainConfig
    from neural_memory.core.fiber import Fiber
    from neural_memory.storage.base import NeuralStorage


@dataclass
class ActivationResult:
    """
    Result of activating a neuron through spreading activation.

    Attributes:
        neuron_id: The activated neuron's ID
        activation_level: Final activation level (0.0 - 1.0)
        hop_distance: Number of hops from the nearest anchor
        path: List of neuron IDs showing how we reached this neuron
        source_anchor: The anchor neuron that led to this activation
    """

    neuron_id: str
    activation_level: float
    hop_distance: int
    path: list[str]
    source_anchor: str


@dataclass
class ActivationState:
    """Internal state during activation spreading."""

    neuron_id: str
    level: float
    hops: int
    path: list[str]
    source: str

    def __lt__(self, other: ActivationState) -> bool:
        """For heap ordering (higher activation = higher priority)."""
        return self.level > other.level


class SpreadingActivation:
    """
    Spreading activation algorithm for neural memory retrieval.

    This implements the core retrieval mechanism: starting from
    anchor neurons and spreading activation through synapses,
    decaying with distance, to find related memories.
    """

    def __init__(
        self,
        storage: NeuralStorage,
        config: BrainConfig,
    ) -> None:
        """
        Initialize the activation system.

        Args:
            storage: Storage backend to read graph from
            config: Brain configuration for parameters
        """
        self._storage = storage
        self._config = config

    async def activate(
        self,
        anchor_neurons: list[str],
        max_hops: int | None = None,
        decay_factor: float = 0.5,
        min_activation: float | None = None,
    ) -> dict[str, ActivationResult]:
        """
        Spread activation from anchor neurons through the graph.

        The activation spreads through synapses, with the level
        decaying at each hop:
            activation(hop) = initial * decay_factor^hop * synapse_weight

        Args:
            anchor_neurons: Starting neurons with activation = 1.0
            max_hops: Maximum number of hops (default: from config)
            decay_factor: How much activation decays per hop
            min_activation: Minimum activation to continue spreading

        Returns:
            Dict mapping neuron_id to ActivationResult
        """
        if max_hops is None:
            max_hops = self._config.max_spread_hops

        if min_activation is None:
            min_activation = self._config.activation_threshold

        # Track best activation for each neuron
        results: dict[str, ActivationResult] = {}

        # Priority queue for BFS with activation ordering
        queue: list[ActivationState] = []

        # Initialize with anchor neurons
        for anchor_id in anchor_neurons:
            neuron = await self._storage.get_neuron(anchor_id)
            if neuron is None:
                continue

            state = ActivationState(
                neuron_id=anchor_id,
                level=1.0,
                hops=0,
                path=[anchor_id],
                source=anchor_id,
            )
            heapq.heappush(queue, state)

            # Record anchor activation
            results[anchor_id] = ActivationResult(
                neuron_id=anchor_id,
                activation_level=1.0,
                hop_distance=0,
                path=[anchor_id],
                source_anchor=anchor_id,
            )

        # Visited tracking (neuron_id, source) to allow multiple paths
        visited: set[tuple[str, str]] = set()

        # Spread activation
        while queue:
            current = heapq.heappop(queue)

            # Skip if we've visited this neuron from this source
            visit_key = (current.neuron_id, current.source)
            if visit_key in visited:
                continue
            visited.add(visit_key)

            # Skip if we've exceeded max hops
            if current.hops >= max_hops:
                continue

            # Get neighbors
            neighbors = await self._storage.get_neighbors(
                current.neuron_id,
                direction="both",
                min_weight=0.1,
            )

            for neighbor_neuron, synapse in neighbors:
                # Calculate new activation
                new_level = current.level * decay_factor * synapse.weight

                # Skip if below threshold
                if new_level < min_activation:
                    continue

                new_path = [*current.path, neighbor_neuron.id]

                # Update result if this is better activation
                existing = results.get(neighbor_neuron.id)
                if existing is None or new_level > existing.activation_level:
                    results[neighbor_neuron.id] = ActivationResult(
                        neuron_id=neighbor_neuron.id,
                        activation_level=new_level,
                        hop_distance=current.hops + 1,
                        path=new_path,
                        source_anchor=current.source,
                    )

                # Add to queue for further spreading
                new_state = ActivationState(
                    neuron_id=neighbor_neuron.id,
                    level=new_level,
                    hops=current.hops + 1,
                    path=new_path,
                    source=current.source,
                )
                heapq.heappush(queue, new_state)

        return results

    async def activate_from_multiple(
        self,
        anchor_sets: list[list[str]],
        max_hops: int | None = None,
    ) -> tuple[dict[str, ActivationResult], list[str]]:
        """
        Activate from multiple anchor sets and find intersections.

        This is useful when a query has multiple constraints (e.g.,
        time + entity). Neurons activated by multiple anchor sets
        are likely to be more relevant.

        Args:
            anchor_sets: List of anchor neuron lists
            max_hops: Maximum hops for each activation

        Returns:
            Tuple of (combined activations, intersection neuron IDs)
        """
        if not anchor_sets:
            return {}, []

        # Activate from each set
        activation_results: list[dict[str, ActivationResult]] = []
        for anchors in anchor_sets:
            if anchors:
                result = await self.activate(anchors, max_hops)
                activation_results.append(result)

        if not activation_results:
            return {}, []

        if len(activation_results) == 1:
            return activation_results[0], list(activation_results[0].keys())

        # Find intersection
        intersection = self._find_intersection(activation_results)

        # Combine results with boosted activation for intersections
        combined: dict[str, ActivationResult] = {}

        for result_set in activation_results:
            for neuron_id, activation in result_set.items():
                existing = combined.get(neuron_id)

                if existing is None:
                    combined[neuron_id] = activation
                else:
                    # Combine activations (take max, but boost if in intersection)
                    if neuron_id in intersection:
                        # Boost: multiply activations
                        new_level = min(
                            1.0, existing.activation_level + activation.activation_level * 0.5
                        )
                    else:
                        new_level = max(existing.activation_level, activation.activation_level)

                    combined[neuron_id] = ActivationResult(
                        neuron_id=neuron_id,
                        activation_level=new_level,
                        hop_distance=min(existing.hop_distance, activation.hop_distance),
                        path=existing.path
                        if existing.hop_distance <= activation.hop_distance
                        else activation.path,
                        source_anchor=existing.source_anchor,
                    )

        return combined, intersection

    def _find_intersection(
        self,
        activation_sets: list[dict[str, ActivationResult]],
    ) -> list[str]:
        """
        Find neurons activated by multiple anchor sets.

        Args:
            activation_sets: List of activation results from different anchor sets

        Returns:
            List of neuron IDs appearing in multiple sets, sorted by
            combined activation level
        """
        if not activation_sets:
            return []

        # Count appearances and sum activations
        appearances: dict[str, int] = defaultdict(int)
        total_activation: dict[str, float] = defaultdict(float)

        for result_set in activation_sets:
            for neuron_id, activation in result_set.items():
                appearances[neuron_id] += 1
                total_activation[neuron_id] += activation.activation_level

        # Find neurons in multiple sets
        multi_set_neurons = [
            (neuron_id, total_activation[neuron_id], count)
            for neuron_id, count in appearances.items()
            if count > 1
        ]

        # Sort by count (descending) then activation (descending)
        multi_set_neurons.sort(key=lambda x: (x[2], x[1]), reverse=True)

        return [n[0] for n in multi_set_neurons]

    async def get_activated_subgraph(
        self,
        activations: dict[str, ActivationResult],
        min_activation: float = 0.2,
        max_neurons: int = 50,
    ) -> tuple[list[str], list[str]]:
        """
        Get the subgraph of activated neurons and their connections.

        Args:
            activations: Activation results
            min_activation: Minimum activation to include
            max_neurons: Maximum neurons to include

        Returns:
            Tuple of (neuron_ids, synapse_ids) in the subgraph
        """
        # Filter and sort by activation
        filtered = [
            (neuron_id, result)
            for neuron_id, result in activations.items()
            if result.activation_level >= min_activation
        ]
        filtered.sort(key=lambda x: x[1].activation_level, reverse=True)

        # Take top neurons
        selected_neurons = [n[0] for n in filtered[:max_neurons]]
        selected_set = set(selected_neurons)

        # Find synapses connecting selected neurons
        synapse_ids: list[str] = []

        for neuron_id in selected_neurons:
            synapses = await self._storage.get_synapses(source_id=neuron_id)
            for synapse in synapses:
                if synapse.target_id in selected_set:
                    synapse_ids.append(synapse.id)

        return selected_neurons, synapse_ids


@dataclass
class CoActivation:
    """
    Neurons that fired together within a temporal window.

    Implements Hebbian principle: "Neurons that fire together wire together"
    Co-activation tracking enables binding between simultaneously active neurons.

    Attributes:
        neuron_ids: The neurons that co-activated
        temporal_window_ms: How close in time they fired
        co_fire_count: Number of times they co-activated
        binding_strength: Strength of the co-activation binding (0.0 - 1.0)
        source_anchors: Which anchor sets activated these neurons
    """

    neuron_ids: frozenset[str]
    temporal_window_ms: int
    co_fire_count: int = 1
    binding_strength: float = 0.5
    source_anchors: list[str] = field(default_factory=list)


class ReflexActivation:
    """
    Trail-based activation through fiber pathways.

    Unlike SpreadingActivation which uses distance-based decay,
    ReflexActivation conducts signals along fiber pathways with
    trail decay that considers:
    - Fiber conductivity
    - Synapse weight
    - Time factor (recent fibers conduct better)
    - Position in pathway
    """

    def __init__(
        self,
        storage: NeuralStorage,
        config: BrainConfig,
    ) -> None:
        """
        Initialize the reflex activation system.

        Args:
            storage: Storage backend
            config: Brain configuration
        """
        self._storage = storage
        self._config = config

    async def activate_trail(
        self,
        anchor_neurons: list[str],
        fibers: list[Fiber],
        reference_time: datetime | None = None,
        decay_rate: float = 0.15,
    ) -> dict[str, ActivationResult]:
        """
        Spread activation along fiber pathways with trail decay.

        Trail decay formula:
            new_level = level * (1 - decay) * synapse.weight * fiber.conductivity * time_factor

        Args:
            anchor_neurons: Starting neurons with activation = 1.0
            fibers: Fibers to conduct through
            reference_time: Reference time for time factor calculation
            decay_rate: Base decay rate per hop

        Returns:
            Dict mapping neuron_id to ActivationResult
        """
        if reference_time is None:
            reference_time = datetime.utcnow()

        results: dict[str, ActivationResult] = {}

        # Initialize anchor neurons
        for anchor_id in anchor_neurons:
            results[anchor_id] = ActivationResult(
                neuron_id=anchor_id,
                activation_level=1.0,
                hop_distance=0,
                path=[anchor_id],
                source_anchor=anchor_id,
            )

        # Conduct through each fiber that contains anchor neurons
        for fiber in fibers:
            # Find anchor neurons in this fiber's pathway
            fiber_anchors = [a for a in anchor_neurons if fiber.is_in_pathway(a)]
            if not fiber_anchors:
                continue

            # Calculate time factor for this fiber
            time_factor = self._compute_time_factor(fiber, reference_time)

            # Conduct from each anchor along the pathway
            for anchor_id in fiber_anchors:
                start_pos = fiber.pathway_position(anchor_id)
                if start_pos is None:
                    continue

                # Spread forward in pathway
                self._conduct_along_pathway(
                    results=results,
                    fiber=fiber,
                    start_pos=start_pos,
                    direction=1,
                    anchor_id=anchor_id,
                    decay_rate=decay_rate,
                    time_factor=time_factor,
                )

                # Spread backward in pathway
                self._conduct_along_pathway(
                    results=results,
                    fiber=fiber,
                    start_pos=start_pos,
                    direction=-1,
                    anchor_id=anchor_id,
                    decay_rate=decay_rate,
                    time_factor=time_factor,
                )

        return results

    def _conduct_along_pathway(
        self,
        results: dict[str, ActivationResult],
        fiber: Fiber,
        start_pos: int,
        direction: int,
        anchor_id: str,
        decay_rate: float,
        time_factor: float,
    ) -> None:
        """
        Conduct activation along a fiber pathway in one direction.

        Args:
            results: Results dict to update
            fiber: The fiber to conduct through
            start_pos: Starting position in pathway
            direction: 1 for forward, -1 for backward
            anchor_id: The source anchor neuron
            decay_rate: Decay rate per hop
            time_factor: Time-based conductivity factor
        """
        current_level = 1.0
        path = [fiber.pathway[start_pos]]
        pos = start_pos + direction
        hops = 0

        while 0 <= pos < len(fiber.pathway):
            hops += 1
            neuron_id = fiber.pathway[pos]

            # Trail decay formula
            # level * (1 - decay) * fiber.conductivity * time_factor
            current_level = current_level * (1 - decay_rate) * fiber.conductivity * time_factor

            # Stop if below threshold
            if current_level < self._config.activation_threshold:
                break

            path = [*path, neuron_id]

            # Update if better than existing
            existing = results.get(neuron_id)
            if existing is None or current_level > existing.activation_level:
                results[neuron_id] = ActivationResult(
                    neuron_id=neuron_id,
                    activation_level=current_level,
                    hop_distance=hops,
                    path=path,
                    source_anchor=anchor_id,
                )

            pos += direction

    def _compute_time_factor(
        self,
        fiber: Fiber,
        reference_time: datetime,
    ) -> float:
        """
        Compute time-based conductivity factor.

        Recent fibers conduct better. Decay over 7 days.

        Args:
            fiber: The fiber
            reference_time: Reference time

        Returns:
            Time factor between 0.1 and 1.0
        """
        if fiber.last_conducted is None:
            return 0.5  # Unknown history

        age_hours = (reference_time - fiber.last_conducted).total_seconds() / 3600
        # Decay over 7 days (168 hours)
        return max(0.1, 1.0 - (age_hours / 168))

    def find_co_activated(
        self,
        activation_sets: list[dict[str, ActivationResult]],
        temporal_window_ms: int = 500,
    ) -> list[CoActivation]:
        """
        Find neurons that co-activated within a temporal window.

        Implements Hebbian principle: "Neurons that fire together wire together"

        Args:
            activation_sets: Activation results from different anchor sets
            temporal_window_ms: How close in time neurons must fire

        Returns:
            List of CoActivation objects sorted by binding strength
        """
        if not activation_sets:
            return []

        # Track which anchors activated each neuron
        neuron_sources: dict[str, list[int]] = defaultdict(list)

        for i, activation_set in enumerate(activation_sets):
            for neuron_id in activation_set:
                neuron_sources[neuron_id].append(i)

        # Find neurons activated by multiple sources
        co_activations: list[CoActivation] = []

        for neuron_id, sources in neuron_sources.items():
            if len(sources) < 2:
                continue

            # Binding strength based on how many sources activated this neuron
            binding_strength = len(sources) / len(activation_sets)

            co_activations.append(
                CoActivation(
                    neuron_ids=frozenset([neuron_id]),
                    temporal_window_ms=temporal_window_ms,
                    co_fire_count=len(sources),
                    binding_strength=binding_strength,
                    source_anchors=[],
                )
            )

        # Sort by binding strength descending
        co_activations.sort(key=lambda c: c.binding_strength, reverse=True)

        return co_activations

    async def activate_with_co_binding(
        self,
        anchor_sets: list[list[str]],
        fibers: list[Fiber],
        reference_time: datetime | None = None,
    ) -> tuple[dict[str, ActivationResult], list[CoActivation]]:
        """
        Activate from multiple anchor sets with co-activation binding.

        Combines trail activation with co-activation detection.

        Args:
            anchor_sets: List of anchor neuron lists (e.g., [time_anchors, entity_anchors])
            fibers: Fibers to conduct through
            reference_time: Reference time for time factor

        Returns:
            Tuple of (combined activations, co-activations)
        """
        if reference_time is None:
            reference_time = datetime.utcnow()

        # Activate from each anchor set
        activation_results: list[dict[str, ActivationResult]] = []

        for anchors in anchor_sets:
            if anchors:
                result = await self.activate_trail(
                    anchor_neurons=anchors,
                    fibers=fibers,
                    reference_time=reference_time,
                )
                activation_results.append(result)

        if not activation_results:
            return {}, []

        # Find co-activations
        co_activations = self.find_co_activated(activation_results)

        # Combine results with boosted activation for co-activated neurons
        combined: dict[str, ActivationResult] = {}
        co_activated_ids = {
            neuron_id
            for co in co_activations
            for neuron_id in co.neuron_ids
        }

        for result_set in activation_results:
            for neuron_id, activation in result_set.items():
                existing = combined.get(neuron_id)

                if existing is None:
                    combined[neuron_id] = activation
                else:
                    # Boost co-activated neurons
                    if neuron_id in co_activated_ids:
                        new_level = min(
                            1.0,
                            existing.activation_level + activation.activation_level * 0.5,
                        )
                    else:
                        new_level = max(existing.activation_level, activation.activation_level)

                    combined[neuron_id] = ActivationResult(
                        neuron_id=neuron_id,
                        activation_level=new_level,
                        hop_distance=min(existing.hop_distance, activation.hop_distance),
                        path=existing.path
                        if existing.hop_distance <= activation.hop_distance
                        else activation.path,
                        source_anchor=existing.source_anchor,
                    )

        return combined, co_activations
