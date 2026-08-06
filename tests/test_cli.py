from click.testing import CliRunner

from skill_manager.cli import main


def test_help_documents_commands():
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    for command in ("init", "deploy", "list", "extract", "discover", "install"):
        assert command in result.output


def test_init_and_deploy_are_scriptable(tmp_path):
    root = tmp_path / "repo"
    home = tmp_path / "home"
    runner = CliRunner()

    result = runner.invoke(main, ["--root", str(root), "init"])
    assert result.exit_code == 0, result.output
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
