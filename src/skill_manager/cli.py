"""Command-line entry point for skill-manager."""

import json
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from . import __version__
from .adapters import ALIASES, MCP_HARNESSES, SUPPORTED_HARNESSES, select_adapters
from .github import DiscoveredSkill, GitHubError, discover, install
from .manifest import MANIFEST_NAME, load_skills
from .mcp import deploy_mcp
from .state import load_github_sources, save_github_selection
from .sync import (
    DriftStatus,
    deploy,
    diff_skills,
    export_agent_rules,
    export_skill,
    extract_skill,
    list_installed,
    read_receipts,
    unified_diff,
)
from .validation import validate

console = Console()
HARNESS_CHOICES = (*SUPPORTED_HARNESSES, *ALIASES)
MCP_HARNESS_CHOICES = (*MCP_HARNESSES, *ALIASES)


def _adapters(ctx: click.Context, names: tuple[str, ...]):
    try:
        return select_adapters(names, home=ctx.obj["home"])
    except ValueError as error:
        raise click.ClickException(str(error)) from error


def _show_discovered(skills: list[DiscoveredSkill]) -> None:
    table = Table(title="Discovered skills")
    table.add_column("Name", style="cyan")
    table.add_column("Summary")
    table.add_column("Files", justify="right")
    for skill in skills:
        table.add_row(skill.name, skill.summary, str(len(skill.files)))
    console.print(table)


def _select_discovered(skills: list[DiscoveredSkill]) -> list[DiscoveredSkill]:
    console.print("Select skills by number, separated by commas, or choose 'all'.")
    value = click.prompt("Selection", default="all")
    if value.strip().lower() == "all":
        return skills
    selected: list[DiscoveredSkill] = []
    for token in value.split(","):
        try:
            index = int(token.strip()) - 1
            selected.append(skills[index])
        except (ValueError, IndexError) as error:
            raise click.ClickException(f"invalid skill selection: {token.strip()}") from error
    return list(dict.fromkeys(selected))


def _install_selected(ctx: click.Context, repository: str, selected: list[DiscoveredSkill], dry_run: bool) -> None:
    if dry_run:
        console.print(f"[yellow]Dry run:[/] would install {len(selected)} skill(s).")
        return
    try:
        for skill in selected:
            destination = install(skill, ctx.obj["root"])
            deploy(ctx.obj["root"], _adapters(ctx, ()), (skill.name,))
            console.print(f"[green]Installed[/] {skill.name} → {destination}")
        if selected:
            save_github_selection(ctx.obj["root"], repository, tuple(skill.name for skill in selected))
    except (GitHubError, OSError, ValueError) as error:
        raise click.ClickException(str(error)) from error


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="skill-manager")
@click.option(
    "--root",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path.cwd,
    show_default="current directory",
    help="Source-of-truth repository.",
)
@click.option(
    "--home",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path.home,
    show_default="user home",
    help="Override harness home paths.",
)
@click.pass_context
def main(ctx: click.Context, root: Path, home: Path) -> None:
    """Manage skills, MCP servers, agent files, hooks, and prompts across harnesses."""
    ctx.ensure_object(dict)
    ctx.obj["root"] = root.expanduser().resolve()
    ctx.obj["home"] = home.expanduser().resolve()


@main.command()
@click.option("--force", is_flag=True, help="Replace an existing repository manifest.")
@click.pass_context
def init(ctx: click.Context, force: bool) -> None:
    """Initialize a source-of-truth repository layout."""
    root = ctx.obj["root"]
    manifest = root / MANIFEST_NAME
    if manifest.exists() and not force:
        raise click.ClickException(f"{manifest} already exists; pass --force to replace it")
    root.mkdir(parents=True, exist_ok=True)
    for directory in ("skills", "agents", "hooks", "prompts", "mcp"):
        (root / directory).mkdir(exist_ok=True)
    manifest.write_text('[project]\nsource_dir = "skills"\nmcp_dir = "mcp"\n', encoding="utf-8")
    console.print(f"[green]Initialized[/] {root}")


@main.command()
@click.option("--skill", "names", multiple=True, help="Validate only this skill; repeat for more than one.")
@click.pass_context
def validate_command(ctx: click.Context, names: tuple[str, ...]) -> None:
    """Validate source skill packages and emit a JSON report."""
    report = validate(ctx.obj["root"], names)
    click.echo(json.dumps(report.as_dict(), sort_keys=True))
    if not report.valid:
        raise click.exceptions.Exit(1)


