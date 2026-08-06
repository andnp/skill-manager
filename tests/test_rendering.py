import json

import pytest

from skill_manager.rendering import VariableError, render_text


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
