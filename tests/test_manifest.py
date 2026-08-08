from pathlib import Path

import pytest

from skill_manager.manifest import load_manifest, load_mcp_config


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
