"""Render source MCP servers into harness-specific configuration formats."""

import json
from dataclasses import dataclass
from pathlib import Path

from tomlkit import dumps, parse

from .adapters import HarnessAdapter
from .manifest import load_mcp_config
from .models import McpConfig, McpServer


@dataclass(frozen=True)
class McpDeployment:
    """The result of updating one harness MCP configuration."""

    harness: str
    path: Path
    changed: bool


def _server_json(server: McpServer, harness: str) -> dict[str, object]:
    config: dict[str, object] = {"command": server.command, "args": list(server.args)}
    if server.env:
        config["env"] = dict(server.env)
    if server.cwd:
        config["cwd"] = server.cwd
    if harness == "claude":
        config["type"] = "stdio"
    elif harness == "copilot":
        config["type"] = "local"
    return config


def _render_json(existing: bytes, config: McpConfig, harness: str) -> bytes:
    data = json.loads(existing) if existing else {}
    servers = data.setdefault("mcpServers", {})
    for server in config.servers:
        servers[server.name] = _server_json(server, harness)
    for name in config.retired:
        servers.pop(name, None)
    return (json.dumps(data, indent=2) + "\n").encode()


def _render_codex(existing: bytes, config: McpConfig) -> bytes:
    document = parse(existing.decode() if existing else "")
    servers = document.setdefault("mcp_servers", {})
    for server in config.servers:
        entry = {"command": server.command, "args": list(server.args)}
        if server.env:
            entry["env"] = dict(server.env)
        if server.cwd:
            entry["cwd"] = server.cwd
        servers[server.name] = entry
    for name in config.retired:
        servers.pop(name, None)
    return dumps(document).encode()


def render_mcp_config(adapter: HarnessAdapter, config: McpConfig, path: Path) -> bytes:
    """Render one source MCP config using the target harness schema."""
    existing = path.read_bytes() if path.exists() else b""
    if adapter.name == "codex":
        return _render_codex(existing, config)
    if adapter.name in {"claude", "copilot", "agy"}:
        return _render_json(existing, config, adapter.name)
    raise ValueError(f"MCP deployment is not supported for {adapter.name}")


def deploy_mcp(root: Path, adapters: list[HarnessAdapter], dry_run: bool = False) -> list[McpDeployment]:
    """Merge source MCP servers into selected user-level harness configs."""
    config = load_mcp_config(root)
    results: list[McpDeployment] = []
    for adapter in adapters:
        path = adapter.mcp_destination()
        if path is None:
            raise ValueError(f"MCP deployment is not supported for {adapter.name}")
        rendered = render_mcp_config(adapter, config, path)
        changed = not path.exists() or path.read_bytes() != rendered
        if changed and not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(rendered)
        results.append(McpDeployment(adapter.name, path, changed))
    return results
