import json
import os
from pathlib import Path

import pytest

from skill_manager.adapters import select_adapters
from skill_manager.sync import (
    AGENT_RULE_RECEIPT_PATH,
    RECEIPT_PATH,
    DriftStatus,
    FileComparison,
    deploy,
    diff_skills,
    extract_skill,
    list_installed,
    unified_diff,
)


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


def test_deploy_writes_claude_scoped_rules_only_for_claude(tmp_path):
    """Deploy Claude path-scoped rules without emitting them to Codex."""
    source = tmp_path / "source"
    home = tmp_path / "home"
    agents = source / "agents" / "rules"
    agents.mkdir(parents=True)
    (source / "agents" / "skill-manager.json").write_text(
        json.dumps({"model": {"claude": "haiku", "default": "safe"}}), encoding="utf-8"
    )
    (agents / "python.md").write_text(
        '---\npatterns:\n  - "**/*.py"\n---\nUse {{ model }}.\n', encoding="utf-8"
    )
    adapters = select_adapters(("claude", "codex"), home=home)

    results = deploy(source, adapters)

    rule = home / ".claude/rules/python.md"
    assert rule.read_text(encoding="utf-8") == (
        '---\npaths:\n  - "**/*.py"\n---\nUse haiku.\n'
    )
    assert not (home / ".codex/rules/python.md").exists()
    assert [(result.harness, result.skill) for result in results] == [("claude", "agents/rules/python")]


def test_deploy_dry_run_plans_claude_scoped_rules_without_writing(tmp_path):
    """Plan Claude scoped-rule deployment without creating destination files."""
    source = tmp_path / "source"
    home = tmp_path / "home"
    rules = source / "agents" / "rules"
    rules.mkdir(parents=True)
    (rules / "python.md").write_text(
        '---\npatterns: ["**/*.py"]\n---\nUse explicit types.\n', encoding="utf-8"
    )
    adapters = select_adapters(("claude",), home=home)

    results = deploy(source, adapters, dry_run=True)

    assert [(result.skill, result.changed_files, result.planned_files) for result in results] == [
        ("agents/rules/python", 1, 1)
    ]
    assert not (home / ".claude/rules/python.md").exists()


def test_deploy_writes_copilot_scoped_rules_only_for_copilot(tmp_path):
    """Deploy Copilot applyTo rules without emitting them to other harnesses."""
    source = tmp_path / "source"
    home = tmp_path / "home"
    agents = source / "agents" / "rules"
    agents.mkdir(parents=True)
    (source / "agents" / "skill-manager.json").write_text(
        json.dumps({"model": {"copilot": "gpt-4", "default": "safe"}}), encoding="utf-8"
    )
    (agents / "web.md").write_text(
        '---\npatterns:\n  - "**/*.js"\n  - "**/*.ts"\n---\nUse {{ model }}.\n', encoding="utf-8"
    )
    adapters = select_adapters(("copilot", "claude", "codex", "agy"), home=home)

    results = deploy(source, adapters)

    rule = home / ".copilot/instructions/web.instructions.md"
    assert rule.read_text(encoding="utf-8") == (
        '---\napplyTo: "**/*.js,**/*.ts"\n---\nUse gpt-4.\n'
    )
    assert not (home / ".claude/instructions/web.instructions.md").exists()
    assert not (home / ".codex/instructions/web.instructions.md").exists()
    assert not (home / ".gemini/config/instructions/web.instructions.md").exists()
    assert not (home / ".config/opencode/instructions/web.instructions.md").exists()
    assert [(result.harness, result.skill) for result in results] == [
        ("copilot", "agents/rules/web"),
        ("claude", "agents/rules/web"),
    ]


def test_deploy_dry_run_plans_copilot_scoped_rules_without_writing(tmp_path):
    """Plan Copilot scoped-rule deployment without creating destination files."""
    source = tmp_path / "source"
    home = tmp_path / "home"
    rules = source / "agents" / "rules"
    rules.mkdir(parents=True)
    (rules / "web.md").write_text(
        '---\npatterns: ["**/*.js"]\n---\nUse explicit types.\n', encoding="utf-8"
    )
    adapters = select_adapters(("copilot",), home=home)

    results = deploy(source, adapters, dry_run=True)

    assert [(result.skill, result.changed_files, result.planned_files) for result in results] == [
        ("agents/rules/web", 1, 1)
    ]
    assert not (home / ".copilot/instructions/web.instructions.md").exists()


