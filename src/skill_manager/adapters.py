"""Filesystem adapters for the supported coding harnesses."""

from dataclasses import dataclass
from pathlib import Path

SUPPORTED_HARNESSES = ("claude", "codex", "copilot", "agy", "opencode")
MCP_HARNESSES = ("claude", "codex", "copilot", "agy")
ALIASES = {"copilot-cli": "copilot", "antigravity": "agy", "antigravity-cli": "agy"}


@dataclass(frozen=True)
class HarnessAdapter:
    """Map source artifact paths into one harness's global config tree."""

    name: str
    skills_dir: Path
    hooks_dir: Path
    prompts_dir: Path
    agent_file: Path
    mcp_config_file: Path | None = None

    def agent_destination(self) -> Path:
        """Return the global instruction file for this harness."""
        return self.agent_file

    def agent_rule_destination(self, name: str) -> Path | None:
        """Return a native destination for one scoped agent rule."""
        if self.name not in {"claude", "copilot"}:
            return None
        relative = Path(name)
        if not name or relative.is_absolute() or relative.name != name or ".." in relative.parts:
            raise ValueError(f"unsafe agent rule name: {name}")
        if self.name == "claude":
            return self.agent_file.parent / "rules" / f"{name}.md"
        return self.agent_file.parent / "instructions" / f"{name}.instructions.md"

    def root_for(self, kind: str) -> Path:
        """Return the destination root for a supported artifact kind."""
        try:
            return {"skill": self.skills_dir, "hook": self.hooks_dir, "prompt": self.prompts_dir}[kind]
        except KeyError as error:
            raise ValueError(f"unsupported artifact kind: {kind}") from error

    def destination(self, kind: str, name: str, relative_path: Path) -> Path:
        """Return a concrete destination without allowing path traversal."""
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"unsafe artifact path: {relative_path}")
        return self.root_for(kind) / name / relative

    def mcp_destination(self) -> Path | None:
        """Return the user-level MCP configuration file, when supported."""
        return self.mcp_config_file


def default_adapters(home: Path | None = None) -> dict[str, HarnessAdapter]:
    """Build adapters using the current user's standard global locations."""
    home = home or Path.home()
    roots = {
        "claude": home / ".claude",
        "codex": home / ".codex",
        "copilot": home / ".copilot",
        "agy": home / ".gemini" / "config",
        "opencode": home / ".config" / "opencode",
    }
    filenames = {name: "CLAUDE.md" if name == "claude" else "AGENTS.md" for name in roots}
    mcp_files = {
        "claude": home / ".claude.json",
        "codex": home / ".codex" / "config.toml",
        "copilot": home / ".copilot" / "mcp-config.json",
        "agy": home / ".gemini" / "config" / "mcp_config.json",
    }
    return {
        name: HarnessAdapter(
            name,
            root / "skills",
            root / "hooks",
            root / "prompts",
            root / filenames[name],
            mcp_files.get(name),
        )
        for name, root in roots.items()
    }


def select_adapters(names: tuple[str, ...], home: Path | None = None) -> list[HarnessAdapter]:
    """Resolve CLI names and preserve the requested order."""
    adapters = default_adapters(home)
    selected = names or SUPPORTED_HARNESSES
    resolved: list[HarnessAdapter] = []
    for requested in selected:
        name = ALIASES.get(requested, requested)
        if name not in adapters:
            choices = ", ".join(SUPPORTED_HARNESSES)
            raise ValueError(f"unknown harness '{requested}'; choose from {choices}")
        if adapters[name] not in resolved:
            resolved.append(adapters[name])
    return resolved
