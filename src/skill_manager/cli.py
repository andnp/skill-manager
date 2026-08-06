"""Command-line entry point for skill-manager."""

import click

from . import __version__


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="skill-manager")
def main() -> None:
    """Manage skills, hooks, and prompts across coding harnesses."""
