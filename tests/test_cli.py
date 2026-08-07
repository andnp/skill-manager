from pathlib import Path

from click.testing import CliRunner

from skill_manager.cli import main
from skill_manager.github import DiscoveredSkill
from skill_manager.state import save_github_selection


def test_help_documents_commands():
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    for command in ("init", "deploy", "export", "list", "extract", "discover", "install", "update"):
        assert command in result.output


def test_init_and_deploy_are_scriptable(tmp_path):
    root = tmp_path / "repo"
    home = tmp_path / "home"
    runner = CliRunner()

    result = runner.invoke(main, ["--root", str(root), "init"])
    assert result.exit_code == 0, result.output
    assert (root / "agents").is_dir()
    skill = root / "skills" / "demo"
    skill.mkdir()
    (skill / "SKILL.md").write_text("Do the thing.\n", encoding="utf-8")

    result = runner.invoke(
        main,
        [
            "--root",
            str(root),
            "--home",
            str(home),
            "deploy",
            "--harness",
            "claude",
            "--harness",
            "codex",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (home / ".claude/skills/demo/SKILL.md").read_text() == "Do the thing.\n"

    (home / ".codex/skills/demo/SKILL.md").write_text("Edited by Codex.\n", encoding="utf-8")
    result = runner.invoke(
        main,
        [
            "--root",
            str(root),
            "--home",
            str(home),
            "extract",
            "demo",
            "--harness",
            "claude",
            "--harness",
            "codex",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (home / ".claude/skills/demo/SKILL.md").read_text() == "Edited by Codex.\n"


def test_discover_multiselect_persists_selection(tmp_path, monkeypatch):
    skills = [
        DiscoveredSkill("alpha", "Alpha", "acme/demo", "alpha", ("alpha/SKILL.md",)),
        DiscoveredSkill("beta", "Beta", "acme/demo", "beta", ("beta/SKILL.md",)),
    ]
    monkeypatch.setattr("skill_manager.cli.discover", lambda repository: skills)
    monkeypatch.setattr("skill_manager.cli.install", lambda skill, root: Path(root) / skill.name)
    monkeypatch.setattr("skill_manager.cli.deploy", lambda *args: [])

    result = CliRunner().invoke(main, ["--root", str(tmp_path), "discover", "acme/demo"], input="1,2\n")

    assert result.exit_code == 0, result.output
    assert (tmp_path / "state.yaml").read_text() == (
        "github:\n- repository: acme/demo\n  skills:\n  - alpha\n  - beta\n"
    )


def test_update_replays_saved_selection(tmp_path, monkeypatch):
    save_github_selection(tmp_path, "acme/demo", ("beta",))
    skill = DiscoveredSkill("beta", "Beta", "acme/demo", "beta", ("beta/SKILL.md",))
    installed: list[str] = []
    monkeypatch.setattr("skill_manager.cli.discover", lambda repository: [skill])
    monkeypatch.setattr("skill_manager.cli.install", lambda selected, root: installed.append(selected.name) or tmp_path)
    monkeypatch.setattr("skill_manager.cli.deploy", lambda *args: [])

    result = CliRunner().invoke(main, ["--root", str(tmp_path), "update"])

    assert result.exit_code == 0, result.output
    assert installed == ["beta"]


def test_export_copies_rendered_skill_to_repository_harness(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "monorepo"
    home = tmp_path / "home"
    skill = source / "skills" / "demo"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("Use {{ audience }}.\n", encoding="utf-8")
    (skill / "skill-manager.json").write_text('{"audience": {"claude": "Claude"}}', encoding="utf-8")
    references = skill / "references"
    references.mkdir()
    (references / "guide.md").write_text("Guide for {{ audience }}.\n", encoding="utf-8")
    target.mkdir()

    result = CliRunner().invoke(
        main,
        ["--root", str(source), "--home", str(home), "export", "demo", "--repo", str(target), "--harness", "claude"],
    )

    assert result.exit_code == 0, result.output
    assert (target / ".claude/skills/demo/SKILL.md").read_text() == "Use Claude.\n"
    assert (target / ".claude/skills/demo/references/guide.md").read_text() == "Guide for Claude.\n"
    assert not (home / ".claude/skills/demo").exists()
    assert not (source / "state.yaml").exists()


def test_export_reports_missing_source_skill(tmp_path):
    target = tmp_path / "monorepo"
    target.mkdir()

    result = CliRunner().invoke(
        main,
        ["--root", str(tmp_path / "source"), "export", "missing", "--repo", str(target), "--harness", "claude"],
    )

    assert result.exit_code != 0
    assert "source skill not found: missing" in result.output
