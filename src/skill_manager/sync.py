"""Deploy, inspect, and reconcile source artifacts."""

import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from .adapters import HarnessAdapter, select_adapters
from .manifest import VARIABLES_NAME, load_agent_source, load_manifest, load_skills
from .models import InstalledSkill, Skill
from .rendering import render_agent_file, render_agent_rule, render_claude_rule, render_copilot_rule, render_file
from .validation import SkillValidation, package_hash, validate

RECEIPT_PATH = Path(".skill-manager/deployment-receipts.json")


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


@dataclass(frozen=True)
class DeploymentReceipt:
    """Evidence for one successfully rendered package deployment."""

    harness: str
    skill: str
    source_hash: str
    deployed_hash: str
    validation: SkillValidation
    created_at: float

    def as_dict(self) -> dict[str, object]:
        return {
            "harness": self.harness,
            "skill": self.skill,
            "source_hash": self.source_hash,
            "deployed_hash": self.deployed_hash,
            "validation": self.validation.as_dict(),
            "created_at": self.created_at,
        }


def _write_rendered(source: Path, destination: Path, skill_dir: Path, harness: str, dry_run: bool) -> bool:
    return _write_content(render_file(source, skill_dir, harness), destination, dry_run)


def _write_content(content: bytes, destination: Path, dry_run: bool) -> bool:
    if destination.exists() and destination.read_bytes() == content:
        return False
    if not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    return True


