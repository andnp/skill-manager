import json
import os

from skill_manager.adapters import select_adapters
from skill_manager.sync import deploy, extract_skill, list_installed


def make_source(root):
    skill = root / "skills" / "demo"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("Use {{ model }}.\n", encoding="utf-8")
    (skill / "skill-manager.json").write_text(
        json.dumps({"model": {"claude": "haiku", "default": "cheap"}}), encoding="utf-8"
    )
    hooks = root / "hooks"
    hooks.mkdir()
    (hooks / "notify.sh").write_text("echo notify\n", encoding="utf-8")
    return skill


def test_deploy_lists_and_extracts_newest_skill(tmp_path):
    source = tmp_path / "source"
    home = tmp_path / "home"
    skill = make_source(source)
    adapters = select_adapters(("claude", "codex"), home=home)

    results = deploy(source, adapters)

    assert [result.changed_files for result in results] == [1, 1]
    assert (home / ".claude/skills/demo/SKILL.md").read_text() == "Use haiku.\n"
    assert (home / ".codex/skills/demo/SKILL.md").read_text() == "Use cheap.\n"
    assert (home / ".claude/hooks/notify.sh").exists()
    assert len(list_installed(adapters)) == 2

    codex_file = home / ".codex/skills/demo/SKILL.md"
    codex_file.write_text("Edited by Codex.\n", encoding="utf-8")
    os.utime(codex_file, (2_000_000_000, 2_000_000_000))
    extracted = extract_skill(source, "demo", adapters)

    assert extracted.harness == "codex"
    assert (skill / "SKILL.md").read_text() == "Edited by Codex.\n"
