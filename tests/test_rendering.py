import json

import pytest

from skill_manager.manifest import load_agent_source
from skill_manager.rendering import VariableError, render_agent_file, render_text


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
