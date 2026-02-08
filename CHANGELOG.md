# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.13.0] - 2026-02-07

### Added

- **Ground truth evaluation dataset**: 30 curated memories across 5 sessions (Day 1→Day 30) covering project setup, development, integration, sprint review, and production launch
- **Standard IR metrics**: Precision@K, Recall@K, MRR (Mean Reciprocal Rank), NDCG@K with per-query and per-category aggregation
- **25 evaluation queries**: 8 factual, 6 temporal, 4 causal, 4 pattern, 3 multi-session coherence queries with expected relevant results
- **Naive keyword-overlap baseline**: Tokenize-and-rank strawman that NeuralMemory's activation-based recall must beat
- **Long-horizon coherence test framework**: 5-session simulation across 30 days with recall tracking per session (target: >= 60% at day 30)
- `benchmarks/ground_truth.py` — ground truth memories, queries, session schedule
- `benchmarks/metrics.py` — IR metrics: `precision_at_k`, `recall_at_k`, `reciprocal_rank`, `ndcg_at_k`, `evaluate_query`, `BenchmarkReport`
- `benchmarks/naive_baseline.py` — keyword overlap ranking and baseline evaluation
- `benchmarks/coherence_test.py` — multi-session coherence test with `CoherenceReport`
- Ground-truth evaluation section in `run_benchmarks.py` comparing NeuralMemory vs baseline
- 27 new unit tests: precision (6), recall (4), MRR (5), NDCG (4), query evaluation (1), report aggregation (2), baseline (5)

### Changed

- `run_benchmarks.py` now includes ground-truth evaluation with NeuralMemory vs naive baseline comparison in generated markdown output

## [0.12.0] - 2026-02-07

### Added

- **Real-time conflict detection**: Detects factual contradictions and decision reversals at encode time using predicate extraction — no LLM required
- **Factual contradiction detection**: Regex-based extraction of `"X uses/chose/decided Y"` patterns, compares predicates across memories with matching subjects
- **Decision reversal detection**: Identifies when a new DECISION contradicts an existing one via tag overlap analysis
- **Dispute resolution pipeline**: Anti-Hebbian confidence reduction, `_disputed` and `_superseded` metadata markers, and CONTRADICTS synapse creation
- **Disputed neuron deprioritization**: Retrieval pipeline reduces activation of disputed neurons by 50% and superseded neurons by 75%
- `CONTRADICTS` synapse type for linking contradictory memories
- `ConflictType`, `Conflict`, `ConflictResolution`, `ConflictReport` in new `engine/conflict_detection.py`
- `detect_conflicts()`, `resolve_conflicts()` for encode-time conflict handling
- 32 new unit tests: predicate extraction (5), predicate conflict (4), subject matching (4), tag overlap (4), helpers (4), detection integration (6), resolution (5)

### Changed

- Encoder pipeline runs conflict detection after anchor neuron creation, before fiber assembly
- Retrieval pipeline adds `_deprioritize_disputed()` step after stabilization to suppress disputed neurons
- `SynapseType` enum extended with `CONTRADICTS = "contradicts"`

## [0.11.0] - 2026-02-07

### Added

