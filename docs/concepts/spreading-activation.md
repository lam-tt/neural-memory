# Spreading Activation

The core retrieval mechanism in NeuralMemory.

## What is Spreading Activation?

Spreading activation is a cognitive model of how memory retrieval works in the human brain. When you think of a concept, related concepts become more "active" and accessible.

**Example:** Thinking of "apple" activates:
- Fruit (category)
- Red/green (colors)
- Tree (where it grows)
- Pie (food made with it)
- iPhone (brand association)

NeuralMemory implements this computationally:

```
Query: "apple"
    │
    ▼ activate
[apple] ─────► [fruit] ─────► [banana]
    │              │
    │              ▼
    └─────► [red] ─────► [strawberry]
```

## How It Works

### 1. Anchor Selection

The query is parsed to identify anchor neurons:

```bash
nmem recall "What did Alice suggest about auth?"
```

Anchors identified:
- `Alice` (entity)
- `suggest` (action hint)
- `auth` (concept)

### 2. Initial Activation

Anchor neurons receive initial activation (1.0):

```
[Alice] = 1.0
[auth] = 1.0
```

### 3. Activation Spread

Activation spreads through synapses with decay:

```python
activation(neighbor) = source_activation * synapse_weight * decay_factor
```

Example with decay_factor = 0.8:

```
Hop 0: [Alice] = 1.0
Hop 1: [Meeting with Alice] = 1.0 * 0.9 * 0.8 = 0.72
Hop 2: [JWT suggestion] = 0.72 * 0.8 * 0.8 = 0.46
Hop 3: [Auth module] = 0.46 * 0.7 * 0.8 = 0.26
```

### 4. Intersection Finding

Neurons activated by multiple anchors score higher:

```
           Alice anchor          auth anchor
                │                     │
                ▼                     ▼
         [Meeting] ────────► [JWT] ◄──── [auth]
              │                 │
              │    activation   │
              │    from both    │
              └────► [0.72] ◄───┘
                   INTERSECTION
```

Intersection score = sum of activations from different sources

### 5. Subgraph Extraction

The highest-scoring connected region is extracted as the result.

## Configuration

### Brain Config

```python
@dataclass
class BrainConfig:
    decay_rate: float = 0.1           # How fast activation decays
    reinforcement_delta: float = 0.05  # How much to strengthen on use
    activation_threshold: float = 0.2  # Minimum to consider active
    max_spread_hops: int = 4          # Maximum traversal depth
    max_context_tokens: int = 1500    # Max tokens in response
```

### Decay Rate

Controls how quickly activation fades with distance:

```
activation = initial * decay_factor^hops
decay_factor = 1 - decay_rate
```

| decay_rate | Effect |
|------------|--------|
| 0.05 | Slow decay, wide spread |
| 0.1 | Default, balanced |
| 0.2 | Fast decay, focused |
| 0.3 | Very focused, nearby only |

### Activation Threshold

Neurons below this level are ignored:

```python
if activation_level < activation_threshold:
    skip_neuron()
```

Lower threshold = more results, potentially noisy
Higher threshold = fewer results, more precise

### Max Spread Hops

Limits how far activation travels:

| Hops | Reach | Use Case |
|------|-------|----------|
| 1 | Direct connections | Simple lookups |
| 2-3 | Local context | Most queries |
| 4+ | Extended graph | Deep analysis |

## Depth Levels

The CLI uses depth levels to control spreading:

```bash
nmem recall "query" --depth 0  # Instant: 1 hop
nmem recall "query" --depth 1  # Context: 2-3 hops
nmem recall "query" --depth 2  # Habit: 4+ hops
nmem recall "query" --depth 3  # Deep: full traversal
```

### Auto-Detection

Without `--depth`, the system auto-detects:

| Query Pattern | Detected Depth |
|---------------|----------------|
| "What is X?" | Instant (0) |
| "What happened before X?" | Context (1) |
| "Do I usually X?" | Habit (2) |
| "Why did X happen?" | Deep (3) |

## Synapse Weight Effects

Higher-weight synapses transfer more activation:

```
High weight (0.9):  [A] ──0.9──► [B]  →  B gets 0.72 activation
Low weight (0.3):   [A] ──0.3──► [B]  →  B gets 0.24 activation
```

This naturally prioritizes:
- Strong causal links over weak associations
- Recent/reinforced paths over old/unused ones

## Multi-Anchor Convergence

The power of spreading activation shows with multiple query terms:

```
Query: "Alice auth Tuesday"

[Alice] ──────┐
              │
              ▼
         [JWT meeting] ← HIGH SCORE (all 3 converge)
              ▲
              │
[auth] ───────┘
              ▲
              │
[Tuesday] ────┘
```

Neurons where multiple anchors converge score exponentially higher.

## Performance Characteristics

| Graph Size | Typical Query Time |
|------------|-------------------|
| 1K neurons | 5-10ms |
| 10K neurons | 20-50ms |
| 100K neurons | 100-200ms |

Optimization techniques:
- Early termination below threshold
- Priority queue for activation order
- Caching of frequent paths

## Compared to Other Approaches

### vs. Vector Similarity

| Aspect | Vector Search | Spreading Activation |
|--------|--------------|---------------------|
| Model | Geometric distance | Graph traversal |
| Relationships | Implicit | Explicit typed edges |
| Multi-hop | Multiple queries | Single traversal |
| Explanation | "Similar embedding" | "Connected via X" |

### vs. Keyword Search

| Aspect | Keyword Search | Spreading Activation |
|--------|---------------|---------------------|
| Model | Text matching | Semantic graph |
| Synonyms | Manual expansion | Automatic via links |
| Context | None | Full graph context |
| Ranking | TF-IDF / BM25 | Activation convergence |

## Debugging Activation

Use `--show-routing` to see activation paths:

```bash
nmem recall "auth decision" --show-routing
```

Output:
```
Query parsed: entities=[auth], intents=[decision]
Anchors: [neuron-auth-123, neuron-decision-456]
Spread:
  neuron-auth-123 → neuron-jwt-789 (weight: 0.8, activation: 0.64)
  neuron-jwt-789 → neuron-meeting-012 (weight: 0.7, activation: 0.45)
  ...
Intersection: neuron-jwt-789 (score: 0.89)
Result: "We decided to use JWT for authentication"
```
