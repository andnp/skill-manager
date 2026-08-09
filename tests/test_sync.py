import json
import os

from skill_manager.adapters import select_adapters
from skill_manager.sync import RECEIPT_PATH, deploy, extract_skill, list_installed


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

    assert [result.changed_files for result in results[:2]] == [1, 1]
    assert {result.skill for result in results[2:]} == {"hooks"}
    assert (home / ".claude/skills/demo/SKILL.md").read_text() == "Use haiku.\n"
    assert (home / ".codex/skills/demo/SKILL.md").read_text() == "Use cheap.\n"
    assert (home / ".claude/hooks/notify.sh").exists()
    assert len(list_installed(adapters)) == 2

    stale = home / ".claude/skills/demo/references/removed.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("old\n", encoding="utf-8")
    (skill / "SKILL.md").write_text("Updated.\n", encoding="utf-8")
    deploy(source, adapters)
    assert not stale.exists()

    codex_file = home / ".codex/skills/demo/SKILL.md"
    codex_file.write_text("Edited by Codex.\n", encoding="utf-8")
    os.utime(codex_file, (2_000_000_000, 2_000_000_000))
    extracted = extract_skill(source, "demo", adapters)

    assert extracted.harness == "codex"
    assert (skill / "SKILL.md").read_text() == "Edited by Codex.\n"


def test_deploy_writes_hash_receipts_for_selected_skills(tmp_path):
    """Record validation and rendered hashes without deploying unrelated artifacts."""
    source = tmp_path / "source"
    home = tmp_path / "home"
    make_source(source)
    (source / "agents").mkdir()
    (source / "agents/shared.md").write_text("Global guidance.\n", encoding="utf-8")
    adapters = select_adapters(("claude",), home=home)

    deploy(source, adapters, ("demo",))

    receipts = json.loads((source / RECEIPT_PATH).read_text(encoding="utf-8"))
    assert len(receipts) == 1
    receipt = receipts[0]
    assert receipt["harness"] == "claude"
    assert receipt["skill"] == "demo"
    assert len(receipt["source_hash"]) == 64
    assert len(receipt["deployed_hash"]) == 64
    assert receipt["validation"]["valid"] is True
    assert (home / ".claude/hooks/notify.sh").exists()
    assert (home / ".claude/CLAUDE.md").exists()


def test_selected_skill_deploy_preserves_global_artifacts(tmp_path):
    """Deploy hooks, prompts, and agents even when a skill name is selected."""
    source = tmp_path / "source"
    home = tmp_path / "home"
    make_source(source)
    (source / "prompts").mkdir()
    (source / "prompts" / "review.md").write_text("Review.\n", encoding="utf-8")
    (source / "agents").mkdir()
    (source / "agents" / "shared.md").write_text("Global.\n", encoding="utf-8")
    adapters = select_adapters(("claude",), home=home)

    deploy(source, adapters, ("demo",))

    assert (home / ".claude/hooks/notify.sh").exists()
    assert (home / ".claude/prompts/review.md").exists()
    assert (home / ".claude/CLAUDE.md").read_text(encoding="utf-8") == "Global.\n"


def test_deploy_writes_harness_agent_files(tmp_path):
    source = tmp_path / "source"
    home = tmp_path / "home"
    agents = source / "agents"
    agents.mkdir(parents=True)
    (agents / "shared.md").write_text("# Shared\n", encoding="utf-8")
    (agents / "claude.md").write_text("## Claude\n", encoding="utf-8")
    (agents / "codex.md").write_text("## Codex\n", encoding="utf-8")
    (agents / "agy.md").write_text("## Agy\n", encoding="utf-8")
    adapters = select_adapters(("claude", "codex", "agy"), home=home)

    deploy(source, adapters)

    assert (home / ".claude/CLAUDE.md").read_text() == "# Shared\n\n## Claude\n"
    assert (home / ".codex/AGENTS.md").read_text() == "# Shared\n\n## Codex\n"
    assert (home / ".gemini/config/AGENTS.md").read_text() == "# Shared\n\n## Agy\n"