def test_deploy_registers_opencode_rules_and_preserves_config(tmp_path):
    """Create OpenCode instructions while preserving existing configuration."""
    source = tmp_path / "source"
    home = tmp_path / "home"
    rules = source / "agents" / "rules"
    rules.mkdir(parents=True)
    (rules / "python.md").write_text(
        '---\npatterns: ["**/*.py"]\n---\nUse explicit types.\n', encoding="utf-8"
    )
    config = home / ".config/opencode/opencode.json"
    config.parent.mkdir(parents=True)
    rule_path = home / ".config/opencode/skill-manager/rules/python.md"
    config.write_text(
        json.dumps({"theme": "dark", "instructions": ["existing", str(rule_path)]}), encoding="utf-8"
    )
    adapters = select_adapters(("opencode",), home=home)

    results = deploy(source, adapters)

    assert rule_path.read_text(encoding="utf-8") == "Use explicit types.\n"
    saved = json.loads(config.read_text(encoding="utf-8"))
    assert saved == {"instructions": ["existing", str(rule_path)], "theme": "dark"}
    assert [(result.skill, result.changed_files) for result in results] == [
        ("agents/rules/python", 1),
        ("agents/opencode.json", 1),
    ]


def test_deploy_creates_opencode_config_with_new_instruction(tmp_path):
    """Create an OpenCode config containing each generated rule path."""
    source = tmp_path / "source"
    home = tmp_path / "home"
    rules = source / "agents" / "rules"
    rules.mkdir(parents=True)
    (rules / "python.md").write_text(
        '---\npatterns: ["**/*.py"]\n---\nUse explicit types.\n', encoding="utf-8"
    )
    adapters = select_adapters(("opencode",), home=home)

    deploy(source, adapters)

    rule_path = home / ".config/opencode/skill-manager/rules/python.md"
    assert json.loads((home / ".config/opencode/opencode.json").read_text(encoding="utf-8")) == {
        "instructions": [str(rule_path)]
    }


def test_deploy_dry_run_plans_opencode_rule_and_config_without_writing(tmp_path):
    """Plan OpenCode rule and config deployment without creating files."""
    source = tmp_path / "source"
    home = tmp_path / "home"
    rules = source / "agents" / "rules"
    rules.mkdir(parents=True)
    (rules / "python.md").write_text(
        '---\npatterns: ["**/*.py"]\n---\nUse explicit types.\n', encoding="utf-8"
    )
    adapters = select_adapters(("opencode",), home=home)

    results = deploy(source, adapters, dry_run=True)

    assert [(result.skill, result.changed_files, result.planned_files) for result in results] == [
        ("agents/rules/python", 1, 1),
        ("agents/opencode.json", 1, 1),
    ]
    assert not (home / ".config/opencode/skill-manager/rules/python.md").exists()
    assert not (home / ".config/opencode/opencode.json").exists()


def test_deploy_rejects_invalid_opencode_config(tmp_path):
    """Reject malformed OpenCode JSON and invalid instructions values."""
    cases = (
        ("not json", "invalid OpenCode config JSON"),
        (json.dumps({"instructions": {}}), "instructions must be a list"),
    )
    for value, message in cases:
        source = tmp_path / message.replace(" ", "-")
        home = source / "home"
        rules = source / "agents" / "rules"
        rules.mkdir(parents=True)
        (rules / "python.md").write_text(
            '---\npatterns: ["**/*.py"]\n---\nUse explicit types.\n', encoding="utf-8"
        )
        config = home / ".config/opencode/opencode.json"
        config.parent.mkdir(parents=True)
        config.write_text(value, encoding="utf-8")

        with pytest.raises(ValueError, match=message):
            deploy(source, select_adapters(("opencode",), home=home))


