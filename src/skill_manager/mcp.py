"""Render source MCP servers into harness-specific configuration formats."""

import json
from pathlib import Path

from tomlkit import dumps, parse

from .adapters import HarnessAdapter
from .models import McpConfig, McpServer


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
