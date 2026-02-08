# NeuralMemory Roadmap: v0.14.0 → v1.0.0

> From associative reflex engine to portable consciousness platform.
> Every feature passes the VISION.md 4-question test + brain test.
> ZERO LLM dependency — pure algorithmic, regex, graph-based.

**Current state**: v0.17.0 (987 tests, schema v9).
v0.14.0 shipped: relation extraction, tag origin, confirmatory boost.
v0.15.0 shipped: associative inference, co-activation persistence, tag normalization.
v0.16.0 shipped: emotional valence, sentiment extraction, FELT synapses, emotional decay.
v0.17.0 shipped: brain diagnostics, purity score, nmem_health MCP tool + CLI.

---

## Table of Contents

- [Expert Feedback Summary](#expert-feedback-summary)
- [v0.14.0 — Relation Extraction Engine](#v0140--relation-extraction-engine)
- [v0.15.0 — Associative Inference](#v0150--associative-inference)
- [v0.16.0 — Emotional Valence](#v0160--emotional-valence)
- [v0.17.0 — Brain Diagnostics](#v0170--brain-diagnostics)
- [v0.18.0 — Advanced Consolidation](#v0180--advanced-consolidation)
- [v0.19.0 — Temporal Reasoning](#v0190--temporal-reasoning)
- [v1.0.0 — Portable Consciousness v2](#v100--portable-consciousness-v2)
- [Dependency Graph](#dependency-graph)
- [Gap Coverage Matrix](#gap-coverage-matrix)
- [Expert Feedback Coverage](#expert-feedback-coverage)
- [VISION.md Checklist Per Phase](#visionmd-checklist-per-phase)
- [Implementation Priority](#implementation-priority)

---

## Expert Feedback Summary

Four expert reviewers analyzed NeuralMemory v0.13.0 and identified critical architectural gaps:

| Expert | Role | Core Insight | Key Contribution |
|--------|------|-------------|-----------------|
| E1 | Architecture | Memory ingestion must be agent-agnostic. 3-layer tag model: structural / associative / semantic | "Agent = narrator, not architect" principle |
| E2 | Philosophy | Reflexive vs Cognitive memory. Cognitive enrichment needed | Synapse diversity matters more than tag quality |
| E3 | Pragmatic | Auto-synapses > auto-tags. Brain diversity is evolutionary | Dynamic purity score, accept + mitigate |
| E4 | Quality | Descriptive vs Functional tags. Semantic drift. Confirmation weighting | Tag origin tracking, ontology alignment, Hebbian tag confirmation |

### Expert 4's Unique Gaps (not covered by E1–E3)

1. **Tag origin tracking** — Tags should carry `origin` metadata (`auto` vs `agent`). Auto-tags for accuracy in recall, agent-tags for creativity in deep reasoning.
2. **Semantic drift / ontology alignment** — Multiple agents create "UI" vs "Frontend" vs "Client-side" → brain fragmentation. NM needs tag normalization.
3. **Confirmatory weight boost** — When agent tags overlap with auto-tags → Hebbian confirmation signal → boost synapse weights. Divergent agent tags → new association, needs validation.

---

## v0.14.0 — Relation Extraction Engine

> Auto-synapses from content: the brain wires itself.

**Release target**: Next after auto-tags merge.

### The Gap

`CAUSED_BY`, `LEADS_TO`, `BEFORE`, `AFTER`, `ENABLES`, `PREVENTS` synapse types are defined in `core/synapse.py` (29 types total) but are **never auto-created**. The only way to create causal/temporal synapses is manual agent input. A brain that can't wire its own causal relationships is a brain that can't reason about "why."

### Solution

#### 1. Relation extraction module (`extraction/relations.py`)

Regex-based pattern extraction for three relation families:

| Family | Patterns | Synapse Types |
|--------|----------|---------------|
| **Causal** | "because", "caused by", "due to", "as a result", "therefore", "so that", "vì", "nên", "do đó" | `CAUSED_BY`, `LEADS_TO` |
| **Comparative** | "better than", "worse than", "similar to", "unlike", "compared to", "tốt hơn", "giống như" | `SIMILAR_TO`, `CONTRADICTS` |
| **Sequential** | "then", "after", "before", "first...then", "followed by", "trước khi", "sau khi" | `BEFORE`, `AFTER` |

Each extracted relation produces a `RelationCandidate` with: source span, target span, relation type, confidence score (0.0–1.0).

#### 2. Integrate `suggest_memory_type()` into encoder

`suggest_memory_type()` in `core/memory_types.py` (lines 294–363) exists but is not called during encoding. Integrate it as a fallback when no explicit `memory_type` is provided, enabling auto type inference for every memory.

#### 3. Tag origin tracking (E4)

Transform `Fiber.tags: set[str]` into a richer structure that preserves origin metadata:

```python
# Current: tags = {"python", "api", "auth"}
# New: tags carry origin
TagEntry = namedtuple("TagEntry", ["tag", "origin"])  # origin: "auto" | "agent"

# Fiber gains:
#   - auto_tags: set[str]   (from _generate_auto_tags)
#   - agent_tags: set[str]  (from agent input)
#   - tags property: union of both (backward compatible)
```

- Auto-tags used for **accuracy** in recall scoring
- Agent-tags used for **creativity** in deep reasoning (depth 2–3)
- Storage: `typed_memories.tags` JSON gains `{"auto": [...], "agent": [...]}` format

#### 4. Confirmatory weight boost (E4)

When an agent-provided tag matches an auto-generated tag → Hebbian confirmation signal:
- Boost anchor synapse weight by **+0.1** (capped at 1.0)
- Log confirmation event for diagnostics
- Divergent agent tags (no auto-tag match) → create new `RELATED_TO` synapse with weight 0.3 (needs validation through use)

### Files

| Action | File | Changes |
|--------|------|---------|
| **New** | `extraction/relations.py` | Relation extraction engine (~300 lines) |
| **New** | `tests/unit/test_relation_extraction.py` | Comprehensive pattern tests (~250 lines) |
| **Modified** | `engine/encoder.py` | Add relation extraction step, auto type inference, tag origin, confirmation boost (~80 lines) |
| **Modified** | `core/fiber.py` | Tag origin fields (`auto_tags`, `agent_tags`, backward-compatible `tags` property) |
| **Modified** | `storage/sqlite_store.py` | Tag origin storage format |

### Scope

~600 new lines + ~80 modified lines + ~250 test lines

### VISION.md Check

| Question | Answer |
|----------|--------|
| Activation or Search? | Activation — auto-synapses create richer graph for spreading activation |
| Spreading activation still central? | Yes — more synapse types = more activation pathways |
| Works without embeddings? | Yes — pure regex pattern matching |
| More detailed query = faster? | Yes — causal queries activate precise chains instead of broad clusters |
| Brain test? | Yes — human brains auto-wire causal associations during encoding |

---

## v0.15.0 — Associative Inference

> Co-activation becomes persistent structure: neurons that fire together wire together.

**Depends on**: v0.14.0 (needs relation extraction for richer co-activation data).

### The Gap

`CoActivation` data is collected during retrieval (spreading activation records which neurons fire together) but is **never synthesized** into persistent synapses. The brain observes patterns but never learns from them. This is like a brain that notices associations but never forms memories of those associations.

### Solution

#### 1. Associative inference engine (`engine/associative_inference.py`)

Accumulate co-activation events across retrievals. When a neuron pair co-activates above a threshold:
- Create persistent `CO_OCCURS` synapse with weight proportional to co-activation frequency
- Track co-activation history for confidence scoring
- Prune inferred synapses that stop being reinforced (natural forgetting)

**Threshold**: 3 co-activations within 7 days → create synapse (configurable).

#### 2. New `INFER` consolidation strategy

Add to `ConsolidationStrategy` enum in `engine/consolidation.py`:
```python
INFER = "infer"  # Create synapses from co-activation patterns
```

Run during consolidation cycle alongside PRUNE/MERGE/SUMMARIZE.

#### 3. Associative tag generation (E1's Layer 2)

E1's 3-layer tag model:
- **Layer 1 (Structural)**: Entity/keyword tags — already implemented in auto-tags
- **Layer 2 (Associative)**: Tags inferred from co-activation clusters — **this phase**
- **Layer 3 (Semantic)**: Abstract concept tags from pattern extraction — future (v0.18.0)

Generate associative tags from frequently co-activated neuron groups. Example: if "Redis", "cache", "performance" neurons co-activate 5+ times → infer associative tag "caching-infrastructure".

#### 4. Tag normalization / ontology alignment (E4)

New module `utils/tag_normalizer.py`:

```python
class TagNormalizer:
    # Static synonym map
    SYNONYMS = {
        "frontend": ["ui", "client-side", "client side", "front-end"],
        "backend": ["server-side", "server side", "back-end"],
        "database": ["db", "datastore", "data store"],
        ...
    }

    def normalize(self, tag: str) -> str:
        """Map tag to canonical form via synonyms + SimHash near-match."""

    def detect_drift(self, tags: list[str]) -> list[DriftReport]:
        """Flag tags that are likely synonyms but stored separately."""
```

- **Synonym map**: Curated set of common software/general synonyms
- **SimHash near-match**: Use existing SimHash infrastructure (from v0.13.0 dedup) to detect similar tags that aren't in the synonym map
- Applied during encoding (normalize new tags) and consolidation (detect drift in existing tags)

### Files

| Action | File | Changes |
|--------|------|---------|
| **New** | `engine/associative_inference.py` | Co-activation → synapse inference (~300 lines) |
| **New** | `utils/tag_normalizer.py` | Synonym map + SimHash tag normalization (~200 lines) |
| **New** | `tests/unit/test_associative_inference.py` | Inference threshold + edge cases (~200 lines) |
| **New** | `tests/unit/test_tag_normalizer.py` | Normalization + drift detection (~100 lines) |
| **Modified** | `engine/retrieval.py` | Record co-activation events for inference (~40 lines) |
| **Modified** | `engine/consolidation.py` | Add INFER strategy (~50 lines) |
| **Modified** | `storage/sqlite_store.py` | Co-activation event storage (~30 lines) |

### Scope

~500 new lines + ~120 modified lines + ~300 test lines

### VISION.md Check

| Question | Answer |
|----------|--------|
| Activation or Search? | Activation — inferred synapses create new activation pathways |
| Spreading activation still central? | Yes — more connections = richer spreading |
| Works without embeddings? | Yes — pure co-activation counting |
| More detailed query = faster? | Yes — inferred links provide shortcuts |
| Brain test? | Yes — Hebbian learning: "neurons that fire together wire together" |

---

## v0.16.0 — Emotional Valence

> Memories gain emotional color: the brain feels, not just knows.

**Independent**: Can be built in parallel with v0.15.0 or v0.17.0.

### The Gap

`FELT` and `EVOKES` synapse types exist in `core/synapse.py` but **nothing creates them**. Emotional context is a fundamental dimension of biological memory — traumatic memories persist longer, positive associations strengthen recall. Without valence, the brain is purely logical.

### Solution

#### 1. Sentiment extraction (`extraction/sentiment.py`)

Regex/lexicon-based sentiment analysis — NO LLM dependency:

```python
class Valence(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

@dataclass(frozen=True)
class SentimentResult:
    valence: Valence
    intensity: float      # 0.0 – 1.0
    emotion_tags: set[str]  # {"frustration", "satisfaction", ...}
```

**Approach**:
- Curated lexicon: ~200 positive + ~200 negative words (English + Vietnamese)
- Negation handling: "not good" → negative
- Intensifier handling: "very frustrated" → higher intensity
- Emotion tag mapping: word clusters → emotion categories (frustration, satisfaction, confusion, excitement, etc.)

#### 2. Emotional synapses at encode time

During encoding in `engine/encoder.py`:
- Run sentiment extraction on content
- If non-neutral: create `FELT` synapse from anchor neuron to emotion concept neuron
- Emotion concept neurons are shared across fibers (reused, not duplicated)

#### 3. Valence-aware retrieval scoring

In `engine/retrieval.py`, add emotional resonance to score breakdown:
- Queries with emotional content (e.g., "frustrated about the bug") get a boost for matching-valence fibers
- Score component: `emotional_resonance` (0.0–0.1 range)

#### 4. Emotional decay modulation

Extend type-aware decay (v0.13.0):
- High-intensity negative memories decay **slower** (trauma persistence)
- High-intensity positive memories decay **slightly slower** (reward reinforcement)
- Neutral memories follow standard decay curves

### Files

| Action | File | Changes |
|--------|------|---------|
| **New** | `extraction/sentiment.py` | Lexicon-based sentiment analysis (~250 lines) |
| **New** | `tests/unit/test_sentiment.py` | Sentiment accuracy + edge cases (~200 lines) |
| **Modified** | `engine/encoder.py` | Sentiment extraction step + FELT synapse creation (~40 lines) |
| **Modified** | `engine/retrieval.py` | Valence-aware scoring component (~40 lines) |

### Scope

~250 new lines + ~80 modified lines + ~200 test lines

### VISION.md Check

| Question | Answer |
|----------|--------|
| Activation or Search? | Activation — emotional synapses are new activation pathways |
| Spreading activation still central? | Yes — emotion nodes become high-connectivity hubs |
| Works without embeddings? | Yes — pure lexicon matching |
| More detailed query = faster? | Yes — emotional context narrows activation |
| Brain test? | Yes — emotional valence is fundamental to biological memory |

---

## v0.17.0 — Brain Diagnostics

> Know thy brain: quality metrics, health reports, actionable insights.

**Independent**: Can be built in parallel with v0.15.0 or v0.16.0.

### The Gap

No purity score, no activation efficiency metrics, no diagnostic tools. Users can't assess brain quality, detect fragmentation, or identify structural problems. Flying blind.

### Solution

#### 1. Diagnostics engine (`engine/diagnostics.py`)

```python
@dataclass(frozen=True)
class BrainHealthReport:
    # Overall health
    purity_score: float        # 0–100, weighted composite
    grade: str                 # A/B/C/D/F

    # Component scores
    connectivity: float        # Avg synapses per neuron (target: 3–8)
    diversity: float           # Synapse type distribution entropy
    freshness: float           # % of fibers accessed in last 7 days
    consolidation_ratio: float # Semantic fibers / total fibers
    orphan_rate: float         # Neurons with 0 synapses / total

    # Activation metrics
    avg_activation_efficiency: float  # Queries reaching depth-0 / total
    avg_recall_confidence: float      # Mean reconstruction confidence

    # Structural warnings
    warnings: list[DiagnosticWarning]
    recommendations: list[str]
```

**Purity score formula** (E3's dynamic purity):
```
purity = (
    connectivity_score * 0.25 +
    diversity_score * 0.20 +
    freshness_score * 0.15 +
    consolidation_score * 0.15 +
    (1 - orphan_rate) * 0.10 +
    activation_efficiency * 0.10 +
    recall_confidence * 0.05
) * 100
```

#### 2. Semantic drift detection (E4)

Part of diagnostics: scan all tags across fibers and flag likely synonyms:
- Use `TagNormalizer.detect_drift()` from v0.15.0 (or include it here if v0.15.0 not yet shipped)
- Report synonym clusters: `{"UI", "Frontend", "Client-side"}` → recommend normalization
- Include in `BrainHealthReport.warnings`

#### 3. MCP tool: `nmem_health`

New MCP tool exposing diagnostics:
```
nmem_health → BrainHealthReport (JSON)
```

#### 4. CLI command: `nmem health`

```
$ nmem health
Brain: default
Grade: B (78/100)

Connectivity:     ████████░░  8.2 synapses/neuron (good)
Diversity:        ██████░░░░  6 of 29 synapse types used (moderate)
Freshness:        █████████░  91% accessed this week (excellent)
Consolidation:    ████░░░░░░  12% semantic (low — run consolidation)
Orphan rate:      █░░░░░░░░░  3% orphaned (excellent)

Warnings:
  ⚠ Tag drift detected: {"UI", "Frontend"} — consider normalization
  ⚠ Low synapse diversity — only RELATED_TO and CO_OCCURS used

Recommendations:
  → Run `nmem consolidate --strategy mature` to advance episodic memories
  → Causal patterns detected but no CAUSED_BY synapses — upgrade to v0.14.0+
```

### Files

| Action | File | Changes |
|--------|------|---------|
| **New** | `engine/diagnostics.py` | BrainHealthReport + scoring (~350 lines) |
| **New** | `tests/unit/test_diagnostics.py` | Score calculation + edge cases (~200 lines) |
| **Modified** | `mcp/tool_schemas.py` | `nmem_health` tool schema (~20 lines) |
| **Modified** | `mcp/server.py` | `nmem_health` handler (~30 lines) |
| **Modified** | `cli/commands/info.py` | `health` subcommand (~60 lines) |

### Scope

~450 new lines + ~60 modified lines (MCP/CLI) + ~200 test lines

### VISION.md Check

| Question | Answer |
|----------|--------|
| Activation or Search? | Meta — diagnostics improve the activation network itself |
| Spreading activation still central? | Yes — diagnostics measure activation quality |
| Works without embeddings? | Yes — pure graph metrics |
| More detailed query = faster? | N/A (diagnostic tool, not query feature) |
| Brain test? | Yes — self-awareness / metacognition is a brain function |

---

## v0.18.0 — Advanced Consolidation + Workflow Detection

> The brain sleeps, dreams, learns habits, and wakes up smarter.

**Depends on**: v0.14.0 (relation extraction), v0.15.0 (associative inference + co-activation data).

### The Gaps

**Gap 1 — No knowledge creation**: No `ENRICH` strategy, no transitive inference, no dream-like consolidation. Current consolidation (PRUNE/MERGE/SUMMARIZE/MATURE/INFER) handles cleanup, compression, and co-activation inference but doesn't create **new knowledge from existing knowledge**. A brain that can't dream can't make novel connections.

**Gap 2 — No habit learning**: The brain tracks frequency (fiber.frequency, neuron.access_frequency) and co-activation (pairs) but cannot detect **ordered sequences of repeated actions**. A brain that can't recognize habits can't suggest workflows.

### Solution — Part A: Advanced Consolidation

#### 1. `ENRICH` consolidation strategy

Add to `ConsolidationStrategy`:
```python
ENRICH = "enrich"  # Create new synapses via transitive inference
```

**Transitive closure**: If A→CAUSED_BY→B and B→CAUSED_BY→C, infer A→CAUSED_BY→C with reduced weight (0.5 × min(w_AB, w_BC)).

**Cross-cluster links**: Find fibers in different tag clusters that share entity neurons → create `RELATED_TO` synapses between their anchors.

#### 2. `DREAM` consolidation strategy

```python
DREAM = "dream"  # Random activation for hidden connections
```

**Algorithm**:
1. Select N random neurons (configurable, default 5)
2. Run spreading activation from each
3. Record unexpected co-activations (neurons that wouldn't normally co-activate)
4. If unexpected co-activation count > threshold → create weak `RELATED_TO` synapse (weight 0.1)
5. These "dream synapses" must be reinforced through actual use or they decay quickly (10× normal decay rate)

This is E1's Layer 3 (semantic) tag generation via emergent concept discovery.

#### 3. Importance-based retention

During PRUNE strategy:
- High-salience fibers (salience > 0.8) resist pruning even if inactive
- Fibers with many inbound synapses (hub neurons) get decay protection
- Emotional fibers (from v0.16.0, if available) decay slower

### Solution — Part B: Workflow Detection

> "Actions that sequence together template together."

Transform repeated user behavior patterns into named workflow templates with proactive suggestions.

#### 4. Action event log (`storage/action_log.py`)

Persistent, ordered log of user actions within sessions:

```python
@dataclass(frozen=True)
class ActionEvent:
    id: str
    brain_id: str
    session_id: str          # Groups actions within a session
    action_type: str         # "remember", "recall", "encode", "consolidate", etc.
    action_context: str      # Content summary / query text (truncated)
    tags: frozenset[str]     # Tags involved in this action
    fiber_id: str | None     # Fiber created/accessed (if applicable)
    created_at: datetime
```

Schema migration adds `action_events` table. Storage interface: `record_action()`, `get_action_sequences()`, `prune_action_events()`.

#### 5. Sequence mining engine (`engine/sequence_mining.py`)

Detects repeated ordered subsequences across sessions:

```python
@dataclass(frozen=True)
class WorkflowCandidate:
    steps: tuple[str, ...]       # Ordered action types: ("recall", "encode", "consolidate")
    frequency: int               # Number of sessions containing this sequence
    avg_duration_seconds: float  # Avg time from first to last step
    context_tags: frozenset[str] # Common tags across occurrences
    confidence: float            # 0.0–1.0 based on frequency + consistency

@dataclass(frozen=True)
class WorkflowTemplate:
    id: str
    name: str                    # Auto-generated: "dev-cycle", "debug-fix-verify"
    steps: tuple[str, ...]
    trigger_context: frozenset[str]  # Tags/actions that trigger suggestion
    frequency: int
    confidence: float
```

**Algorithm**: Sliding-window subsequence extraction → frequency counting → filter by min_frequency (default: 3 sessions) → rank by confidence → deduplicate overlapping sequences.

- **No LLM dependency**: Pure frequency-based pattern mining (inspired by PrefixSpan but simplified for action sequences)
- **Naming heuristic**: Join action types with "-" → "recall-encode-consolidate" → shorten common patterns ("dev-cycle", "debug-fix", etc.)

#### 6. `LEARN_HABITS` consolidation strategy

```python
LEARN_HABITS = "learn_habits"  # Extract workflow templates from action logs
```

Run during consolidation alongside ENRICH/DREAM:
1. Query action sequences from last N days (configurable window)
2. Run sequence mining → workflow candidates
3. Promote candidates above confidence threshold to `WorkflowTemplate`
4. Store templates as special WORKFLOW-typed fibers with `_workflow_template: True` metadata
5. Prune old action events outside the window

#### 7. Proactive workflow suggestion

During retrieval, after assembling the response:
1. Check current action context (what the user just did)
2. Match against stored workflow templates by trigger_context overlap
3. If match found with confidence > 0.7: include suggestion in retrieval metadata

```python
@dataclass(frozen=True)
class WorkflowSuggestion:
    template_id: str
    template_name: str
    next_steps: tuple[str, ...]   # Remaining steps in the workflow
    confidence: float
    message: str                  # "You usually do X next. Continue?"
```

Exposed via:
- **MCP tool**: `nmem_suggest` → returns active workflow suggestions
- **CLI**: `nmem suggest` → show current workflow suggestions
- **Retrieval metadata**: `RetrievalResult.workflow_suggestions: list[WorkflowSuggestion]`

### Files

| Action | File | Changes |
|--------|------|---------|
| **Modified** | `engine/consolidation.py` | ENRICH + DREAM + LEARN_HABITS strategies (~350 lines) |
| **Modified** | `engine/pattern_extraction.py` | Transitive closure helper (~100 lines) |
| **New** | `storage/action_log.py` | ActionEvent storage mixin (~80 lines) |
| **New** | `engine/sequence_mining.py` | Sequence mining + WorkflowTemplate (~250 lines) |
| **New** | `engine/workflow_suggest.py` | Proactive suggestion engine (~100 lines) |
| **Modified** | `engine/retrieval.py` | Attach workflow suggestions to results (~30 lines) |
| **Modified** | `storage/sqlite_schema.py` | action_events table migration (~20 lines) |
| **Modified** | `storage/base.py` | Action log abstract methods (~20 lines) |
| **Modified** | `mcp/tool_schemas.py` | `nmem_suggest` tool schema (~15 lines) |
| **Modified** | `mcp/server.py` | `nmem_suggest` handler (~20 lines) |
| **New** | `tests/unit/test_enrichment.py` | Transitive inference + dream tests (~200 lines) |
| **New** | `tests/unit/test_sequence_mining.py` | Sequence extraction + workflow template tests (~200 lines) |
| **New** | `tests/unit/test_workflow_suggest.py` | Proactive suggestion tests (~150 lines) |

### Scope

~950 new lines + ~555 modified lines + ~550 test lines

### VISION.md Check

| Question | Answer |
|----------|--------|
| Activation or Search? | Activation — DREAM uses spreading activation; workflow templates create new activation shortcuts |
| Spreading activation still central? | Yes — DREAM literally uses it; workflow suggestions augment retrieval results |
| Works without embeddings? | Yes — graph traversal + frequency-based sequence mining |
| More detailed query = faster? | Yes — enrichment creates shortcuts; workflows predict next action |
| Brain test? | Yes — dreaming, transitive inference, and habit formation are core brain functions |

---

## v0.19.0 — Temporal Reasoning

> "Why did this happen?" — trace the causal chain. "When?" — query time ranges.

**Depends on**: v0.14.0 (needs auto-created causal/temporal synapses to traverse).

### The Gap

"Why?" queries can't trace `CAUSED_BY` chains — the router identifies causal intent (in `extraction/router.py`) but retrieval has no causal traversal algorithm. "When?" queries can't do temporal range filtering beyond basic time bounds. Event sequences aren't first-class query results.

### Solution

#### 1. Causal traversal engine (`engine/causal_traversal.py`)

```python
def trace_causal_chain(
    store: SQLiteStore,
    brain_id: str,
    fiber_id: str,
    direction: Literal["causes", "effects"],
    max_depth: int = 5,
) -> CausalChain:
    """Follow CAUSED_BY/LEADS_TO synapses to build a causal chain."""

def query_temporal_range(
    store: SQLiteStore,
    brain_id: str,
    start: datetime,
    end: datetime,
    memory_types: set[MemoryType] | None = None,
) -> list[Fiber]:
    """Retrieve fibers within a temporal range, ordered chronologically."""

def trace_event_sequence(
    store: SQLiteStore,
    brain_id: str,
    seed_fiber_id: str,
    direction: Literal["forward", "backward"],
    max_steps: int = 10,
) -> EventSequence:
    """Follow BEFORE/AFTER synapses to reconstruct event sequences."""
```

#### 2. New synthesis methods

Add to `SynthesisMethod` in `engine/reconstruction.py`:
```python
CAUSAL_CHAIN = "causal_chain"        # "A because B because C"
TEMPORAL_SEQUENCE = "temporal_sequence"  # "First A, then B, then C"
```

Reconstruction formats the chain/sequence into natural language output.

#### 3. Router integration

Enhance `extraction/router.py` to route:
- "Why?" queries → causal traversal → `CAUSAL_CHAIN` synthesis
- "When?" queries → temporal range → `TEMPORAL_SEQUENCE` synthesis
- "What happened after X?" → event sequence → `TEMPORAL_SEQUENCE` synthesis

### Files

| Action | File | Changes |
|--------|------|---------|
| **New** | `engine/causal_traversal.py` | Causal chain + temporal range + event sequence (~300 lines) |
| **New** | `tests/unit/test_causal_traversal.py` | Chain traversal + edge cases (~200 lines) |
| **Modified** | `engine/reconstruction.py` | CAUSAL_CHAIN + TEMPORAL_SEQUENCE synthesis (~60 lines) |
| **Modified** | `extraction/router.py` | Route causal/temporal queries to traversal (~40 lines) |

### Scope

~300 new lines + ~100 modified lines + ~200 test lines

### VISION.md Check

| Question | Answer |
|----------|--------|
| Activation or Search? | Activation — causal traversal IS directed activation along causal synapses |
| Spreading activation still central? | Yes — causal traversal is constrained spreading activation |
| Works without embeddings? | Yes — pure graph traversal |
| More detailed query = faster? | Yes — "Why did X fail?" traverses a specific causal chain |
| Brain test? | Yes — causal reasoning is fundamental to human cognition |

---

## v1.0.0 — Portable Consciousness v2

> Marketplace foundations: brains become products.

**Depends on**: v0.17.0 (diagnostics for brain quality rating), all prior versions for stable API surface.

### Features

#### 1. Brain versioning
- Snapshot history: save named versions of brain state
- Rollback: restore any previous version
- Diff: compare two versions (neurons/synapses added/removed)
- Storage: version metadata in `brain_versions` table

#### 2. Partial brain transplant
- Topic-filtered merge: extract fibers matching tag/type filters from one brain
- Import into target brain with conflict resolution
- Preserve synapse structure within the transplanted subgraph
- Example: "transplant all Python knowledge from expert-brain to my-brain"

#### 3. Brain quality rating
- Grade A–F derived from `BrainHealthReport` (v0.17.0)
- Quality badge for marketplace display
- Minimum grade requirements for marketplace listing (B or above)
- Auto-computed, not self-reported

#### 4. Stable API guarantee
- Semantic versioning from v1.0.0 onward
- Public API surface documented and frozen
- Deprecation policy: 2 minor versions before removal
- Migration guides for breaking changes

#### 5. Documentation
- API reference (auto-generated from schemas)
- Architecture guide
- Brain marketplace specification
- Migration guide from v0.x → v1.0

### Files

| Action | File | Changes |
|--------|------|---------|
| **New** | `engine/brain_versioning.py` | Snapshot + rollback + diff (~300 lines) |
| **New** | `engine/brain_transplant.py` | Topic-filtered merge (~200 lines) |
| **Modified** | `engine/diagnostics.py` | Quality grade computation (~50 lines) |
| **Modified** | `storage/sqlite_store.py` | Version table + transplant queries (~100 lines) |
| **Modified** | `storage/sqlite_schema.py` | `brain_versions` table migration (~30 lines) |
| **New** | `tests/unit/test_brain_versioning.py` | Snapshot + rollback tests (~200 lines) |
| **New** | `tests/unit/test_brain_transplant.py` | Filtered merge tests (~150 lines) |

### Scope

~500 new lines + ~150 modified lines + ~350 test lines

### VISION.md Check

| Question | Answer |
|----------|--------|
| Activation or Search? | Activation — transplanted subgraphs preserve activation structure |
| Spreading activation still central? | Yes — versioning/transplant don't change the core algorithm |
| Works without embeddings? | Yes — pure graph operations |
| More detailed query = faster? | N/A (infrastructure, not query feature) |
| Brain test? | Yes — brain transplants are real (well, almost). Versioning = memory snapshots |

---

## Dependency Graph

```
v0.14.0 ✅ (Relation Extraction)
  ├──→ v0.15.0 ✅ (Associative Inference)
  │       └──→ v0.18.0 (Advanced Consolidation + Workflow Detection)
  └──→ v0.19.0 (Temporal Reasoning)

v0.16.0 ✅ (Emotional Valence)     ← shipped
v0.17.0 ✅ (Brain Diagnostics)     ← shipped
  └──→ v1.0.0 (Portable Consciousness v2)
```

**Critical path**: ~~v0.14.0 → v0.15.0~~ → v0.18.0 (v0.14-v0.17 shipped)

**Parallelizable**:
- v0.19.0 only needs v0.14.0 ✅ (can start now)
- v0.18.0 needs v0.14.0 ✅ + v0.15.0 ✅ (can start now)

---

## Gap Coverage Matrix

### 7 Critical Architectural Gaps

| # | Gap | Status Before | Resolved In |
|---|-----|---------------|-------------|
| G1 | Causal/temporal synapses never auto-created | 29 synapse types defined, 0 auto-created | **v0.14.0** ✅ |
| G2 | Co-activation never synthesized into synapses | Data collected, never used | **v0.15.0** ✅ |
| G3 | Emotional synapses (`FELT`/`EVOKES`) never created | Types exist, unused | **v0.16.0** ✅ |
| G4 | No brain health metrics or diagnostics | Flying blind | **v0.17.0** ✅ |
| G5 | No enrichment or dream consolidation | Only PRUNE/MERGE/SUMMARIZE/MATURE/INFER | **v0.18.0** |
| G6 | "Why?" and "When?" queries can't trace chains | Router detects intent, no traversal | **v0.19.0** |
| G7 | No brain versioning or partial transplant | Export/import only (all-or-nothing) | **v1.0.0** |
| G8 | No habit/workflow detection from repeated actions | Frequency tracked but sequences ignored | **v0.18.0** |

### Expert 4's 3 New Gaps

| # | Gap | Resolved In |
|---|-----|-------------|
| E4-1 | Tag origin tracking (auto vs agent) | **v0.14.0** |
| E4-2 | Semantic drift / ontology alignment | **v0.15.0** (normalizer) + **v0.17.0** (detection) |
| E4-3 | Confirmatory weight boost (Hebbian tag confirmation) | **v0.14.0** |

---

## Expert Feedback Coverage

| Expert | Key Point | Phase |
|--------|-----------|-------|
| **E1** | Agent-agnostic ingestion | v0.14.0 (auto type inference, auto relations) |
| **E1** | Layer 1 tags (structural) | v0.13.0 ✓ (auto-tags, already implemented) |
| **E1** | Layer 2 tags (associative) | v0.15.0 (co-activation → tags) |
| **E1** | Layer 3 tags (semantic) | v0.18.0 (DREAM consolidation → emergent concepts) |
| **E2** | Reflexive vs Cognitive memory | v0.14.0+ (auto-synapses = reflexive wiring) |
| **E2** | Cognitive enrichment | v0.18.0 (ENRICH strategy) |
| **E2** | Synapse diversity > tag quality | v0.14.0–v0.18.0 (each phase adds new synapse creation paths) |
| **E3** | Auto-synapses > auto-tags | v0.14.0 (relation extraction = auto-synapses) |
| **E3** | Dynamic purity score | v0.17.0 (BrainHealthReport.purity_score) |
| **E3** | Accept + mitigate (brain diversity is evolutionary) | v0.15.0 (normalize) + v0.18.0 (DREAM validates via use) |
| **E4** | Tag origin tracking | v0.14.0 (auto_tags/agent_tags split) |
| **E4** | Semantic drift / ontology alignment | v0.15.0 (TagNormalizer) + v0.17.0 (drift detection) |
| **E4** | Confirmatory weight boost (Hebbian) | v0.14.0 (agent tag ∩ auto tag → +0.1 weight) |
| **E4** | Descriptive vs Functional tags | v0.14.0 (origin tracking enables differential use) |

---

## VISION.md Checklist Per Phase

Each phase must pass all 4 questions + brain test before implementation begins.

| Phase | Q1: Activation? | Q2: Spreading central? | Q3: No embeddings? | Q4: Detail = fast? | Brain test? |
|-------|-----------------|----------------------|--------------------|--------------------|-------------|
| v0.14.0 | ✓ Auto-synapses | ✓ More pathways | ✓ Regex | ✓ Precise chains | ✓ Causal wiring |
| v0.15.0 | ✓ Inferred links | ✓ Richer graph | ✓ Counting | ✓ Shortcuts | ✓ Hebbian learning |
| v0.16.0 | ✓ Emotion paths | ✓ Emotion hubs | ✓ Lexicon | ✓ Emotional focus | ✓ Emotional memory |
| v0.17.0 | ✓ Meta-quality | ✓ Measures it | ✓ Graph metrics | N/A | ✓ Metacognition |
| v0.18.0 | ✓ Dream links | ✓ DREAM uses it | ✓ Graph ops | ✓ Transitive shortcuts | ✓ Dream consolidation |
| v0.19.0 | ✓ Causal activation | ✓ Directed spreading | ✓ Graph traversal | ✓ Precise chains | ✓ Causal reasoning |
| v1.0.0 | ✓ Preserved structure | ✓ Unchanged | ✓ Graph ops | N/A | ✓ Memory snapshots |

---

## Implementation Priority

Ranked by impact × feasibility:

| Rank | Phase | Impact | Feasibility | Rationale |
|------|-------|--------|-------------|-----------|
| 1 | **v0.14.0** ✅ | Critical | High | Shipped. Relation extraction, tag origin, confirmatory boost. |
| 2 | **v0.15.0** ✅ | High | Medium | Shipped. Associative inference, co-activation, tag normalization. |
| 3 | **v0.17.0** ✅ | High | High | Shipped. Brain diagnostics, purity score, nmem_health MCP + CLI. |
| 4 | **v0.16.0** ✅ | Medium | High | Shipped. Emotional valence, sentiment extraction, FELT synapses, emotional decay. |
| 5 | **v0.19.0** | High | Medium | Fills VISION.md Pillar 2 (Temporal & Causal). Needs v0.14.0 first. |
| 6 | **v0.18.0** | High | Medium | DREAM + ENRICH + Workflow Detection. Largest scope but high differentiator (habit learning). Needs v0.14.0 ✅ + v0.15.0 ✅. |
| 7 | **v1.0.0** | Critical | Low | Largest scope. Marketplace foundations. Needs everything else stable. |

### Recommended execution order

```
v0.14.0 ✅ → v0.15.0 ✅ → v0.16.0 ✅ → v0.17.0 ✅ → v0.19.0 → v0.18.0 → v1.0.0
```

v0.17.0 and v0.19.0 can be developed in parallel — all dependencies met.

---

## Cumulative Scope Estimate

| Phase | New Lines | Modified Lines | Test Lines | Cumulative Tests (est.) |
|-------|-----------|---------------|------------|------------------------|
| v0.14.0 | ~600 | ~80 | ~250 | ~1,041 |
| v0.15.0 | ~500 | ~120 | ~300 | ~1,341 |
| v0.16.0 | ~250 | ~80 | ~200 | ~1,541 |
| v0.17.0 | ~450 | ~60 | ~200 | ~1,741 |
| v0.18.0 | ~950 | ~555 | ~550 | ~2,008 |
| v0.19.0 | ~300 | ~100 | ~200 | ~2,208 |
| v1.0.0 | ~500 | ~150 | ~350 | ~2,558 |
| **Total** | **~3,550** | **~1,145** | **~2,050** | **~2,558** |

Starting from 987 tests (v0.17.0) → targeting ~2,558 tests at v1.0.0.

---

*See [VISION.md](VISION.md) for the north star guiding all decisions.*
*Last updated: 2026-02-08 (v0.17.0 shipped: brain diagnostics)*
