import json

import pytest

from skill_manager.manifest import load_agent_source
from skill_manager.models import AgentRule
from skill_manager.rendering import VariableError, render_agent_file, render_agent_rule, render_text


def test_rendering_selects_harness_then_default(tmp_path):
    skill = tmp_path / "skills" / "demo"
    skill.mkdir(parents=True)
    (skill / "skill-manager.json").write_text(
        json.dumps({"model": {"claude": "haiku", "default": "cheap"}}), encoding="utf-8"
    )
    template = "Use {{ model }}.\n"

    assert render_text(template, skill, "claude") == "Use haiku.\n"
    assert render_text(template, skill, "codex") == "Use cheap.\n"


def test_rendering_reports_invalid_json(tmp_path):
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "skill-manager.json").write_text("not json", encoding="utf-8")

    with pytest.raises(VariableError, match="invalid JSON"):
        render_text("{{ value }}", skill, "claude")


def test_agent_rendering_composes_shared_and_harness_override(tmp_path):
    agents = tmp_path / "agents"
    agents.mkdir()
    (agents / "shared.md").write_text("# Shared\nUse {{ model }}.\n", encoding="utf-8")
    (agents / "codex.md").write_text("## Codex\n", encoding="utf-8")
    (agents / "skill-manager.json").write_text(
        json.dumps({"model": {"codex": "gpt-5", "default": "safe"}}), encoding="utf-8"
    )

    source = load_agent_source(tmp_path)

    assert source is not None
    assert render_agent_file(source, "codex") == b"# Shared\nUse gpt-5.\n\n## Codex\n"
    assert render_agent_file(source, "claude") == b"# Shared\nUse safe.\n"


def test_agent_rule_rendering_uses_default_variables(tmp_path):
    """Render a scoped rule with its default variable value."""
    source_root = tmp_path / "agents"
    source_root.mkdir()
    (source_root / "skill-manager.json").write_text(
        json.dumps({"model": {"default": "safe"}}), encoding="utf-8"
    )
    rule = AgentRule("python", source_root / "rules/python.md", ("**/*.py",), "Use {{ model }}.\n")

    assert render_agent_rule(rule, source_root, "claude") == "Use safe.\n"
    assert rule.patterns == ("**/*.py",)


def test_agent_rule_rendering_uses_harness_specific_variables(tmp_path):
    """Prefer a harness-specific value when rendering a scoped rule."""
    source_root = tmp_path / "agents"
    source_root.mkdir()
    (source_root / "skill-manager.json").write_text(
        json.dumps({"model": {"codex": "gpt-5", "default": "safe"}}), encoding="utf-8"
    )
    rule = AgentRule("python", source_root / "rules/python.md", ("**/*.py",), "Use {{ model }}.\n")

    assert render_agent_rule(rule, source_root, "codex") == "Use gpt-5.\n"


def test_agent_rule_rendering_preserves_content_without_variables(tmp_path):
    """Return scoped rule content unchanged when it has no variables."""
    source_root = tmp_path / "agents"
    source_root.mkdir()
    content = "Use explicit types.\n"
    rule = AgentRule("python", source_root / "rules/python.md", ("**/*.py",), content)

    assert render_agent_rule(rule, source_root, "claude") == content
