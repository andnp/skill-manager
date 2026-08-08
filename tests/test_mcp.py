import json
from pathlib import Path

from click.testing import CliRunner

from skill_manager.adapters import select_adapters
from skill_manager.cli import main
from skill_manager.mcp import render_mcp_config
from skill_manager.models import McpConfig, McpServer


def test_render_json_configs_preserves_unmanaged_servers(tmp_path: Path):
    """Merge managed servers into JSON without discarding existing entries."""
    path = tmp_path / "mcp.json"
    path.write_text(json.dumps({"other": True, "mcpServers": {"custom": {"command": "keep"}}}), encoding="utf-8")
    config = McpConfig((McpServer("repowise", "repowise", ("mcp",)),), ("codegraph",))

    rendered = render_mcp_config(select_adapters(("claude",), tmp_path)[0], config, path)
    data = json.loads(rendered)

    assert data["other"] is True
    assert data["mcpServers"]["custom"] == {"command": "keep"}
    assert data["mcpServers"]["repowise"]["type"] == "stdio"


def test_render_codex_config_preserves_unmanaged_tables(tmp_path: Path):
    """Merge Codex MCP tables without replacing unrelated TOML settings."""
    path = tmp_path / "config.toml"
    path.write_text('[features]\nhooks = true\n\n[mcp_servers.custom]\ncommand = "keep"\n', encoding="utf-8")
    config = McpConfig((McpServer("repowise", "repowise", ("mcp",)),), ("codegraph",))

    rendered = render_mcp_config(select_adapters(("codex",), tmp_path)[0], config, path).decode()

    assert "hooks = true" in rendered
    assert '[mcp_servers.custom]' in rendered
    assert '[mcp_servers.repowise]' in rendered


def test_render_mcp_config_rejects_opencode(tmp_path: Path):
    """Reject MCP deployment for the explicitly deferred OpenCode target."""
    path = tmp_path / "config.json"
    config = McpConfig((McpServer("repowise", "repowise"),))

    try:
        render_mcp_config(select_adapters(("opencode",), tmp_path)[0], config, path)
    except ValueError as error:
        assert "not supported" in str(error)
    else:
        raise AssertionError("OpenCode MCP rendering unexpectedly succeeded")


def test_deploy_mcp_updates_selected_user_configs(tmp_path: Path):
    """Deploy the source manifest and retire CodeGraph across all MCP targets."""
    source = tmp_path / "source"
    home = tmp_path / "home"
    (source / "mcp").mkdir(parents=True)
    home.mkdir()
    (source / "mcp/servers.yaml").write_text(
        "servers:\n  repowise:\n    command: repowise\n    args: [mcp]\nretired: [codegraph]\n",
        encoding="utf-8",
    )
    (home / ".claude.json").write_text(
        json.dumps({"mcpServers": {"custom": {"command": "keep"}, "codegraph": {"command": "old"}}}),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        main,
        ["--root", str(source), "--home", str(home), "deploy-mcp"],
    )

    assert result.exit_code == 0, result.output
    data = json.loads((home / ".claude.json").read_text())
    assert set(data["mcpServers"]) == {"custom", "repowise"}
    assert (home / ".codex/config.toml").exists()
    assert (home / ".copilot/mcp-config.json").exists()
    assert (home / ".gemini/config/mcp_config.json").exists()