@main.command(name="deploy")
@click.option("--skill", "names", multiple=True, help="Deploy only this skill; repeat for more than one.")
@click.option(
    "--harness",
    "harnesses",
    multiple=True,
    type=click.Choice(HARNESS_CHOICES),
    help="Target harness; repeat to select a subset.",
)
@click.option("--dry-run", is_flag=True, help="Show planned changes without writing files.")
@click.option("--json", "as_json", is_flag=True, help="Emit a machine-readable deployment report.")
@click.pass_context
def deploy_command(
    ctx: click.Context, names: tuple[str, ...], harnesses: tuple[str, ...], dry_run: bool, as_json: bool
) -> None:
    """Render and deploy source artifacts to selected harnesses."""
    root = ctx.obj["root"]
    available = {skill.name for skill in load_skills(root)}
    missing = sorted(set(names) - available)
    if missing:
        raise click.ClickException(f"source skill(s) not found: {', '.join(missing)}")
    try:
        results = deploy(root, _adapters(ctx, harnesses), names, dry_run)
    except (OSError, ValueError) as error:
        raise click.ClickException(str(error)) from error
    if as_json:
        payload = {"deployments": [result.__dict__ for result in results], "receipts": read_receipts(root)}
        click.echo(json.dumps(payload, sort_keys=True))
        return
    if not results:
        console.print("[yellow]No source skills found.[/]")
        return
    table = Table(title="Deployment")
    table.add_column("Harness", style="cyan")
    table.add_column("Skill")
    table.add_column("Changed", justify="right")
    table.add_column("Planned", justify="right")
    for result in results:
        table.add_row(result.harness, result.skill, str(result.changed_files), str(result.planned_files))
    console.print(table)


DRIFT_STYLES = {
    DriftStatus.IN_SYNC: "green",
    DriftStatus.NOT_DEPLOYED: "yellow",
    DriftStatus.SOURCE_AHEAD: "cyan",
    DriftStatus.DEPLOYED_AHEAD: "magenta",
    DriftStatus.CONFLICT: "red",
    DriftStatus.DIVERGED: "yellow",
}


@main.command(name="diff")
@click.option("--skill", "names", multiple=True, help="Inspect only this skill; repeat for more than one.")
@click.option(
    "--harness",
    "harnesses",
    multiple=True,
    type=click.Choice(HARNESS_CHOICES),
    help="Inspect one harness; repeat for more than one.",
)
@click.option("--all", "show_all", is_flag=True, help="Include packages that are already in sync.")
@click.option("--patch", is_flag=True, help="Print unified diffs instead of a summary table.")
@click.pass_context
def diff_command(
    ctx: click.Context, names: tuple[str, ...], harnesses: tuple[str, ...], show_all: bool, patch: bool
) -> None:
    """Report how deployed packages differ from their source."""
    root = ctx.obj["root"]
    available = {skill.name for skill in load_skills(root)}
    missing = sorted(set(names) - available)
    if missing:
        raise click.ClickException(f"source skill(s) not found: {', '.join(missing)}")
    try:
        drifts = diff_skills(root, _adapters(ctx, harnesses), names)
    except (OSError, ValueError) as error:
        raise click.ClickException(str(error)) from error
    shown = [drift for drift in drifts if show_all or drift.status is not DriftStatus.IN_SYNC]
    if not shown:
        console.print("[green]Every selected package is in sync.[/]")
        return
    if patch:
        for drift in shown:
            for comparison in drift.changed:
                console.print(f"[cyan]{drift.harness}/{drift.skill}[/] [{DRIFT_STYLES[drift.status]}]{drift.status}[/]")
                click.echo("".join(unified_diff(comparison)), nl=False)
        return
    table = Table(title="Drift")
    table.add_column("Harness", style="cyan")
    table.add_column("Skill")
    table.add_column("Status")
    table.add_column("Files", overflow="fold")
    for drift in shown:
        style = DRIFT_STYLES[drift.status]
        files = ", ".join(str(comparison.path) for comparison in drift.changed)
        table.add_row(drift.harness, drift.skill, f"[{style}]{drift.status}[/]", files)
    console.print(table)


@main.command(name="deploy-mcp")
@click.option(
    "--harness",
    "harnesses",
    multiple=True,
    type=click.Choice(MCP_HARNESS_CHOICES),
    help="Target MCP harness; repeat to select a subset.",
)
@click.option("--dry-run", is_flag=True, help="Show planned MCP changes without writing files.")
@click.pass_context
def deploy_mcp_command(ctx: click.Context, harnesses: tuple[str, ...], dry_run: bool) -> None:
    """Merge source MCP servers into user-level harness configurations."""
    try:
        results = deploy_mcp(ctx.obj["root"], _adapters(ctx, harnesses or MCP_HARNESSES), dry_run)
    except (OSError, ValueError) as error:
        raise click.ClickException(str(error)) from error
    table = Table(title="MCP deployment")
    table.add_column("Harness", style="cyan")
    table.add_column("Path", overflow="fold")
    table.add_column("Changed", justify="right")
    for result in results:
        table.add_row(result.harness, str(result.path), "yes" if result.changed else "no")
    console.print(table)


@main.command(name="export")
@click.argument("name")
@click.option("--repo", "repository", required=True, type=click.Path(path_type=Path, exists=True, file_okay=False))
@click.option("--harness", required=True, type=click.Choice(HARNESS_CHOICES))
@click.pass_context
def export_command(ctx: click.Context, name: str, repository: Path, harness: str) -> None:
    """Export one source skill to one repository-local harness directory."""
    try:
        export_skill(ctx.obj["root"], repository.expanduser().resolve(), name, harness)
    except (OSError, ValueError) as error:
        raise click.ClickException(str(error)) from error
    console.print(f"[green]Exported[/] {name} → {harness} ({repository})")


