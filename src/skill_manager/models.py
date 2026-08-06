"""Small domain models shared by the CLI and harness adapters."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceManifest:
    """Repository-level settings for the source-of-truth tree."""

    source_dir: str = "skills"


@dataclass(frozen=True)
class Skill:
    """A source skill and the files that belong to it."""

    name: str
    path: Path
    summary: str
    files: tuple[Path, ...]


@dataclass(frozen=True)
class InstalledSkill:
    """A skill currently present in one harness's global directory."""

    harness: str
    name: str
    path: Path
    modified_at: float
