"""Load the small repository manifest used by skill-manager."""

import tomllib
from pathlib import Path

import yaml

from .models import AgentSource, McpConfig, McpServer, Skill, SourceManifest

MANIFEST_NAME = "skill-manager.toml"
VARIABLES_NAME = "skill-manager.json"
AGENTS_DIR = "agents"
AGENT_SHARED_NAME = "shared.md"
MCP_CONFIG_NAME = "servers.yaml"


def load_manifest(root: Path) -> SourceManifest:
    """Load repository settings, falling back to the conventional layout."""
    path = root / MANIFEST_NAME
    if not path.exists():
        return SourceManifest()
    with path.open("rb") as stream:
        data = tomllib.load(stream)
    project = data.get("project", {})
    return SourceManifest(
        source_dir=str(project.get("source_dir", "skills")),
        mcp_dir=str(project.get("mcp_dir", "mcp")),
    )


def load_mcp_config(root: Path, manifest: SourceManifest | None = None) -> McpConfig:
    """Load source MCP servers and explicit retirement entries."""
    config = manifest or load_manifest(root)
    path = root / config.mcp_dir / MCP_CONFIG_NAME
    if not path.exists():
        return McpConfig()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw_servers = data.get("servers", {})
    if not isinstance(raw_servers, dict):
        raise ValueError(f"MCP servers must be a mapping: {path}")
    servers: list[McpServer] = []
    for name, raw_server in raw_servers.items():
        if not isinstance(name, str) or not isinstance(raw_server, dict):
            raise ValueError(f"invalid MCP server entry: {name!r}")
        command = raw_server.get("command")
        if not isinstance(command, str) or not command:
            raise ValueError(f"MCP server '{name}' requires a command")
        args = raw_server.get("args", [])
        env = raw_server.get("env", {})
        if not isinstance(args, list) or not all(isinstance(value, str) for value in args):
            raise ValueError(f"MCP server '{name}' args must be a list of strings")
        if not isinstance(env, dict) or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in env.items()
        ):
            raise ValueError(f"MCP server '{name}' env must be a mapping of strings")
        cwd = raw_server.get("cwd")
        if cwd is not None and not isinstance(cwd, str):
            raise ValueError(f"MCP server '{name}' cwd must be a string")
        servers.append(McpServer(name, command, tuple(args), tuple(env.items()), cwd))
    retired = data.get("retired", [])
    if not isinstance(retired, list) or not all(isinstance(name, str) for name in retired):
        raise ValueError(f"MCP retired must be a list of strings: {path}")
    return McpConfig(tuple(servers), tuple(retired))


def _summary(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        frontmatter, _, text = text[3:].partition("---")
        for line in frontmatter.splitlines():
            if line.strip().startswith("description:"):
                return line.split(":", 1)[1].strip().strip("\"'")
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line
    return "No summary provided"


def load_skills(root: Path, manifest: SourceManifest | None = None) -> list[Skill]:
    """Find source skill folders and their deployable files."""
    config = manifest or load_manifest(root)
    skills_root = root / config.source_dir
    if not skills_root.exists():
        return []
    skills: list[Skill] = []
    for path in sorted(item for item in skills_root.iterdir() if item.is_dir() and not item.name.startswith(".")):
        files = tuple(sorted(file for file in path.rglob("*") if file.is_file() and file.name != VARIABLES_NAME))
        markdown = next((file for file in files if file.name.lower() in {"skill.md", "readme.md"}), None)
        skills.append(Skill(path.name, path, _summary(markdown) if markdown else "No summary provided", files))
    return skills


def load_agent_source(root: Path) -> AgentSource | None:
    """Find shared and harness-specific agent Markdown in the source repo."""
    source_root = root / AGENTS_DIR
    if not source_root.exists():
        return None
    files = sorted(file for file in source_root.iterdir() if file.is_file() and file.suffix.lower() == ".md")
    shared = next((file for file in files if file.name.lower() == AGENT_SHARED_NAME), None)
    overrides = {file.stem.lower(): file for file in files if file != shared}
    return AgentSource(source_root, shared, overrides)