def _write_opencode_config(destination: Path, rule_paths: list[Path], dry_run: bool) -> bool:
    """Register generated rule paths without overwriting invalid config."""
    if destination.exists():
        try:
            config = json.loads(destination.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid OpenCode config JSON: {destination}: {error}") from error
        if not isinstance(config, dict):
            raise ValueError(f"OpenCode config must be an object: {destination}")
        instructions = config.get("instructions", [])
        if not isinstance(instructions, list):
            raise ValueError(f"OpenCode instructions must be a list: {destination}")
    else:
        config = {}
        instructions = []
    for rule_path in rule_paths:
        path = str(rule_path)
        if path not in instructions:
            instructions.append(path)
    config["instructions"] = instructions
    content = (json.dumps(config, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return _write_content(content, destination, dry_run)


def _remove_stale_files(root: Path, expected: set[Path], dry_run: bool) -> int:
    if not root.exists():
        return 0
    stale = [file for file in root.rglob("*") if file.is_file() and file.relative_to(root) not in expected]
    if not dry_run:
        for file in stale:
            file.unlink()
    return len(stale)


def deploy_skill(skill: Skill, adapters: list[HarnessAdapter], dry_run: bool = False) -> list[Deployment]:
    """Render and deploy one skill to every selected harness."""
    results: list[Deployment] = []
    for adapter in adapters:
        files = [
            source
            for source in skill.files
            if adapter.name == "codex" or source.relative_to(skill.path) != Path("agents/openai.yaml")
        ]
        changed = sum(
            _write_rendered(
                source,
                adapter.destination("skill", skill.name, source.relative_to(skill.path)),
                skill.path,
                adapter.name,
                dry_run,
            )
            for source in files
        )
        destination_root = adapter.root_for("skill") / skill.name
        expected = {source.relative_to(skill.path) for source in files}
        changed += _remove_stale_files(destination_root, expected, dry_run)
        results.append(Deployment(adapter.name, skill.name, changed, len(files)))
    return results


def export_skill(root: Path, destination: Path, name: str, harness: str) -> Deployment:
    """Export one source skill into one repository-local harness directory."""
    skill = next((item for item in load_skills(root) if item.name == name), None)
    if skill is None:
        raise ValueError(f"source skill not found: {name}")
    return deploy_skill(skill, select_adapters((harness,), home=destination))[0]


def export_agent_rules(root: Path, destination: Path, harness: str) -> Deployment:
    """Export source agent rules into a repository-local harness layout."""
    if harness != "agy":
        raise ValueError("repository-local agent export currently supports only the agy harness")
    source = load_agent_source(root)
    rules = source.rules if source else ()
    rendered: list[tuple[Path, bytes]] = []
    for rule in rules:
        content = (
            "---\n"
            "trigger: glob\n"
            "globs:\n"
            + "".join(f"  - {json.dumps(pattern)}\n" for pattern in rule.patterns)
            + "---\n"
            + render_agent_rule(rule, source.root, harness)
        ).encode("utf-8")
        rendered.append((destination / ".agents" / "rules" / f"{rule.name}.md", content))
    conflicts = [path for path, content in rendered if path.exists() and path.read_bytes() != content]
    if conflicts:
        paths = "; ".join(str(path) for path in conflicts)
        raise ValueError(f"agent rule conflict at: {paths}")
    changed = sum(_write_content(content, path, dry_run=False) for path, content in rendered)
    return Deployment(harness, "agents/rules", changed, len(rendered))


def deploy(
    root: Path, adapters: list[HarnessAdapter], names: tuple[str, ...] = (), dry_run: bool = False
) -> list[Deployment]:
    """Deploy selected skills and flat hook/prompt trees from a source repo."""
    source_root = root / load_manifest(root).source_dir
    validation = (
        validate(root, names)
        if names or source_root.exists()
        else SkillValidation(True, (), {}, ())
    )
    if not validation.valid:
        raise ValueError("validation failed: " + "; ".join(validation.errors))
    skills = load_skills(root)
    selected = [skill for skill in skills if not names or skill.name in names]
    results = [result for skill in selected for result in deploy_skill(skill, adapters, dry_run)]
    receipts: list[DeploymentReceipt] = []
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
    if agent_source and (agent_source.shared or agent_source.overrides or agent_source.rules):
        for adapter in adapters:
            if agent_source.shared or agent_source.overrides:
                changed = _write_content(
                    render_agent_file(agent_source, adapter.name), adapter.agent_destination(), dry_run
                )
                results.append(Deployment(adapter.name, "agents", int(changed), 1))
            if adapter.name in {"claude", "copilot", "opencode"}:
                opencode_paths: list[Path] = []
                for rule in agent_source.rules:
                    destination = adapter.agent_rule_destination(rule.name)
                    if destination is None:
                        continue
                    if adapter.name == "claude":
                        content = render_claude_rule(rule, agent_source.root)
                    elif adapter.name == "copilot":
                        content = render_copilot_rule(rule, agent_source.root)
                    else:
                        content = render_agent_rule(rule, agent_source.root, adapter.name)
                    changed = _write_content(
                        content.encode("utf-8"), destination, dry_run
                    )
                    results.append(Deployment(adapter.name, f"agents/rules/{rule.name}", int(changed), 1))
                    if adapter.name == "opencode":
                        opencode_paths.append(destination)
                if opencode_paths:
                    config_destination = adapter.agent_rule_config_destination()
                    if config_destination is None:
                        raise ValueError("OpenCode adapter has no rule config destination")
                    changed = _write_opencode_config(config_destination, opencode_paths, dry_run)
                    results.append(Deployment(adapter.name, "agents/opencode.json", int(changed), 1))
    if selected and not dry_run:
        for skill in selected:
            for adapter in adapters:
                destination = adapter.root_for("skill") / skill.name
                receipts.append(
                    DeploymentReceipt(
                        adapter.name,
                        skill.name,
                        validation.source_hashes[skill.name],
                        package_hash(destination),
                        validation,
                        time.time(),
                    )
                )
        _write_receipts(root, receipts)
    return results


def read_receipts(root: Path) -> list[dict[str, object]]:
    """Read deployment receipts without changing the source repository."""
    path = root / RECEIPT_PATH
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise ValueError(f"invalid deployment receipts: {path}")
    return payload


def _write_receipts(root: Path, receipts: list[DeploymentReceipt]) -> None:
    existing = read_receipts(root)
    current = {
        (str(item.get("harness")), str(item.get("skill"))): item
        for item in existing
        if item.get("harness") and item.get("skill")
    }
    current.update({(receipt.harness, receipt.skill): receipt.as_dict() for receipt in receipts})
    path = root / RECEIPT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(list(current.values()), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


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
