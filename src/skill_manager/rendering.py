"""Harness-aware variable replacement for source artifact files."""

import json
from pathlib import Path
from typing import Any

from jinja2 import StrictUndefined, TemplateError
from jinja2.sandbox import SandboxedEnvironment

from .manifest import VARIABLES_NAME
from .models import AgentRule, AgentSource


class VariableError(ValueError):
    """Raised when a skill variable file is invalid or incomplete."""


def load_variables(skill_dir: Path) -> dict[str, dict[str, str]]:
    """Read the optional per-skill harness/default variable map."""
    path = skill_dir / VARIABLES_NAME
    if not path.exists():
        return {}
    try:
        data: Any = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise VariableError(f"invalid JSON in {path}: {error}") from error
    if not isinstance(data, dict) or any(not isinstance(value, dict) for value in data.values()):
        raise VariableError(f"variables in {path} must map names to harness values")
    return data


def render_text(text: str, skill_dir: Path, harness: str) -> str:
    """Render ``{{ variable }}`` expressions for one harness."""
    variables = load_variables(skill_dir)
    context = {name: values.get(harness, values.get("default", "")) for name, values in variables.items()}
    environment = SandboxedEnvironment(undefined=StrictUndefined, autoescape=False, keep_trailing_newline=True)
    try:
        return environment.from_string(text).render(context)
    except TemplateError as error:
        raise VariableError(f"cannot render {skill_dir.name} for {harness}: {error}") from error


def render_file(path: Path, skill_dir: Path, harness: str) -> bytes:
    """Return rendered text bytes, or the original bytes for binary files."""
    content = path.read_bytes()
    if b"\x00" in content:
        return content
    return render_text(content.decode("utf-8"), skill_dir, harness).encode("utf-8")


def render_agent_rule(rule: AgentRule, source_root: Path, harness: str) -> str:
    """Render one neutral agent rule while preserving its source patterns."""
    return render_text(rule.content, source_root, harness)


def render_claude_rule(rule: AgentRule, source_root: Path) -> str:
    """Render one agent rule using Claude's path-scoped Markdown format."""
    paths = "".join(f"  - {json.dumps(pattern)}\n" for pattern in rule.patterns)
    return f"---\npaths:\n{paths}---\n{render_agent_rule(rule, source_root, 'claude')}"


def render_agent_file(source: AgentSource, harness: str) -> bytes:
    """Compose shared and harness-specific agent Markdown."""
    files = [file for file in (source.shared, source.overrides.get(harness)) if file]
    if not files:
        return b""
    parts = [render_file(file, source.root, harness).decode("utf-8").rstrip("\n") for file in files]
    return "\n\n".join(parts).encode("utf-8") + b"\n"
