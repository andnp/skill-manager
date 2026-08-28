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
AGENT_RULE_RECEIPT_PATH = Path(".skill-manager/agent-rule-receipts.json")


@dataclass(frozen=True)
class Deployment:
    """The result of copying one source skill to one harness."""

    harness: str
    skill: str
    changed_files: int
    planned_files: int


@dataclass(frozen=True)
class FileComparison:
    """One source file's rendered content measured against its deployed copy."""

    path: Path
    destination: Path
    rendered: bytes | None
    deployed: bytes | None

    @property
    def changed(self) -> bool:
        return self.rendered != self.deployed


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


def _read_agent_rule_receipts(root: Path) -> list[dict[str, str]]:
    """Read the owned scoped-rule paths from the previous deployment."""
    path = root / AGENT_RULE_RECEIPT_PATH
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid agent rule receipt JSON: {path}: {error}") from error
    if not isinstance(payload, list) or not all(
        isinstance(item, dict)
        and isinstance(item.get("harness"), str)
        and isinstance(item.get("path"), str)
        for item in payload
    ):
        raise ValueError(f"invalid agent rule receipt: {path}")
    return payload


def _write_agent_rule_receipts(root: Path, records: list[dict[str, str]]) -> None:
    path = root / AGENT_RULE_RECEIPT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_opencode_config(
    destination: Path, rule_paths: list[Path], stale_paths: list[Path], dry_run: bool
) -> bool:
    """Register generated rule paths without overwriting invalid config."""
    if not destination.exists() and not rule_paths:
        return False
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
    stale_values = {str(path) for path in stale_paths}
    config["instructions"] = [path for path in instructions if path not in stale_values]
    content = (json.dumps(config, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return _write_content(content, destination, dry_run)


def _scoped_rule_root(adapter: HarnessAdapter) -> Path:
    if adapter.name == "claude":
        return adapter.agent_file.parent / "rules"
    if adapter.name == "copilot":
        return adapter.agent_file.parent / "instructions"
    if adapter.name == "opencode":
        return adapter.agent_file.parent / "skill-manager" / "rules"
    raise ValueError(f"unsupported scoped-rule harness: {adapter.name}")


def _validate_owned_rule_path(adapter: HarnessAdapter, path: Path) -> None:
    valid_name = path.name.endswith(".instructions.md") if adapter.name == "copilot" else path.suffix == ".md"
    if not path.is_absolute() or path.parent != _scoped_rule_root(adapter) or not valid_name:
        raise ValueError(f"invalid agent rule receipt path for {adapter.name}: {path}")


def _reconcile_stale_agent_rules(
    prior: list[dict[str, str]],
    adapters: list[HarnessAdapter],
    expected: dict[str, list[Path]],
    dry_run: bool,
) -> tuple[list[Deployment], dict[str, list[Path]], list[dict[str, str]]]:
    """Remove only recorded stale files and return updated ownership records."""
    results: list[Deployment] = []
    stale_by_harness: dict[str, list[Path]] = {}
    active = {adapter.name for adapter in adapters}
    records = [record for record in prior if record["harness"] not in active]
    for adapter in adapters:
        if adapter.name not in {"claude", "copilot", "opencode"}:
            continue
        current = {str(path) for path in expected.get(adapter.name, [])}
        prior_paths = [
            Path(record["path"])
            for record in prior
            if record["harness"] == adapter.name
        ]
        stale = []
        for path in prior_paths:
            _validate_owned_rule_path(adapter, path)
            if str(path) not in current:
                stale.append(path)
        stale_by_harness[adapter.name] = stale
        for path in stale:
            if path.exists():
                if not dry_run:
                    path.unlink()
                results.append(Deployment(adapter.name, "agents/rules cleanup", 1, 1))
        records.extend(
            {"harness": adapter.name, "path": str(path)}
            for path in expected.get(adapter.name, [])
        )
    return results, stale_by_harness, records


def _deployable_files(skill: Skill, adapter: HarnessAdapter) -> list[Path]:
    return [
        source
        for source in skill.files
        if adapter.name == "codex" or source.relative_to(skill.path) != Path("agents/openai.yaml")
    ]


def compare_skill(skill: Skill, adapter: HarnessAdapter) -> list[FileComparison]:
    """Measure one skill's rendered files against their deployed copies."""
    comparisons: list[FileComparison] = []
    for source in _deployable_files(skill, adapter):
        relative = source.relative_to(skill.path)
        destination = adapter.destination("skill", skill.name, relative)
        comparisons.append(
            FileComparison(
                relative,
                destination,
                render_file(source, skill.path, adapter.name),
                destination.read_bytes() if destination.is_file() else None,
            )
        )
    expected = {comparison.path for comparison in comparisons}
    root = adapter.root_for("skill") / skill.name
    if root.is_dir():
        for existing in sorted(root.rglob("*")):
            relative = existing.relative_to(root)
            if existing.is_file() and relative not in expected:
                comparisons.append(FileComparison(relative, existing, None, existing.read_bytes()))
    return comparisons


def deploy_skill(skill: Skill, adapters: list[HarnessAdapter], dry_run: bool = False) -> list[Deployment]:
    """Render and deploy one skill to every selected harness."""
    results: list[Deployment] = []
    for adapter in adapters:
        comparisons = compare_skill(skill, adapter)
        changed = sum(
            _write_content(comparison.rendered, comparison.destination, dry_run)
            for comparison in comparisons
            if comparison.rendered is not None
        )
        stale = [comparison for comparison in comparisons if comparison.rendered is None]
        if not dry_run:
            for comparison in stale:
                comparison.destination.unlink()
        results.append(
            Deployment(adapter.name, skill.name, changed + len(stale), len(comparisons) - len(stale))
        )
    return results


def export_skill(root: Path, destination: Path, name: str, harness: str) -> Deployment:
    """Export one source skill into one repository-local harness directory."""
    skill = next((item for item in load_skills(root) if item.name == name), None)
    if skill is None:
        raise ValueError(f"source skill not found: {name}")
    return deploy_skill(skill, select_adapters((harness,), home=destination))[0]


def export_agent_rules(root: Path, destination: Path, harness: str) -> Deployment:
    """Export source agent rules into a repository-local harness layout."""
    if harness not in {"agy", "codex"}:
        raise ValueError(
            "repository-local agent export currently supports only the agy harness "
            "and representable codex directories"
        )
    source = load_agent_source(root)
    rules = source.rules if source else ()
    source_root = source.root if source else root
    if harness == "codex":
        sections: dict[Path, list[tuple[str, str]]] = {}
        for rule in rules:
            directories = set()
            for pattern in rule.patterns:
                if pattern.endswith("/**/*"):
                    directory = pattern[:-5]
                elif pattern.endswith("/**"):
                    directory = pattern[:-3]
                else:
                    raise ValueError(
                        f"Codex requires a directory-representable pattern, got: {pattern}"
                    )
                path = Path(directory)
                if not directory or path.is_absolute() or any(char in directory for char in "*?[]"):
                    raise ValueError(
                        f"Codex requires a directory-representable pattern, got: {pattern}"
                    )
                if ".." in path.parts:
                    raise ValueError(f"unsafe Codex rule directory: {directory}")
                directories.add(path)
            body = render_agent_rule(rule, source_root, harness)
            for directory in directories:
                sections.setdefault(directory, []).append((rule.name, body))
        rendered = []
        for directory, entries in sorted(sections.items()):
            ordered = sorted(entries)
            if len(ordered) == 1:
                content = ordered[0][1]
            else:
                content = "\n\n".join(f"## {name}\n{body.rstrip()}" for name, body in ordered) + "\n"
            rendered.append((destination / directory / "AGENTS.md", content.encode("utf-8")))
    else:
        rendered = []
        for rule in rules:
            content = (
                "---\n"
                "trigger: glob\n"
                "globs:\n"
                + "".join(f"  - {json.dumps(pattern)}\n" for pattern in rule.patterns)
                + "---\n"
                + render_agent_rule(rule, source_root, harness)
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
    prior_agent_rules = _read_agent_rule_receipts(root)
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
    expected_agent_rules: dict[str, list[Path]] = {}
    if agent_source and (agent_source.shared or agent_source.overrides or agent_source.rules):
        for adapter in adapters:
            if agent_source.shared or agent_source.overrides:
                changed = _write_content(
                    render_agent_file(agent_source, adapter.name), adapter.agent_destination(), dry_run
                )
                results.append(Deployment(adapter.name, "agents", int(changed), 1))
            if adapter.name in {"claude", "copilot", "opencode"}:
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
                    expected_agent_rules.setdefault(adapter.name, []).append(destination)
    cleanup, stale_by_harness, agent_rule_records = _reconcile_stale_agent_rules(
        prior_agent_rules, adapters, expected_agent_rules, dry_run
    )
    results.extend(cleanup)
    for adapter in adapters:
        if adapter.name != "opencode":
            continue
        current_paths = expected_agent_rules.get(adapter.name, [])
        stale_paths = stale_by_harness.get(adapter.name, [])
        if not current_paths and not stale_paths:
            continue
        config_destination = adapter.agent_rule_config_destination()
        if config_destination is None:
            raise ValueError("OpenCode adapter has no rule config destination")
        changed = _write_opencode_config(config_destination, current_paths, stale_paths, dry_run)
        results.append(Deployment(adapter.name, "agents/opencode.json", int(changed), 1))
    if not dry_run and (prior_agent_rules or expected_agent_rules):
        _write_agent_rule_receipts(root, agent_rule_records)
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