@main.command(name="export-agents")
@click.option("--repo", "repository", required=True, type=click.Path(path_type=Path, exists=True, file_okay=False))
@click.option("--harness", required=True, type=str)
@click.pass_context
def export_agents_command(ctx: click.Context, repository: Path, harness: str) -> None:
    """Export source agent rules to a repository-local harness layout."""
    try:
        result = export_agent_rules(ctx.obj["root"], repository.expanduser().resolve(), harness)
    except (OSError, ValueError) as error:
        raise click.ClickException(str(error)) from error
    console.print(
        f"[green]Exported[/] {result.planned_files} agent rule(s) → {harness} ({repository}); "
        f"{result.changed_files} changed"
    )


@main.command(name="list")
@click.option(
    "--harness",
    "harnesses",
    multiple=True,
    type=click.Choice(HARNESS_CHOICES),
    help="Inspect one harness; repeat for more than one.",
)
@click.pass_context
def list_command(ctx: click.Context, harnesses: tuple[str, ...]) -> None:
    """List skills installed in the selected harnesses."""
    installed = list_installed(_adapters(ctx, harnesses))
    if not installed:
        console.print("[yellow]No installed skills found.[/]")
        return
    table = Table(title="Installed skills")
    table.add_column("Harness", style="cyan")
    table.add_column("Skill")
    table.add_column("Updated")
    table.add_column("Path", overflow="fold")
    for item in installed:
        updated = datetime.fromtimestamp(item.modified_at).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        table.add_row(item.harness, item.name, updated, str(item.path))
    console.print(table)


@main.command()
@click.argument("name")
@click.option(
    "--harness",
    "harnesses",
    multiple=True,
    type=click.Choice(HARNESS_CHOICES),
    help="Search one harness; repeat for more than one.",
)
@click.option("--dry-run", is_flag=True, help="Report the winner without updating source files.")
@click.pass_context
def extract(ctx: click.Context, name: str, harnesses: tuple[str, ...], dry_run: bool) -> None:
    """Reconcile a skill from the newest deployed harness copy."""
    adapters = _adapters(ctx, harnesses)
    try:
        result = extract_skill(ctx.obj["root"], name, adapters, dry_run)
        if not dry_run:
            deploy(ctx.obj["root"], adapters, (name,))
    except (OSError, ValueError) as error:
        raise click.ClickException(str(error)) from error
    action = "would update" if dry_run else "updated"
    redeploy = " and redeployed it" if not dry_run else ""
    console.print(f"[green]Extracted[/] {name}: {action}{redeploy} from {result.harness} ({result.path})")


@main.command(name="discover")
@click.argument("repository")
@click.option("--yes", is_flag=True, help="Install every discovered skill without prompting.")
@click.option("--dry-run", is_flag=True, help="Discover and show selections without downloading files.")
@click.pass_context
def discover_command(ctx: click.Context, repository: str, yes: bool, dry_run: bool) -> None:
    """Discover GitHub skills and optionally install selected packages."""
    try:
        skills = discover(repository)
    except GitHubError as error:
        raise click.ClickException(str(error)) from error
    if not skills:
        console.print("[yellow]No SKILL.md packages found.[/]")
        return
    _show_discovered(skills)
    selected = (
        skills
        if yes or dry_run
        else _select_discovered(skills)
    )
    _install_selected(ctx, repository, selected, dry_run)


@main.command(name="install")
@click.argument("repository")
@click.option("--skill", "names", multiple=True, help="Install only this discovered skill; repeat for more than one.")
@click.pass_context
def install_command(ctx: click.Context, repository: str, names: tuple[str, ...]) -> None:
    """Install discovered GitHub skills without interactive prompts."""
    try:
        skills = discover(repository)
    except GitHubError as error:
        raise click.ClickException(str(error)) from error
    selected = [skill for skill in skills if not names or skill.name in names]
    missing = sorted(set(names) - {skill.name for skill in skills})
    if missing:
        raise click.ClickException(f"discovered skill(s) not found: {', '.join(missing)}")
    _show_discovered(selected)
    _install_selected(ctx, repository, selected, dry_run=False)


@main.command(name="update")
@click.pass_context
def update_command(ctx: click.Context) -> None:
    """Fetch the latest version of every saved GitHub skill selection."""
    sources = load_github_sources(ctx.obj["root"])
    if not sources:
        console.print("[yellow]No saved GitHub skill selections found.[/]")
        return
    for source in sources:
        try:
            discovered = {skill.name: skill for skill in discover(source.repository)}
        except GitHubError as error:
            raise click.ClickException(str(error)) from error
        missing = sorted(set(source.skills) - discovered.keys())
        if missing:
            raise click.ClickException(
                f"{source.repository}: saved skill(s) not found: {', '.join(missing)}"
            )
        selected = [discovered[name] for name in source.skills]
        _install_selected(ctx, source.repository, selected, dry_run=False)
    console.print(f"[green]Updated[/] {sum(len(source.skills) for source in sources)} skill(s).")
