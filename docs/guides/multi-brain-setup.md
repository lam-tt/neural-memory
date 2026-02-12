# Multi-Brain Setup

NeuralMemory stores each brain as a separate SQLite database. This gives you complete data isolation between agents, projects, or workspaces.

```
~/.neuralmemory/brains/
  default.db          ← shared brain (default)
  coder-agent.db      ← Agent 1
  researcher-agent.db ← Agent 2
  project-api.db      ← Project-specific
```

## Quick Setup

### Method 1: OpenClaw Plugin Config

Each OpenClaw profile can use a different brain via the `brain` field:

```json
{
  "neuralmemory": {
    "brain": "coder-agent"
  }
}
```

The brain is created automatically on first use.

### Method 2: MCP Server (Claude Code, Cursor, etc.)

Set the `NEURALMEMORY_BRAIN` environment variable in your MCP config:

```json
{
  "mcpServers": {
    "neural-memory": {
      "command": "python",
      "args": ["-m", "neural_memory.mcp"],
      "env": {
        "NEURALMEMORY_BRAIN": "my-project"
      }
    }
  }
}
```

### Method 3: CLI

```bash
# Create a new brain
nmem brain create research-brain

# Switch to it
nmem brain use research-brain

# List all brains
nmem brain list
```

## OpenClaw Multi-Profile Example

If you run multiple OpenClaw agents — each as a separate entity with its own files, memory, and keys — configure a different brain per profile.

**Profile: Coder**
```json
{
  "neuralmemory": {
    "brain": "coder",
    "autoContext": true,
    "autoCapture": true
  }
}
```

**Profile: Researcher**
```json
{
  "neuralmemory": {
    "brain": "researcher",
    "autoContext": true,
    "autoCapture": true,
    "contextDepth": 2
  }
}
```

**Profile: Security Reviewer**
```json
{
  "neuralmemory": {
    "brain": "security",
    "autoContext": true,
    "autoCapture": false
  }
}
```

Each agent gets a completely separate database file. No data leaks between brains.

## Per-Workspace MCP Config

For project-level isolation in Claude Code, create a `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "neural-memory": {
      "command": "python",
      "args": ["-m", "neural_memory.mcp"],
      "env": {
        "NEURALMEMORY_BRAIN": "work-api"
      }
    }
  }
}
```

This overrides the global config — memories stay scoped to that workspace.

## Sharing Knowledge Between Brains

Use the `nmem_transplant` tool to copy memories from one brain to another:

```
nmem_transplant(
  source_brain="researcher",
  tags=["architecture", "api-design"]
)
```

This copies matching fibers (with their neurons and synapses) into the current brain. Use it to share insights without merging entire brain histories.

Options:
- **tags** — only transplant fibers matching these tags
- **memory_types** — filter by type (`fact`, `decision`, `insight`, etc.)
- **strategy** — conflict resolution: `prefer_local`, `prefer_remote`, `prefer_recent`, `prefer_stronger`

## Best Practices

### When to Use Separate Brains

| Scenario | Recommendation |
|----------|---------------|
| Different agents with different roles | Separate brains |
| Different projects on the same machine | Separate brains |
| Same agent, different topics | Use tags instead |
| Security-sensitive isolation | Separate brains |
| Temporary experiments | Separate brain, delete when done |

### Naming Conventions

- **By agent role**: `coder`, `researcher`, `planner`, `security`
- **By project**: `work-api`, `side-project`, `open-source`
- **By environment**: `dev`, `staging`, `prod`

Valid characters: `a-z`, `A-Z`, `0-9`, `-`, `_`, `.` (max 64 chars).

### Maintenance

Each brain is independent. Run health checks per brain:

```bash
# Switch to a brain and check health
nmem brain use coder
nmem health
nmem stats
```

Or use the `nmem_health` / `nmem_stats` MCP tools — they always operate on the currently configured brain.