- **Activation stabilization**: Iterative dampening algorithm settles neural activations into stable patterns after spreading activation — noise floor removal, dampening (0.85x), homeostatic normalization, convergence detection (typically 2-4 iterations)
- **Multi-neuron answer reconstruction**: Strategy-based answer synthesis replacing single-neuron `reconstitute_answer()` — SINGLE mode (high-confidence top neuron), FIBER_SUMMARY mode (best fiber summary), MULTI_NEURON mode (top-5 neurons ordered by fiber pathway position)
- **Memory maturation lifecycle**: Four-stage memory model STM → Working (30min) → Episodic (4h) → Semantic (7d + spacing effect). Stage-aware decay multipliers: STM 5x, Working 2x, Episodic 1x, Semantic 0.3x
- **Spacing effect requirement**: EPISODIC → SEMANTIC promotion requires reinforcement across 3+ distinct calendar days, modeling biological spaced repetition
- **Pattern extraction**: Episodic → semantic concept formation via tag Jaccard clustering (Union-Find). Clusters of 3+ similar fibers generate CONCEPT neurons with IS_A synapses to common entities
- **MATURE consolidation strategy**: New consolidation strategy that advances maturation stages and extracts semantic patterns from mature episodic memories
- `StabilizationConfig`, `StabilizationReport`, `stabilize()` in new `engine/stabilization.py`
- `SynthesisMethod`, `ReconstructionResult`, `reconstruct_answer()` in new `engine/reconstruction.py`
- `MemoryStage`, `MaturationRecord`, `compute_stage_transition()`, `get_decay_multiplier()` in new `engine/memory_stages.py`
- `ExtractedPattern`, `ExtractionReport`, `extract_patterns()` in new `engine/pattern_extraction.py`
- `SQLiteMaturationMixin` in new `storage/sqlite_maturation.py` — maturation CRUD for SQLite backend
- Schema migration v6→v7: `memory_maturations` table with composite key (brain_id, fiber_id)
- `contributing_neurons` and `synthesis_method` fields on `RetrievalResult`
- `stages_advanced` and `patterns_extracted` fields on `ConsolidationReport`
- Maturation abstract methods on `NeuralStorage` base: `save_maturation()`, `get_maturation()`, `find_maturations()`
- 49 new unit tests: stabilization (12), reconstruction (11), memory stages (16), pattern extraction (8), plus 2 consolidation tests

### Changed

- Retrieval pipeline inserts stabilization phase after lateral inhibition and before answer reconstruction
- Answer reconstruction uses multi-strategy `reconstruct_answer()` instead of `reconstitute_answer()`
- Encoder initializes maturation record (STM stage) when creating new fibers
- Consolidation engine supports `MATURE` strategy for stage advancement and pattern extraction

## [0.10.0] - 2026-02-07

### Added

- **Formal Hebbian learning rule**: Principled weight update `Δw = η_eff * pre * post * (w_max - w)` replacing ad-hoc `weight += delta + dormancy_bonus`
- **Novelty-adaptive learning rate**: New synapses learn ~4x faster, frequently reinforced synapses stabilize toward base rate via exponential decay
- **Natural weight saturation**: `(w_max - w)` term prevents runaway weight growth — weights near ceiling barely change
- **Competitive normalization**: `normalize_outgoing_weights()` caps total outgoing weight per neuron at budget (default 5.0), implementing winner-take-most competition
- **Anti-Hebbian update**: `anti_hebbian_update()` for conflict resolution weight reduction (used in Phase 3)
- `learning_rate`, `weight_normalization_budget`, `novelty_boost_max`, `novelty_decay_rate` on `BrainConfig`
- `LearningConfig`, `WeightUpdate`, `hebbian_update`, `compute_effective_rate`, `normalize_outgoing_weights` in new `engine/learning_rule.py`
- 33 new unit tests covering learning rule, normalization, and backward compatibility

### Changed

- `Synapse.reinforce()` accepts optional `pre_activation`, `post_activation`, `now` parameters — uses formal Hebbian rule when activations provided, falls back to direct delta for backward compatibility
- `ReflexPipeline._defer_co_activated()` passes neuron activation levels to Hebbian strengthening
- `ReflexPipeline._defer_reinforce_or_create()` forwards activation levels to `reinforce()`
- Removed dormancy bonus from `Synapse.reinforce()` (novelty adaptation in learning rule replaces it)

## [0.9.6] - 2026-02-07

### Added

- **Sigmoid activation function**: Neurons now use sigmoid gating (`1/(1+e^(-6(x-0.5)))`) instead of raw clamping, producing bio-realistic nonlinear activation curves
- **Firing threshold**: Neurons only propagate signals when activation meets threshold (default 0.3), filtering borderline noise
- **Refractory period**: Cooldown prevents same neuron firing twice within a query pipeline (default 500ms), checked during spreading activation
- **Lateral inhibition**: Top-K winner-take-most competition in retrieval pipeline — top 10 neurons survive unchanged, rest suppressed by 0.7x factor
- **Homeostatic target field**: Reserved `homeostatic_target` field on NeuronState for v2 adaptive regulation
- `fired` and `in_refractory` properties on `NeuronState`
- `sigmoid_steepness`, `default_firing_threshold`, `default_refractory_ms`, `lateral_inhibition_k`, `lateral_inhibition_factor` on `BrainConfig`
- Schema migration v5→v6: four new columns on `neuron_states` table

