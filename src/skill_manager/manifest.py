"""Load the small repository manifest used by skill-manager."""

import tomllib
from pathlib import Path

from .models import AgentSource, Skill, SourceManifest

MANIFEST_NAME = "skill-manager.toml"
VARIABLES_NAME = "skill-manager.json"
AGENTS_DIR = "agents"
AGENT_SHARED_NAME = "shared.md"


def load_manifest(root: Path) -> SourceManifest:
    """Load repository settings, falling back to the conventional layout."""
    path = root / MANIFEST_NAME
    if not path.exists():
        return SourceManifest()
    with path.open("rb") as stream:
        data = tomllib.load(stream)
    return SourceManifest(source_dir=str(data.get("project", {}).get("source_dir", "skills")))


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
