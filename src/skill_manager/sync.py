"""Deploy, inspect, and reconcile source artifacts."""

import shutil
from dataclasses import dataclass
from pathlib import Path

from .adapters import HarnessAdapter, select_adapters
from .manifest import VARIABLES_NAME, load_agent_source, load_manifest, load_skills
from .models import InstalledSkill, Skill
from .rendering import render_agent_file, render_file


@dataclass(frozen=True)
class Deployment:
    """The result of copying one source skill to one harness."""

    harness: str
    skill: str
    changed_files: int
    planned_files: int


@dataclass(frozen=True)
class Extraction:
    """The deployed version selected as the source-of-truth update."""

    skill: str
    harness: str
    path: Path
    modified_at: float


def _write_rendered(source: Path, destination: Path, skill_dir: Path, harness: str, dry_run: bool) -> bool:
    return _write_content(render_file(source, skill_dir, harness), destination, dry_run)


def _write_content(content: bytes, destination: Path, dry_run: bool) -> bool:
    if destination.exists() and destination.read_bytes() == content:
        return False
    if not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    return True


def deploy_skill(skill: Skill, adapters: list[HarnessAdapter], dry_run: bool = False) -> list[Deployment]:
    """Render and deploy one skill to every selected harness."""
    results: list[Deployment] = []
    for adapter in adapters:
        changed = sum(
            _write_rendered(
                source,
                adapter.destination("skill", skill.name, source.relative_to(skill.path)),
                skill.path,
                adapter.name,
                dry_run,
            )
            for source in skill.files
        )
        results.append(Deployment(adapter.name, skill.name, changed, len(skill.files)))
    return results


def export_skill(root: Path, destination: Path, name: str, harness: str) -> Deployment:
    """Export one source skill into one repository-local harness directory."""
    skill = next((item for item in load_skills(root) if item.name == name), None)
    if skill is None:
        raise ValueError(f"source skill not found: {name}")
    return deploy_skill(skill, select_adapters((harness,), home=destination))[0]


def deploy(
    root: Path, adapters: list[HarnessAdapter], names: tuple[str, ...] = (), dry_run: bool = False
) -> list[Deployment]:
    """Deploy selected skills and flat hook/prompt trees from a source repo."""
    skills = load_skills(root)
    selected = [skill for skill in skills if not names or skill.name in names]
    results = [result for skill in selected for result in deploy_skill(skill, adapters, dry_run)]
    for kind in ("hook", "prompt"):
        source_root = root / f"{kind}s"
        if not source_root.exists():
            continue
        files = sorted(file for file in source_root.rglob("*") if file.is_file() and file.name != VARIABLES_NAME)
        for adapter in adapters:
            changed = 0
            for source in files:
                destination = adapter.root_for(kind) / source.relative_to(source_root)
                changed += _write_rendered(source, destination, source.parent, adapter.name, dry_run)
            if files:
                results.append(Deployment(adapter.name, f"{kind}s", changed, len(files)))
    agent_source = load_agent_source(root)
    if agent_source and (agent_source.shared or agent_source.overrides):
        for adapter in adapters:
            changed = _write_content(
                render_agent_file(agent_source, adapter.name), adapter.agent_destination(), dry_run
            )
            results.append(Deployment(adapter.name, "agents", int(changed), 1))
    return results


def _latest_mtime(path: Path) -> float:
    files = [file for file in path.rglob("*") if file.is_file()]
    return max((file.stat().st_mtime for file in files), default=0.0)


def list_installed(adapters: list[HarnessAdapter]) -> list[InstalledSkill]:
    """List discovered skills and their latest file modification time."""
    installed: list[InstalledSkill] = []
    for adapter in adapters:
        if not adapter.skills_dir.exists():
            continue
        for path in sorted(item for item in adapter.skills_dir.iterdir() if item.is_dir()):
            modified_at = _latest_mtime(path)
            if modified_at:
                installed.append(InstalledSkill(adapter.name, path.name, path, modified_at))
    return installed


def extract_skill(root: Path, name: str, adapters: list[HarnessAdapter], dry_run: bool = False) -> Extraction:
    """Copy the newest deployed skill version back into the source tree."""
    candidates = [item for item in list_installed(adapters) if item.name == name]
    if not candidates:
        raise ValueError(f"skill '{name}' is not installed in the selected harnesses")
    winner = max(candidates, key=lambda item: item.modified_at)
    source = root / load_manifest(root).source_dir / name
    if not dry_run:
        source.mkdir(parents=True, exist_ok=True)
        for file in winner.path.rglob("*"):
            if file.is_file():
                destination = source / file.relative_to(winner.path)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, destination)
    return Extraction(name, winner.harness, winner.path, winner.modified_at)
