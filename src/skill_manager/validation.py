"""Validate source skill packages before deployment."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from .adapters import SUPPORTED_HARNESSES
from .manifest import VARIABLES_NAME, load_manifest
from .rendering import VariableError, load_variables, render_file


@dataclass(frozen=True)
class SkillValidation:
    """Machine-readable validation evidence for selected source packages."""

    valid: bool
    skills: tuple[str, ...]
    source_hashes: dict[str, str]
    errors: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "skills": list(self.skills),
            "source_hashes": dict(self.source_hashes),
            "errors": list(self.errors),
        }


def package_hash(path: Path) -> str:
    """Hash a package's regular files in stable relative-path order."""
    digest = hashlib.sha256()
    for file in sorted(path.rglob("*")):
        if not file.is_file() or file.is_symlink():
            continue
        digest.update(str(file.relative_to(path)).encode("utf-8"))
        digest.update(b"\0")
        digest.update(file.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def validate(root: Path, names: tuple[str, ...] = ()) -> SkillValidation:
    """Validate package structure, variables, rendering, and source paths."""
    source_root = root / load_manifest(root).source_dir
    selected = tuple(names) or tuple(
        sorted(path.name for path in source_root.iterdir() if path.is_dir() and not path.name.startswith("."))
    ) if source_root.exists() else ()
    errors: list[str] = []
    source_hashes: dict[str, str] = {}

    if not source_root.is_dir():
        errors.append(f"source directory not found: {source_root}")
    for name in selected:
        package = source_root / name
        if not package.is_dir() or package.is_symlink():
            errors.append(f"invalid skill package: {name}")
            continue
        files = [path for path in package.rglob("*") if path.is_file()]
        if not files:
            errors.append(f"skill package is empty: {name}")
            continue
        if not (package / "SKILL.md").is_file() or (package / "SKILL.md").is_symlink():
            errors.append(f"skill package is missing SKILL.md: {name}")
        for path in package.rglob("*"):
            if path.is_symlink():
                errors.append(f"skill package contains a symlink: {name}/{path.relative_to(package)}")
        try:
            load_variables(package)
            for file in files:
                if file.name == VARIABLES_NAME:
                    continue
                for harness in SUPPORTED_HARNESSES:
                    render_file(file, package, harness)
        except (OSError, VariableError, UnicodeError) as error:
            errors.append(f"skill package cannot render: {name}: {error}")
        source_hashes[name] = package_hash(package)

    return SkillValidation(not errors, selected, source_hashes, tuple(errors))
