# NeuralMemory - Project Rules for Claude

## Project Overview

NeuralMemory is a biologically-inspired memory system for AI agents. It has three interfaces:
- **CLI** (`nmem`) — Human-facing, built with Typer
- **MCP Server** — AI agent-facing, Model Context Protocol
- **VS Code Extension** — Visual brain explorer + inline recall

## Architecture

```
src/neural_memory/
├── cli/                  # CLI interface (Typer)
│   ├── main.py           # Entry point, app registration only
│   ├── commands/          # One file per command group
│   ├── config.py          # CLIConfig dataclass
│   ├── storage.py         # PersistentStorage adapter
│   ├── tui.py             # Rich TUI renderers
│   └── _helpers.py        # Shared CLI utilities
├── core/                  # Domain models (Brain, Neuron, Synapse, Fiber)
├── engine/                # Encoding, retrieval, activation, decay
├── extraction/            # NLP parsing, entity extraction, routing
├── storage/               # Persistence (SQLite, JSON, shared)
├── mcp/                   # MCP server
├── server/                # FastAPI REST server
├── sync/                  # Shared brain sync client
├── safety/                # Freshness checks, sensitive content
└── utils/                 # Shared utilities

vscode-extension/
├── src/
│   ├── extension.ts       # Entry point
│   ├── commands/           # Command handlers
│   ├── editors/            # CodeLens, decorations
│   ├── server/             # HTTP client, WebSocket, lifecycle
│   └── views/              # TreeView, GraphPanel webview
└── test/                   # Unit, integration, perf tests
```

---

## 1. Risk Classification

Every code change MUST be classified before execution.

### Type A — Safe (Apply Immediately)

- New files or functions with no dependencies
- Comments, documentation, docstrings
- Test files
- Configuration files in isolated scopes

### Type B — Caution (Show Diff + Verify)

- Logic changes to existing functions
- Refactoring of working code
- Parameter additions with defaults
- Bug fixes in non-core modules

**Protocol:**
1. Show diff clearly
2. Verify no regression in related functions
3. Identify all callers of modified functions

### Type C — Critical (Full Impact Analysis + User Approval)

- Core logic (storage layer, engine, encoder, retrieval)
- Database schema changes (SQLite migrations)
- API signature changes (MCP tools, REST endpoints)
- Global configuration changes
- Breaking public API changes

**Protocol:**
1. Document potential side effects BEFORE coding
2. Provide fallback/rollback plan
3. Present alternatives (safer vs current approach)
4. Get explicit user approval

### Protocol Rules

| Rule | Description |
|------|-------------|
| **Burden of Proof** | Modifying working code requires evidence (error, performance, security) — "looks better" is NOT valid |
| **One Change Per Edit** | Never mix refactoring with bug fixes — isolate changes for clean debugging |
| **Syntax Verification** | Run `python -m py_compile <file>` after EVERY Python edit |
| **Complete Bodies** | NEVER use placeholder comments like `# ... (skipping)` — always write FULL function bodies |

---

## 2. File Size Rules (ENFORCED)

### Hard Limits
- **Python files: 500 lines max**
- **TypeScript files: 500 lines max**
- **Functions: 50 lines max**
- **No exceptions.** If a file approaches 400 lines and you need to add >50 lines, split first.

### Before Adding Code
1. Check target file line count: `wc -l <file>`
2. If file > 400 lines AND your change adds > 50 lines → **refactor first, add second**
3. If file > 500 lines → **refuse to add code until it is split**

### How to Split
- Extract by concern (one responsibility per file)
- Keep public API stable (re-export from `__init__.py` if needed)
- Move tests accordingly
- Verify all imports resolve after split

---

## 3. Module Boundaries

### CLI Commands (`cli/commands/`)
Each file registers commands on the main `app` or a sub-`Typer`:

| File | Commands | Max lines |
|------|----------|-----------|
| `memory.py` | remember, todo, recall, context | ~480 |
| `listing.py` | list, cleanup | ~400 |
| `brain.py` | brain list/use/create/export/import/delete/health | ~430 |
| `project.py` | project create/list/show/delete/extend | ~420 |
| `shared.py` | shared enable/disable/status/test/sync | ~250 |
| `info.py` | stats, check, status, version | ~300 |
| `tools.py` | mcp, dashboard, ui, graph, init, serve, decay, hooks | ~400 |
| `shortcuts.py` | q, a, last, today, mcp-config, prompt, export, import | ~350 |

### Storage Layer
- `base.py` — Abstract interface
- `sqlite_store.py` — SQLite implementation (currently 1659 lines, needs splitting)
- `memory_store.py` — JSON-based storage
- `shared_store.py` — Remote shared storage

### Engine Layer
- `encoder.py` — Memory encoding pipeline
- `retrieval.py` — Reflex-based retrieval
- `activation.py` — Neuron activation spreading
- `lifecycle.py` — Decay and lifecycle management

---

## 4. Adding New CLI Commands

