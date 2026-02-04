"""Reflex retrieval pipeline - the main memory retrieval mechanism."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import TYPE_CHECKING, Any

from neural_memory.core.neuron import NeuronType
from neural_memory.engine.activation import ActivationResult, SpreadingActivation
from neural_memory.extraction.parser import QueryIntent, QueryParser, Stimulus

if TYPE_CHECKING:
    from neural_memory.core.brain import BrainConfig
    from neural_memory.core.fiber import Fiber
    from neural_memory.storage.base import NeuralStorage


class DepthLevel(IntEnum):
    """
    Depth levels for retrieval queries.

    Higher depth = more exploration but slower retrieval.
    """

    INSTANT = 0  # Who, where, what (1 hop) - Simple fact retrieval
    CONTEXT = 1  # Before/after (2-3 hops) - Contextual information
    HABIT = 2  # Patterns (cross-time) - Recurring patterns
    DEEP = 3  # Emotions, causality (full) - Deep analysis


@dataclass
class Subgraph:
    """
    Extracted subgraph from activation.

    Attributes:
        neuron_ids: IDs of neurons in the subgraph
        synapse_ids: IDs of synapses connecting neurons
        anchor_ids: IDs of the anchor neurons that started activation
    """

    neuron_ids: list[str]
    synapse_ids: list[str]
    anchor_ids: list[str]


@dataclass
class RetrievalResult:
    """
    Result of a retrieval query.

    Attributes:
        answer: Reconstructed answer text (if determinable)
        confidence: Confidence in the answer (0.0 - 1.0)
        depth_used: Which depth level was used
        neurons_activated: Number of neurons that were activated
        fibers_matched: IDs of fibers that matched the query
        subgraph: The extracted relevant subgraph
        context: Formatted context for injection into agent prompts
        latency_ms: Time taken for retrieval in milliseconds
        metadata: Additional retrieval metadata
    """

    answer: str | None
    confidence: float
    depth_used: DepthLevel
    neurons_activated: int
    fibers_matched: list[str]
    subgraph: Subgraph
    context: str
    latency_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)


class ReflexPipeline:
    """
    Main retrieval engine - the "consciousness" of the memory system.

    The reflex pipeline:
    1. Decomposes queries into activation signals (Stimulus)
    2. Finds anchor neurons matching signals
    3. Spreads activation through the graph
    4. Finds intersection points
    5. Extracts relevant subgraph
    6. Reconstitutes answer/context

    This mimics human memory retrieval - associative recall through
    spreading activation rather than database search.
    """

    def __init__(
        self,
        storage: NeuralStorage,
        config: BrainConfig,
        parser: QueryParser | None = None,
    ) -> None:
        """
        Initialize the retrieval pipeline.

        Args:
            storage: Storage backend
            config: Brain configuration
            parser: Custom query parser (creates default if None)
        """
        self._storage = storage
        self._config = config
        self._parser = parser or QueryParser()
        self._activator = SpreadingActivation(storage, config)

    async def query(
        self,
        query: str,
        depth: DepthLevel | None = None,
        max_tokens: int | None = None,
        reference_time: datetime | None = None,
    ) -> RetrievalResult:
        """
        Execute the retrieval pipeline.

        Args:
            query: The query text
            depth: Retrieval depth (auto-detect if None)
            max_tokens: Maximum tokens in context
            reference_time: Reference time for temporal parsing

        Returns:
            RetrievalResult with answer and context
        """
        start_time = time.perf_counter()

        if max_tokens is None:
            max_tokens = self._config.max_context_tokens

        if reference_time is None:
            reference_time = datetime.now()

        # 1. Parse query into stimulus
        stimulus = self._parser.parse(query, reference_time)

        # 2. Auto-detect depth if not specified
        if depth is None:
            depth = self._detect_depth(stimulus)

        # 3. Find anchor neurons
        anchor_sets = await self._find_anchors(stimulus)

        # 4. Spread activation
        activations, intersections = await self._activator.activate_from_multiple(
            anchor_sets,
            max_hops=self._depth_to_hops(depth),
        )

        # 5. Find matching fibers
        fibers_matched = await self._find_matching_fibers(activations)

        # 6. Extract subgraph
        neuron_ids, synapse_ids = await self._activator.get_activated_subgraph(
            activations,
            min_activation=self._config.activation_threshold,
            max_neurons=50,
        )

        subgraph = Subgraph(
            neuron_ids=neuron_ids,
            synapse_ids=synapse_ids,
            anchor_ids=[a for anchors in anchor_sets for a in anchors],
        )

        # 7. Reconstitute answer and context
        answer, confidence = await self._reconstitute_answer(
            activations,
            intersections,
            stimulus,
        )

        context = await self._format_context(
            activations,
            fibers_matched,
            max_tokens,
        )

        latency_ms = (time.perf_counter() - start_time) * 1000

        return RetrievalResult(
            answer=answer,
            confidence=confidence,
            depth_used=depth,
            neurons_activated=len(activations),
            fibers_matched=[f.id for f in fibers_matched],
            subgraph=subgraph,
            context=context,
            latency_ms=latency_ms,
            metadata={
                "query_intent": stimulus.intent.value,
                "anchors_found": sum(len(a) for a in anchor_sets),
                "intersections": len(intersections),
            },
        )

    def _detect_depth(self, stimulus: Stimulus) -> DepthLevel:
        """Auto-detect required depth from query intent."""
        # Deep questions need full exploration
        if stimulus.intent in (QueryIntent.ASK_WHY, QueryIntent.ASK_FEELING):
            return DepthLevel.DEEP

        # Pattern questions need cross-time analysis
        if stimulus.intent == QueryIntent.ASK_PATTERN:
            return DepthLevel.HABIT

        # Contextual questions need some exploration
        if stimulus.intent in (QueryIntent.ASK_HOW, QueryIntent.COMPARE):
            return DepthLevel.CONTEXT

        # Check for context keywords
        context_words = {"before", "after", "then", "trước", "sau", "rồi"}
        query_words = set(stimulus.raw_query.lower().split())
        if query_words & context_words:
            return DepthLevel.CONTEXT

        # Simple queries use instant retrieval
        return DepthLevel.INSTANT

    def _depth_to_hops(self, depth: DepthLevel) -> int:
        """Convert depth level to maximum hops."""
        mapping = {
            DepthLevel.INSTANT: 1,
            DepthLevel.CONTEXT: 3,
            DepthLevel.HABIT: 4,
            DepthLevel.DEEP: self._config.max_spread_hops,
        }
        return mapping.get(depth, 2)

    async def _find_anchors(self, stimulus: Stimulus) -> list[list[str]]:
        """Find anchor neurons for each signal type."""
        anchor_sets: list[list[str]] = []

        # Time anchors
        time_anchors: list[str] = []
        for hint in stimulus.time_hints:
            neurons = await self._storage.find_neurons(
                type=NeuronType.TIME,
                time_range=(hint.absolute_start, hint.absolute_end),
                limit=5,
            )
            time_anchors.extend(n.id for n in neurons)

        if time_anchors:
            anchor_sets.append(time_anchors)

        # Entity anchors
        entity_anchors: list[str] = []
        for entity in stimulus.entities:
            neurons = await self._storage.find_neurons(
                content_contains=entity.text,
                limit=3,
            )
            entity_anchors.extend(n.id for n in neurons)

        if entity_anchors:
            anchor_sets.append(entity_anchors)

        # Keyword anchors
        keyword_anchors: list[str] = []
        for keyword in stimulus.keywords[:5]:  # Limit keywords
            neurons = await self._storage.find_neurons(
                content_contains=keyword,
                limit=2,
            )
            keyword_anchors.extend(n.id for n in neurons)

        if keyword_anchors:
            anchor_sets.append(keyword_anchors)

        return anchor_sets

    async def _find_matching_fibers(
        self,
        activations: dict[str, ActivationResult],
    ) -> list[Fiber]:
        """Find fibers that contain activated neurons."""
        fibers: list[Fiber] = []
        seen_fiber_ids: set[str] = set()

        # Get highly activated neurons
        top_neurons = sorted(
            activations.values(),
            key=lambda a: a.activation_level,
            reverse=True,
        )[:20]

        for activation in top_neurons:
            matching = await self._storage.find_fibers(
                contains_neuron=activation.neuron_id,
                limit=3,
            )

            for fiber in matching:
                if fiber.id not in seen_fiber_ids:
                    fibers.append(fiber)
                    seen_fiber_ids.add(fiber.id)

        # Sort by salience
        fibers.sort(key=lambda f: f.salience, reverse=True)

        return fibers[:10]  # Limit to top 10

    async def _reconstitute_answer(
        self,
        activations: dict[str, ActivationResult],
        intersections: list[str],
        stimulus: Stimulus,
    ) -> tuple[str | None, float]:
        """
        Attempt to reconstitute an answer from activated neurons.

        Returns (answer_text, confidence)
        """
        if not activations:
            return None, 0.0

        # Find the most relevant neurons
        candidates: list[tuple[str, float]] = []

        # Prioritize intersection neurons
        for neuron_id in intersections:
            if neuron_id in activations:
                candidates.append((neuron_id, activations[neuron_id].activation_level * 1.5))

        # Add highly activated neurons
        for neuron_id, result in activations.items():
            if neuron_id not in intersections:
                candidates.append((neuron_id, result.activation_level))

        # Sort by score
        candidates.sort(key=lambda x: x[1], reverse=True)

        if not candidates:
            return None, 0.0

        # Get the top neuron's content as answer
        top_neuron_id = candidates[0][0]
        top_neuron = await self._storage.get_neuron(top_neuron_id)

        if top_neuron is None:
            return None, 0.0

        # Confidence based on activation and intersection count
        confidence = min(1.0, candidates[0][1])
        if intersections:
            confidence = min(1.0, confidence + 0.1 * len(intersections))

        return top_neuron.content, confidence

    async def _format_context(
        self,
        activations: dict[str, ActivationResult],
        fibers: list[Fiber],
        max_tokens: int,
    ) -> str:
        """Format activated memories into context for agent injection."""
        lines: list[str] = []
        token_estimate = 0

        # Add fiber summaries first
        if fibers:
            lines.append("## Relevant Memories\n")

            for fiber in fibers[:5]:
                if fiber.summary:
                    line = f"- {fiber.summary}"
                else:
                    anchor = await self._storage.get_neuron(fiber.anchor_neuron_id)
                    if anchor:
                        line = f"- {anchor.content}"
                    else:
                        continue

                token_estimate += len(line.split())
                if token_estimate > max_tokens:
                    break

                lines.append(line)

        # Add individual activated neurons
        if token_estimate < max_tokens:
            lines.append("\n## Related Information\n")

            sorted_activations = sorted(
                activations.values(),
                key=lambda a: a.activation_level,
                reverse=True,
            )

            for result in sorted_activations[:20]:
                neuron = await self._storage.get_neuron(result.neuron_id)
                if neuron is None:
                    continue

                # Skip time neurons in context (they're implicit)
                if neuron.type == NeuronType.TIME:
                    continue

                line = f"- [{neuron.type.value}] {neuron.content}"
                token_estimate += len(line.split())

                if token_estimate > max_tokens:
                    break

                lines.append(line)

        return "\n".join(lines)

    async def query_with_stimulus(
        self,
        stimulus: Stimulus,
        depth: DepthLevel | None = None,
        max_tokens: int | None = None,
    ) -> RetrievalResult:
        """
        Execute retrieval with a pre-parsed stimulus.

        Useful when you want to control the parsing or reuse a stimulus.

        Args:
            stimulus: Pre-parsed stimulus
            depth: Retrieval depth
            max_tokens: Maximum tokens in context

        Returns:
            RetrievalResult
        """
        # Reconstruct query string for the main method
        return await self.query(
            stimulus.raw_query,
            depth=depth,
            max_tokens=max_tokens,
        )
