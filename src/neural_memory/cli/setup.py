"""Zero-config setup for NeuralMemory.

Handles first-time initialization: config, brain, and MCP auto-configuration.
Called by `nmem init` to set up everything in one command.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

import typer


def find_nmem_command() -> dict[str, Any]:
    """Find the best command to run the MCP server.

    Priority:
    1. nmem-mcp entry point (cleanest)
    2. nmem CLI with mcp subcommand
    3. python -m fallback
    """
    nmem_mcp = shutil.which("nmem-mcp")
    if nmem_mcp:
        return {"command": "nmem-mcp"}

    nmem = shutil.which("nmem")
    if nmem:
        return {"command": "nmem", "args": ["mcp"]}

    return {"command": sys.executable, "args": ["-m", "neural_memory.mcp"]}


def setup_config(data_dir: Path, *, force: bool = False) -> bool:
    """Create ~/.neuralmemory/ with config.toml and brains/ directory.

    Returns True if config was created/updated, False if skipped.
    """
    from neural_memory.unified_config import UnifiedConfig

    config_path = data_dir / "config.toml"

    if config_path.exists() and not force:
        return False

    config = UnifiedConfig(data_dir=data_dir)
    config.save()

    brains_dir = data_dir / "brains"
    brains_dir.mkdir(parents=True, exist_ok=True)

    return True


def setup_brain(data_dir: Path) -> str:
    """Ensure default brain SQLite DB exists.

    Returns the brain name.
    """
    brains_dir = data_dir / "brains"
    brains_dir.mkdir(parents=True, exist_ok=True)

    db_path = brains_dir / "default.db"
    if not db_path.exists():
        db_path.touch()

    return "default"


def setup_mcp_claude() -> str:
    """Auto-configure MCP in Claude Code (~/.claude/mcp_servers.json).

    Returns status string: "added", "exists", "failed", or "not_found".
    """
    claude_dir = Path.home() / ".claude"
    if not claude_dir.exists():
        return "not_found"

    config_path = claude_dir / "mcp_servers.json"
    mcp_entry = find_nmem_command()

    existing: dict[str, Any] = {}
    if config_path.exists():
        try:
            raw = config_path.read_text(encoding="utf-8").strip()
            if raw:
                existing = json.loads(raw)
        except (json.JSONDecodeError, OSError):
            existing = {}

    if "neural-memory" in existing:
        return "exists"

    try:
        existing["neural-memory"] = mcp_entry
        config_path.write_text(
            json.dumps(existing, indent=2) + "\n",
            encoding="utf-8",
        )
        return "added"
    except OSError:
        return "failed"


def setup_mcp_cursor() -> str:
    """Auto-configure MCP in Cursor (~/.cursor/mcp.json).

    Returns status string: "added", "exists", "failed", or "not_found".
    """
    cursor_dir = Path.home() / ".cursor"
    if not cursor_dir.exists():
        return "not_found"

    config_path = cursor_dir / "mcp.json"
    mcp_entry = find_nmem_command()

    existing: dict[str, Any] = {}
    if config_path.exists():
        try:
            raw = config_path.read_text(encoding="utf-8").strip()
            if raw:
                existing = json.loads(raw)
        except (json.JSONDecodeError, OSError):
            existing = {}

    servers = existing.get("mcpServers", {})
    if "neural-memory" in servers:
        return "exists"

    try:
        servers["neural-memory"] = mcp_entry
        existing["mcpServers"] = servers
        config_path.write_text(
            json.dumps(existing, indent=2) + "\n",
            encoding="utf-8",
        )
        return "added"
    except OSError:
        return "failed"


def print_summary(results: dict[str, str]) -> None:
    """Print formatted setup summary."""
    typer.echo()
    typer.secho("  NeuralMemory Setup", bold=True)
    typer.echo()

    status_icons = {
        "ok": typer.style("[OK]", fg=typer.colors.GREEN),
        "skip": typer.style("[--]", fg=typer.colors.YELLOW),
        "fail": typer.style("[!!]", fg=typer.colors.RED),
    }

    for label, detail in results.items():
        icon = status_icons.get(_classify_status(detail), status_icons["skip"])
        typer.echo(f"  {icon} {label:<16}{detail}")

    typer.echo()


def _classify_status(detail: str) -> str:
    """Classify a result detail string into ok/skip/fail."""
    lower = detail.lower()
    if any(word in lower for word in ("created", "added", "ready")):
        return "ok"
    if any(word in lower for word in ("exists", "already")):
        return "ok"
    if any(word in lower for word in ("not detected", "skipped", "not found")):
        return "skip"
    return "fail"
