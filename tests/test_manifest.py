from pathlib import Path

import pytest

from skill_manager.manifest import load_agent_source, load_manifest, load_mcp_config


def test_load_mcp_config_reads_servers_and_retirements(tmp_path: Path):
    """Load the source MCP manifest into portable server models."""
    (tmp_path / "mcp").mkdir()
    (tmp_path / "mcp/servers.yaml").write_text(
        "servers:\n  demo:\n    command: demo-mcp\n    args: [run]\n    env:\n      MODE: test\nretired: [old]\n",
        encoding="utf-8",
    )

    config = load_mcp_config(tmp_path)

    assert config.servers[0].name == "demo"
    assert config.servers[0].args == ("run",)
    assert config.servers[0].env == (("MODE", "test"),)
    assert config.retired == ("old",)


def test_load_mcp_config_rejects_invalid_server_command(tmp_path: Path):
    """Reject an MCP entry that cannot describe a launch command."""
    (tmp_path / "mcp").mkdir()
    (tmp_path / "mcp/servers.yaml").write_text("servers:\n  demo: {}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="requires a command"):
        load_mcp_config(tmp_path)


def test_load_manifest_supports_custom_mcp_directory(tmp_path: Path):
    """Read the optional MCP directory alongside the skill directory."""
    (tmp_path / "skill-manager.toml").write_text('[project]\nmcp_dir = "configs/mcp"\n', encoding="utf-8")

    assert load_manifest(tmp_path).mcp_dir == "configs/mcp"


def test_load_agent_source_reads_scoped_rules(tmp_path: Path):
    """Load rule patterns and Markdown content from the neutral source tree."""
    rules = tmp_path / "agents" / "rules"
    rules.mkdir(parents=True)
    rule = rules / "python.md"
    rule.write_text('---\npatterns:\n  - "**/*.py"\n---\nUse type hints.\n', encoding="utf-8")

    source = load_agent_source(tmp_path)

    assert source is not None
    assert source.rules[0].name == "python"
    assert source.rules[0].path == rule
    assert source.rules[0].patterns == ("**/*.py",)
    assert source.rules[0].content == "Use type hints.\n"


def test_load_agent_source_rejects_malformed_rule_frontmatter(tmp_path: Path):
    """Reject YAML that cannot describe scoped rule metadata."""
    rules = tmp_path / "agents" / "rules"
    rules.mkdir(parents=True)
    (rules / "python.md").write_text("---\npatterns: [\n---\nRule\n", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid agent rule frontmatter"):
        load_agent_source(tmp_path)


def test_load_agent_source_rejects_missing_rule_patterns(tmp_path: Path):
    """Reject a rule whose metadata omits its activation patterns."""
    rules = tmp_path / "agents" / "rules"
    rules.mkdir(parents=True)
    (rules / "python.md").write_text("---\nname: Python\n---\nRule\n", encoding="utf-8")

    with pytest.raises(ValueError, match="patterns must be a non-empty list"):
        load_agent_source(tmp_path)


def test_load_agent_source_rejects_rule_paths_outside_source_root(tmp_path: Path):
    """Reject a rule symlink that resolves outside the source rules directory."""
    rules = tmp_path / "agents" / "rules"
    rules.mkdir(parents=True)
    outside = tmp_path / "outside.md"
    outside.write_text('---\npatterns: ["**/*.py"]\n---\nRule\n', encoding="utf-8")
    (rules / "python.md").symlink_to(outside)

    with pytest.raises(ValueError, match="agent rule path escapes"):
        load_agent_source(tmp_path)


def test_load_agent_source_preserves_shared_and_harness_overrides(tmp_path: Path):
    """Keep existing shared and harness-specific agent source loading intact."""
    agents = tmp_path / "agents"
    agents.mkdir()
    shared = agents / "shared.md"
    override = agents / "codex.md"
    shared.write_text("Shared\n", encoding="utf-8")
    override.write_text("Codex\n", encoding="utf-8")

    source = load_agent_source(tmp_path)

    assert source is not None
    assert source.shared == shared
    assert source.overrides == {"codex": override}
    assert source.rules == ()