1. Identify which command group the new command belongs to
2. Check the target file's line count
3. Add the command function with full type hints
4. Follow the async inner function pattern:
   ```python
   @app.command()
   def my_command(
       arg: Annotated[str, typer.Argument(help="...")],
       json_output: Annotated[bool, typer.Option("--json", "-j")] = False,
   ) -> None:
       """Docstring with examples."""
       async def _my_command() -> dict:
           config = get_config()
           storage = await get_storage(config)
           # ... logic ...
           return {"message": "Done"}

       result = asyncio.run(_my_command())
       output_result(result, json_output)
   ```
5. Register in `main.py` if it's a new module

---

## 5. Coding Standards (Python)

### Required
- Type hints on ALL function signatures
- Immutable patterns — never mutate dicts/lists in-place, return new objects
- Specific exception handling with context messages
- `snake_case` functions/variables, `PascalCase` classes, `SCREAMING_SNAKE` constants
- Parameterized SQL queries only (never f-strings in SQL)
- No hardcoded secrets — use environment variables
- Functions under 50 lines
- One class per file for major classes
- Organize by feature/domain, not by type

### Forbidden
- Files over 500 lines
- Functions over 50 lines
- Bare `except:` clauses
- `print()` statements (use `typer.echo` in CLI, `logger` elsewhere)
- Mutable default arguments (`def f(items=[])` → use `def f(items: list | None = None)`)
- Global mutable state
- `# type: ignore` without explanation
- Blocking calls in async functions (`requests.get` → use `httpx` or `aiohttp`)
- Placeholder comments (`# ... rest of code ...`, `# skipping`)

### Security
- Parameterized SQL queries — NEVER `f"SELECT ... {user_input}"`
- No hardcoded secrets — use `os.getenv()` with validation
- Validate external input at system boundaries
- Path traversal prevention — resolve paths and check `is_relative_to(base_dir)`
- No sensitive data in logs — mask or omit API keys, passwords, tokens

### Patterns
- Async inner function pattern for CLI commands (see above)
- Config/storage access via `get_config()` / `get_storage(config)`
- JSON or human-readable output via `output_result(data, as_json)`
- Error returns as `{"error": "message"}` dicts
- Frozen dataclasses for immutable data models (`@dataclass(frozen=True)`)

---

## 6. Coding Standards (TypeScript)

### Required
- Strict TypeScript (`strict: true` in tsconfig)
- Immutable patterns — spread operators, no mutation
- Error handling with try/catch on all async operations
- VS Code API disposal pattern (`context.subscriptions.push(...)`)
- Functions under 50 lines

### Forbidden
- Files over 500 lines
- Functions over 50 lines
- `console.log` (use `OutputChannel` for VS Code extension logging)
- `any` type without justification
- Direct DOM manipulation in webviews (use message passing)

---

## 7. Validation & Verification

### After EVERY Python Edit

```bash
# 1. Syntax check
python -m py_compile <filename>

# 2. Import check
python -c "from neural_memory.<module> import <name>; print('OK')"
```

### After Type B/C Changes

```bash
# 3. Full test suite
pytest tests/

# 4. Lint + type check
ruff check src/
mypy src/ --ignore-missing-imports
```

### After TypeScript Edits

```bash
cd vscode-extension
npx tsc --noEmit                   # Type check
npm run test:unit                  # Unit tests
```

---

## 8. Code Quality Checklist

Run before completing ANY task:

### Correctness
- [ ] Risk classified (Type A/B/C) and protocol followed
- [ ] `python -m py_compile <file>` passed (Python) or `tsc --noEmit` passed (TypeScript)
- [ ] No placeholder comments left in code
- [ ] Import verification passed
- [ ] All callers of modified functions identified

### Style
- [ ] Type hints on ALL functions
- [ ] Immutable patterns used (no mutation)
- [ ] Specific exceptions (no bare `except`)
- [ ] No blocking calls in async functions
- [ ] Functions < 50 lines
- [ ] Files < 500 lines

### Security
- [ ] No hardcoded secrets
- [ ] Parameterized SQL queries (no f-strings in SQL)
- [ ] External input validated at system boundaries
- [ ] No sensitive data in logs
- [ ] No path traversal vulnerabilities

---

## 9. Testing

- Unit tests: `test/unit/` — pure logic, no VS Code dependency
- Integration tests: `test/suite/` — requires VS Code test runner
- Perf benchmarks: `test/webview/` — Playwright
- CLI tests: `tests/cli/` — pytest
- Run unit tests: `npm run test:unit` (extension), `pytest` (Python)

---

## 10. Build & Verify

### Python
```bash
ruff check src/                    # Lint
mypy src/ --ignore-missing-imports # Type check
pytest tests/                      # Tests
```

### VS Code Extension
```bash
cd vscode-extension
npm run build                      # esbuild bundle
npx tsc --noEmit                   # Type check
npm run test:unit                  # Unit tests
```

---

## 11. Git Conventions

- Commit format: `<type>: <description>` (feat, fix, refactor, docs, test, chore, perf, ci)
- No `Co-Authored-By` attribution (disabled in settings)
- Commit only when explicitly asked
- Never force push to main
- One change per commit — never mix refactoring with bug fixes
