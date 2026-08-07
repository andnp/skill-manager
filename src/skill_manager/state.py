"""Persist remote skill selections for repeatable updates."""

from dataclasses import dataclass
from pathlib import Path

import yaml

STATE_NAME = "state.yaml"


@dataclass(frozen=True)
class GitHubSource:
    repository: str
    skills: tuple[str, ...]


def load_github_sources(root: Path) -> list[GitHubSource]:
    path = root / STATE_NAME
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [
        GitHubSource(str(item["repository"]), tuple(str(name) for name in item.get("skills", [])))
        for item in data.get("github", [])
    ]


def save_github_selection(root: Path, repository: str, skills: tuple[str, ...]) -> None:
    sources = [source for source in load_github_sources(root) if source.repository != repository]
    sources.append(GitHubSource(repository, skills))
    payload = {"github": [{"repository": source.repository, "skills": list(source.skills)} for source in sources]}
    (root / STATE_NAME).write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