def test_deploy_does_not_emit_opencode_rules_to_other_harnesses(tmp_path):
    """Keep OpenCode rule files and config isolated from other harnesses."""
    source = tmp_path / "source"
    home = tmp_path / "home"
    rules = source / "agents" / "rules"
    rules.mkdir(parents=True)
    (rules / "python.md").write_text(
        '---\npatterns: ["**/*.py"]\n---\nUse explicit types.\n', encoding="utf-8"
    )
    adapters = select_adapters(("claude", "copilot", "codex", "agy"), home=home)

    deploy(source, adapters)

    assert not (home / ".claude/skill-manager/rules/python.md").exists()
    assert not (home / ".copilot/skill-manager/rules/python.md").exists()
    assert not (home / ".codex/skill-manager/rules/python.md").exists()
    assert not (home / ".gemini/config/skill-manager/rules/python.md").exists()


def test_deploy_cleans_stale_claude_and_copilot_rules_only(tmp_path):
    """Remove recorded stale rules while preserving unrelated harness files."""
    source = tmp_path / "source"
    home = tmp_path / "home"
    rules = source / "agents" / "rules"
    rules.mkdir(parents=True)
    (rules / "python.md").write_text(
        '---\npatterns: ["**/*.py"]\n---\nPython.\n', encoding="utf-8"
    )
    (rules / "web.md").write_text(
        '---\npatterns: ["**/*.js"]\n---\nWeb.\n', encoding="utf-8"
    )
    adapters = select_adapters(("claude", "copilot"), home=home)
    deploy(source, adapters)
    unrelated_claude = home / ".claude/rules/manual.md"
    unrelated_copilot = home / ".copilot/instructions/manual.instructions.md"
    unrelated_claude.parent.mkdir(parents=True, exist_ok=True)
    unrelated_copilot.parent.mkdir(parents=True, exist_ok=True)
    unrelated_claude.write_text("Manual.\n", encoding="utf-8")
    unrelated_copilot.write_text("Manual.\n", encoding="utf-8")
    (rules / "web.md").unlink()

    deploy(source, adapters)

    assert not (home / ".claude/rules/web.md").exists()
    assert not (home / ".copilot/instructions/web.instructions.md").exists()
    assert unrelated_claude.exists()
    assert unrelated_copilot.exists()
    records = json.loads((source / AGENT_RULE_RECEIPT_PATH).read_text(encoding="utf-8"))
    assert {record["path"] for record in records} == {
        str(home / ".claude/rules/python.md"),
        str(home / ".copilot/instructions/python.instructions.md"),
    }


def test_deploy_cleans_stale_opencode_rule_and_instruction_only(tmp_path):
    """Remove recorded OpenCode paths while preserving unrelated instructions."""
    source = tmp_path / "source"
    home = tmp_path / "home"
    rules = source / "agents" / "rules"
    rules.mkdir(parents=True)
    (rules / "python.md").write_text(
        '---\npatterns: ["**/*.py"]\n---\nPython.\n', encoding="utf-8"
    )
    adapters = select_adapters(("opencode",), home=home)
    deploy(source, adapters)
    rule_path = home / ".config/opencode/skill-manager/rules/python.md"
    config = home / ".config/opencode/opencode.json"
    saved = json.loads(config.read_text(encoding="utf-8"))
    saved["instructions"].append("user-configured.md")
    config.write_text(json.dumps(saved), encoding="utf-8")
    (rules / "python.md").unlink()

    deploy(source, adapters)

    assert not rule_path.exists()
    assert json.loads(config.read_text(encoding="utf-8"))["instructions"] == ["user-configured.md"]


def test_deploy_dry_run_reports_stale_cleanup_without_mutation(tmp_path):
    """Report recorded stale cleanup without changing files or receipts."""
    source = tmp_path / "source"
    home = tmp_path / "home"
    rules = source / "agents" / "rules"
    rules.mkdir(parents=True)
    (rules / "python.md").write_text(
        '---\npatterns: ["**/*.py"]\n---\nPython.\n', encoding="utf-8"
    )
    adapters = select_adapters(("claude",), home=home)
    deploy(source, adapters)
    receipt = source / AGENT_RULE_RECEIPT_PATH
    receipt_before = receipt.read_text(encoding="utf-8")
    stale = home / ".claude/rules/python.md"
    (rules / "python.md").unlink()

    results = deploy(source, adapters, dry_run=True)

    assert stale.exists()
    assert receipt.read_text(encoding="utf-8") == receipt_before
    assert [(result.skill, result.changed_files, result.planned_files) for result in results] == [
        ("agents/rules cleanup", 1, 1)
    ]


