# How NeuralMemory Works

NeuralMemory uses a fundamentally different approach to memory retrieval than traditional search or RAG systems.

## The Core Idea

**Human memory doesn't work like search.**

You don't query your brain with:
```sql
SELECT * FROM memories WHERE content LIKE '%Alice%' ORDER BY similarity DESC
```

Instead, thinking of "Alice" *activates* related memories - her face, your last conversation, the project you worked on together. These emerge through **association**, not **search**.

NeuralMemory replicates this process:

```
Query: "What did Alice suggest?"
         │
         ▼
┌─────────────────────┐
│ 1. Decompose Query  │  → time hints, entities, intent
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ 2. Find Anchors     │  → "Alice" neuron
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ 3. Spread Activation│  → activate connected neurons
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ 4. Find Intersection│  → high-activation subgraph
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ 5. Extract Context  │  → "Alice suggested rate limiting"
└─────────────────────┘
```

## Key Components

### Neurons

Neurons are atomic units of information:

- **Entity neurons** - People, places, things ("Alice", "coffee shop")
- **Time neurons** - Temporal references ("Tuesday 3pm", "last week")
- **Concept neurons** - Ideas, topics ("authentication", "rate limiting")
- **Action neurons** - What happened ("discussed", "decided", "fixed")
- **State neurons** - Conditions ("blocked", "completed", "urgent")

### Synapses

Synapses are typed connections between neurons:

- **Temporal** - `HAPPENED_AT`, `BEFORE`, `AFTER`
- **Causal** - `CAUSED_BY`, `LEADS_TO`, `ENABLES`
- **Associative** - `RELATED_TO`, `CO_OCCURS`
- **Semantic** - `IS_A`, `HAS_PROPERTY`, `INVOLVES`

### Fibers

Fibers are clusters of related neurons - a coherent "memory":

```
Fiber: "Meeting with Alice"
├── [Alice] ←DISCUSSED→ [API design]
├── [Coffee shop] ←AT_LOCATION→ [Meeting]
├── [Tuesday 3pm] ←HAPPENED_AT→ [Meeting]
└── [Rate limiting] ←SUGGESTED_BY→ [Alice]
```

## Encoding Process

When you store a memory:

```bash
nmem remember "Met Alice at coffee shop to discuss API design, she suggested rate limiting"
```

NeuralMemory:

1. **Extracts entities** - Alice, coffee shop, API design, rate limiting
2. **Extracts temporal context** - (uses current time if not specified)
3. **Identifies relationships** - Alice DISCUSSED API design, Alice SUGGESTED rate limiting
4. **Creates neurons** - One for each entity/concept
5. **Creates synapses** - Typed connections between neurons
6. **Bundles into fiber** - Groups everything into a coherent memory

## Retrieval Process

When you query:

```bash
nmem recall "What did Alice suggest?"
```

NeuralMemory:

1. **Parses query** - Identifies "Alice" as entity, "suggest" as action hint
2. **Finds anchor neurons** - Locates "Alice" neuron in graph
3. **Spreads activation** - Activates connected neurons with decay
4. **Finds intersections** - Multiple query terms converge on same neurons
5. **Extracts subgraph** - Gets most activated cluster
6. **Reconstructs answer** - "Alice suggested rate limiting"

## Activation Dynamics

Activation spreads through the graph with decay:

```
activation(hop) = initial * decay_factor^hop
```

Neurons with high activation from multiple sources rank higher:

```
Alice ──→ [API design] ←── suggest
   \          ↑         /
    \         |        /
     └───> [RESULT] <─┘
```

## Depth Levels

Different queries need different exploration depths:

| Level | Name | Hops | Use Case |
|-------|------|------|----------|
| 0 | Instant | 1 | Who, what, where |
| 1 | Context | 2-3 | Before/after context |
| 2 | Habit | 4+ | Cross-time patterns |
| 3 | Deep | Full | Causal chains, emotions |

## Memory Lifecycle

Memories evolve over time:

### Decay

Unused memories weaken following the Ebbinghaus forgetting curve:

```
activation = initial * e^(-decay_rate * days)
```

### Reinforcement

Frequently accessed memories strengthen (Hebbian learning):

```
When recalled: synapse.weight += reinforcement_delta
```

### Compression

Old memories can be summarized:

```
Original: [20 detailed neurons about Tuesday meeting]
Compressed: [1 summary neuron: "API design meeting with Alice"]
```

## Comparison with RAG

| Aspect | RAG | NeuralMemory |
|--------|-----|--------------|
| Data model | Flat chunks | Neural graph |
| Retrieval | Similarity search | Spreading activation |
| Relationships | Implicit | Explicit typed synapses |
| Temporal | Metadata filter | First-class neurons |
| Multi-hop | Multiple queries | Single traversal |
| Memory lifecycle | Static | Dynamic decay/reinforce |
