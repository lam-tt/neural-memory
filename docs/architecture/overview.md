# Architecture Overview

NeuralMemory's layered architecture for memory management.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI / MCP Server / REST API               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Encoder    │  │  Retrieval   │  │   Lifecycle  │       │
│  │              │  │   Pipeline   │  │   Manager    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                    Extraction Layer                          │
│  ┌───────────┐  ┌────────────┐  ┌──────────────────┐        │
│  │QueryParser│  │QueryRouter │  │TemporalExtractor │        │
│  └───────────┘  └────────────┘  └──────────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                    Storage Interface                         │
│  ┌───────────┐  ┌───────────┐  ┌───────────────────┐        │
│  │InMemory   │  │SQLite     │  │SharedStorage(HTTP)│        │
│  └───────────┘  └───────────┘  └───────────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                    Core Layer                                │
│  ┌──────┐  ┌───────┐  ┌─────┐  ┌─────┐  ┌───────────┐      │
│  │Neuron│  │Synapse│  │Fiber│  │Brain│  │TypedMemory│      │
│  └──────┘  └───────┘  └─────┘  └─────┘  └───────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Layers

### Interface Layer

Entry points for users and applications:

- **CLI** - Command-line interface (`nmem` commands)
- **MCP Server** - Model Context Protocol for Claude integration
- **REST API** - FastAPI-based HTTP server

### Engine Layer

Core processing components:

- **MemoryEncoder** - Converts text to neural structures
- **ReflexPipeline** - Query processing with spreading activation
- **LifecycleManager** - Decay, reinforcement, compression

### Extraction Layer

NLP and parsing utilities:

- **QueryParser** - Decomposes queries into signals
- **QueryRouter** - Determines query intent and depth
- **TemporalExtractor** - Extracts time references

### Storage Layer

Pluggable storage backends:

- **InMemoryStorage** - NetworkX-based, for testing
- **SQLiteStorage** - Persistent, single-user
- **SharedStorage** - HTTP client for remote server

### Core Layer

Fundamental data structures:

- **Neuron** - Atomic information unit
- **Synapse** - Typed connection between neurons
- **Fiber** - Memory cluster
- **Brain** - Container with configuration
- **TypedMemory** - Metadata layer for memories

## Data Flow

### Encoding Flow

```
Input Text
    │
    ▼
┌─────────────────┐
│  QueryParser    │  Extract entities, time, concepts
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  MemoryEncoder  │  Create neurons and synapses
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Storage        │  Persist to graph
└─────────────────┘
```

### Retrieval Flow

```
Query
    │
    ▼
┌─────────────────┐
│  QueryParser    │  Decompose query
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  QueryRouter    │  Determine depth, intent
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Find Anchors   │  Locate entry neurons
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Spread         │  Activate connected neurons
│  Activation     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Intersection   │  Find convergence points
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Extract        │  Build response context
│  Subgraph       │
└─────────────────┘
```

## Storage Interface

All storage backends implement `NeuralStorage`:

```python
class NeuralStorage(ABC):
    # Neuron operations
    async def add_neuron(self, neuron: Neuron) -> str
    async def get_neuron(self, neuron_id: str) -> Neuron | None
    async def find_neurons(self, **filters) -> list[Neuron]

    # Synapse operations
    async def add_synapse(self, synapse: Synapse) -> str
    async def get_synapses(self, **filters) -> list[Synapse]

    # Graph traversal
    async def get_neighbors(self, neuron_id: str, ...) -> list[tuple]

    # Fiber operations
    async def add_fiber(self, fiber: Fiber) -> str
    async def get_fiber(self, fiber_id: str) -> Fiber | None

    # Brain operations
    async def export_brain(self, brain_id: str) -> BrainSnapshot
    async def import_brain(self, snapshot: BrainSnapshot, brain_id: str)
```

Benefits:

- Swap backends without changing application code
- Test with InMemory, deploy with SQLite/Neo4j
- Future-proof for scaling needs

## Configuration

### Brain Configuration

```python
@dataclass
class BrainConfig:
    decay_rate: float = 0.1
    reinforcement_delta: float = 0.05
    activation_threshold: float = 0.2
    max_spread_hops: int = 4
    max_context_tokens: int = 1500
```

### CLI Configuration

Stored in `~/.neural-memory/config.toml`:

```toml
[brain]
default = "default"
decay_rate = 0.1

[auto]
min_confidence = 0.7
detect_decisions = true
detect_errors = true

[shared]
enabled = false
url = ""
api_key = ""
```

## File Structure

```
~/.neural-memory/
├── config.toml           # User configuration
├── brains/
│   ├── default.db        # SQLite brain database
│   ├── work.db
│   └── personal.db
└── cache/
    └── ...
```

## Module Organization

```
src/neural_memory/
├── __init__.py           # Public API exports
├── py.typed              # PEP 561 marker
├── core/
│   ├── brain.py          # Brain, BrainConfig
│   ├── neuron.py         # Neuron, NeuronType, NeuronState
│   ├── synapse.py        # Synapse, SynapseType, Direction
│   ├── fiber.py          # Fiber
│   └── typed_memory.py   # TypedMemory, MemoryType
├── engine/
│   ├── encoder.py        # MemoryEncoder
│   ├── retrieval.py      # ReflexPipeline, DepthLevel
│   ├── activation.py     # SpreadingActivation
│   └── lifecycle.py      # DecayManager, ReinforcementManager
├── extraction/
│   ├── parser.py         # QueryParser, Stimulus
│   ├── router.py         # QueryRouter
│   └── temporal.py       # TemporalExtractor
├── storage/
│   ├── base.py           # NeuralStorage ABC
│   ├── memory_store.py   # InMemoryStorage
│   ├── sqlite_store.py   # SQLiteStorage
│   └── shared_store.py   # SharedStorage
├── server/
│   ├── app.py            # FastAPI application
│   ├── routes/           # API route handlers
│   └── models.py         # Pydantic models
├── mcp/
│   ├── server.py         # MCP server implementation
│   └── prompt.py         # System prompts
├── cli/
│   └── main.py           # Typer CLI
└── sharing/
    ├── export.py         # BrainExporter
    └── import_.py        # BrainImporter
```