### Changed

- `NeuronState.activate()` applies sigmoid function and accepts `now` and `sigmoid_steepness` parameters
- `NeuronState.decay()` preserves all new fields (firing_threshold, refractory_until, refractory_period_ms, homeostatic_target)
- `DecayManager.apply_decay()` uses `state.decay()` instead of manual NeuronState construction
- `ReinforcementManager.reinforce()` directly sets activation level (bypasses sigmoid for reinforcement)
- Spreading activation skips neurons in refractory cooldown
- Storage layer (SQLite + SharedStore) serializes/deserializes all new NeuronState fields

## [0.9.5] - 2026-02-07

### Added

- **Type-aware decay rates**: Different memory types now decay at biologically-inspired rates (facts: 0.02/day, todos: 0.15/day). `DEFAULT_DECAY_RATES` dict and `get_decay_rate()` helper in `memory_types.py`
- **Retrieval score breakdown**: `ScoreBreakdown` dataclass exposes confidence components (base_activation, intersection_boost, freshness_boost, frequency_boost) in `RetrievalResult` and MCP `nmem_recall` response
- **SimHash near-duplicate detection**: 64-bit locality-sensitive hashing via `utils/simhash.py`. New `content_hash` field on `Neuron` model. Encoder and auto-capture use SimHash to catch paraphrased duplicates
- **Point-in-time temporal queries**: `valid_at` parameter on `nmem_recall` filters fibers by temporal validity window (`time_start <= valid_at <= time_end`)
- Schema migration v4→v5: `content_hash INTEGER` column on neurons table

### Changed

- `DecayManager.apply_decay()` now uses per-neuron `state.decay_rate` instead of global rate
- `reconstitute_answer()` returns `ScoreBreakdown` as third tuple element
- `_remember()` MCP handler sets type-specific decay rates on neuron states after encoding

## [0.9.4] - 2026-02-07

### Performance

- **SQLite WAL mode** + `synchronous=NORMAL` + 8MB cache for concurrent reads and reduced I/O
- **Batch storage methods**: `get_synapses_for_neurons()`, `find_fibers_batch()`, `get_neuron_states_batch()` — single `IN()` queries replacing N sequential calls
- **Deferred write queue**: Fiber conductivity, Hebbian strengthening, and synapse writes batched after response assembly
- **Parallel anchor finding**: Entity + keyword lookups via `asyncio.gather()` instead of sequential loops
- **Batch fiber discovery**: Single junction-table query replaces 5-15 sequential `find_fibers()` calls
- **Batch subgraph extraction**: Single query replaces 20-50 sequential `get_synapses()` calls
- **BFS state prefetch**: Batch `get_neuron_states_batch()` per hop instead of individual lookups
- Target: 3-5x faster retrieval (800-4500ms → 200-800ms)

## [0.9.0] - 2026-02-06

### Added

- **Codebase indexing** (`nmem_index`): Index Python files into neural graph for code-aware recall
- **Python AST extractor**: Parse functions, classes, methods, imports, constants via stdlib `ast`
- **Codebase encoder**: Map code symbols to neurons (SPATIAL/ACTION/CONCEPT/ENTITY) and synapses (CONTAINS/IS_A/RELATED_TO/CO_OCCURS)
- **Branch-aware sessions**: `nmem_session` auto-detects git branch/commit/repo and stores in metadata + tags
- **Git context utility**: Detect branch, commit SHA, repo root via subprocess (zero deps)
- **CLI `nmem index` command**: Index codebase from command line with `--ext`, `--status`, `--json` options
- 16 new tests for extraction, encoding, and git context

## [0.8.0]

### Added

- Initial project structure
- Core data models: Neuron, Synapse, Fiber, Brain
- In-memory storage backend using NetworkX
- Temporal extraction for Vietnamese and English
- Query parser with stimulus decomposition
- Spreading activation algorithm
- Reflex retrieval pipeline
- Memory encoder
- FastAPI server with memory and brain endpoints
- Unit and integration tests
- Docker support

## [0.1.0] - TBD

### Added

- First public release
- Core memory encoding and retrieval
- Multi-language support (English, Vietnamese)
- REST API server
- Brain export/import functionality
