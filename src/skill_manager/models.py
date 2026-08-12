"""Small domain models shared by the CLI and harness adapters."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceManifest:
    """Repository-level settings for the source-of-truth tree."""

    source_dir: str = "skills"
    mcp_dir: str = "mcp"


@dataclass(frozen=True)
class McpServer:
    """A source MCP server using the portable stdio configuration shape."""

    name: str
    command: str
    args: tuple[str, ...] = ()
    env: tuple[tuple[str, str], ...] = ()
    cwd: str | None = None


@dataclass(frozen=True)
class McpConfig:
    """Source MCP servers and explicitly retired server names."""

    servers: tuple[McpServer, ...] = ()
    retired: tuple[str, ...] = ()


@dataclass(frozen=True)
class Skill:
    """A source skill and the files that belong to it."""

    name: str
    path: Path
    summary: str
    files: tuple[Path, ...]


@dataclass(frozen=True)
class AgentRule:
    """A language-scoped agent rule from the neutral source tree."""

    name: str
    path: Path
    patterns: tuple[str, ...]
    content: str


@dataclass(frozen=True)
class AgentSource:
    """Shared and harness-specific Markdown used to build one agent file."""

    root: Path
    shared: Path | None
    overrides: dict[str, Path]
    rules: tuple[AgentRule, ...] = ()


@dataclass(frozen=True)
class InstalledSkill:
    """A skill currently present in one harness's global directory."""

    harness: str
    name: str
    path: Path
    modified_at: float