def test_deploy_rejects_invalid_agent_rule_receipt_without_deleting(tmp_path):
    """Reject invalid scoped-rule receipts before any cleanup occurs."""
    source = tmp_path / "source"
    home = tmp_path / "home"
    source.mkdir()
    receipt = source / AGENT_RULE_RECEIPT_PATH
    receipt.parent.mkdir(parents=True)
    receipt.write_text("not json", encoding="utf-8")
    stale = home / ".claude/rules/old.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("Old.\n", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid agent rule receipt JSON"):
        deploy(source, select_adapters(("claude",), home=home))

    assert stale.exists()


def test_diff_reports_a_package_edited_after_deployment(tmp_path):
    source = tmp_path / "source"
    home = tmp_path / "home"
    make_source(source)
    adapters = select_adapters(("claude",), home=home)
    deploy(source, adapters)

    (home / ".claude/skills/demo/SKILL.md").write_text("Edited in place.\n", encoding="utf-8")
    drift = next(item for item in diff_skills(source, adapters) if item.skill == "demo")

    assert drift.status is DriftStatus.DEPLOYED_AHEAD
    assert [str(item.path) for item in drift.changed] == ["SKILL.md"]


def test_diff_reports_source_changes_that_were_never_deployed(tmp_path):
    source = tmp_path / "source"
    home = tmp_path / "home"
    skill = make_source(source)
    adapters = select_adapters(("claude",), home=home)
    deploy(source, adapters)

    (skill / "SKILL.md").write_text("Rewritten source.\n", encoding="utf-8")
    drift = next(item for item in diff_skills(source, adapters) if item.skill == "demo")

    assert drift.status is DriftStatus.SOURCE_AHEAD


def test_diff_reports_a_conflict_when_both_sides_moved(tmp_path):
    source = tmp_path / "source"
    home = tmp_path / "home"
    skill = make_source(source)
    adapters = select_adapters(("claude",), home=home)
    deploy(source, adapters)

    (skill / "SKILL.md").write_text("Rewritten source.\n", encoding="utf-8")
    (home / ".claude/skills/demo/SKILL.md").write_text("Edited in place.\n", encoding="utf-8")
    drift = next(item for item in diff_skills(source, adapters) if item.skill == "demo")

    assert drift.status is DriftStatus.CONFLICT


def test_diff_reports_in_sync_and_undeployed_packages(tmp_path):
    source = tmp_path / "source"
    home = tmp_path / "home"
    make_source(source)
    adapters = select_adapters(("claude",), home=home)

    undeployed = next(item for item in diff_skills(source, adapters) if item.skill == "demo")
    assert undeployed.status is DriftStatus.NOT_DEPLOYED

    deploy(source, adapters)
    assert next(item for item in diff_skills(source, adapters) if item.skill == "demo").status is DriftStatus.IN_SYNC


def test_diff_compares_rendered_output_rather_than_raw_source(tmp_path):
    source = tmp_path / "source"
    home = tmp_path / "home"
    make_source(source)
    adapters = select_adapters(("claude",), home=home)
    deploy(source, adapters)

    drift = next(item for item in diff_skills(source, adapters) if item.skill == "demo")

    assert drift.status is DriftStatus.IN_SYNC
    assert drift.comparisons[0].rendered == b"Use haiku.\n"


def test_diff_reports_a_deployed_file_with_no_source(tmp_path):
    source = tmp_path / "source"
    home = tmp_path / "home"
    make_source(source)
    adapters = select_adapters(("claude",), home=home)
    deploy(source, adapters)

    extra = home / ".claude/skills/demo/references/orphan.md"
    extra.parent.mkdir(parents=True)
    extra.write_text("orphan\n", encoding="utf-8")
    drift = next(item for item in diff_skills(source, adapters) if item.skill == "demo")

    orphan = next(item for item in drift.changed if str(item.path) == "references/orphan.md")
    assert orphan.rendered is None
    assert orphan.deployed == b"orphan\n"


def test_unified_diff_reports_binary_files_without_decoding(tmp_path):
    comparison = FileComparison(Path("logo.png"), tmp_path / "logo.png", b"\xff\xfe\x00", b"\x00\xff")

    assert unified_diff(comparison) == ["Binary file logo.png differs\n"]
