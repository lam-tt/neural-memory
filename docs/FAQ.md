# NeuralMemory FAQ

## Installation

### Q: `pip install neural-memory` installs what?

- **Core**: pydantic, networkx, python-dateutil, typer, aiohttp, aiosqlite, rich
- **CLI tools**: `nmem`, `neural-memory`, `nmem-mcp`
- **Optional extras**:
  - `[server]` — FastAPI + Uvicorn
  - `[neo4j]` — Neo4j graph database
  - `[nlp-en]` — English NLP (spaCy)
  - `[nlp-vi]` — Vietnamese NLP (underthesea, pyvi)
  - `[all]` — All of the above
  - `[dev]` — Development tools (pytest, ruff, mypy, etc.)

### Q: `pip` not working on Windows?

Use `python -m pip` instead:

```powershell
python -m pip install neural-memory[all]
```

### Q: How to install from source?

```bash
git clone https://github.com/nhadaututtheky/neural-memory.git
cd neural-memory
pip install -e ".[all,dev]"
```

The `-e` flag enables editable mode — code changes take effect immediately without reinstalling.

### Q: Too many commands — is there a simpler UI/UX approach?

Yes. If you use VS Code, the **NeuralMemory extension** provides a full GUI — no terminal commands needed:

- **Encode memory**: Select text → `Ctrl+Shift+M E`
- **Query memory**: `Ctrl+Shift+M Q` → type your question
- **Start/stop server**: `Ctrl+Shift+P` → NeuralMemory: Start Server
- **Switch brain**: `Ctrl+Shift+P` → NeuralMemory: Switch Brain
- **View graph**: `Ctrl+Shift+P` → NeuralMemory: Open Graph View

The sidebar panel also shows neurons, fibers, and brain stats at a glance.

### Q: How to update to the latest version?

```bash
pip install --upgrade neural-memory[all]
```

If installed from source:

```bash
git pull
pip install -e ".[all,dev]"
```

## VS Code Extension

### Q: How to use NeuralMemory without writing Python code?

Install the VS Code extension:

1. Open VS Code
2. Go to Extensions (`Ctrl+Shift+X`)
3. Search **NeuralMemory**
4. Click **Install**

> **Note**: The extension still requires Python + `neural-memory` package installed on the machine as its backend.

### Q: Extension not showing data?

1. Start the server: `Ctrl+Shift+P` → **NeuralMemory: Start Server**
2. Switch brain if needed: `Ctrl+Shift+P` → **NeuralMemory: Switch Brain** → select your brain
3. Click refresh

### Q: Server running on a different port than the extension expects?

The extension defaults to port `8000`. If your server runs on a different port, update the setting:

1. Open VS Code Settings (`Ctrl+,`)
2. Search `neuralmemory.serverUrl`
3. Set it to your server's URL (e.g. `http://127.0.0.1:8080`)

### Q: Server is running, correct port set, but extension still shows nothing?

A new brain starts empty — there is no data to display yet. You need to encode at least one memory first:

1. Select any text in your editor
2. Press `Ctrl+Shift+M E` to encode it
3. Click refresh in the NeuralMemory sidebar

After encoding, neurons and fibers will appear in the sidebar.

### Q: I opened the server URL in the browser but only see JSON info, not my data?

The root URL (`/`) only shows basic API info. To view your data:

- **Graph visualization (UI)**: go to `/ui` (e.g. `http://127.0.0.1:8000/ui`)
- **API documentation (Swagger)**: go to `/docs` (e.g. `http://127.0.0.1:8000/docs`)
- **Neurons list (API)**: go to `/memory/neurons` (requires `X-Brain-ID` header)

The VS Code sidebar is the main way to browse your neurons and fibers.
