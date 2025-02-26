"""Command line interface for the helm-values-manager plugin."""

from typing import Optional

import typer

from helm_values_manager.commands.add_value_config_command import AddValueConfigCommand
from helm_values_manager.commands.init_command import InitCommand
from helm_values_manager.utils.logger import HelmLogger

COMMAND_INFO = "helm values-manager"

app = typer.Typer(
    name="values-manager",
    help="A Helm plugin to manage values and secrets across environments.",
    add_completion=True,
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Helm Values Manager - A plugin to manage values and secrets across environments.

    This plugin helps you manage Helm values and secrets across different
    environments while supporting multiple secret backends like AWS Secrets
    Manager, Azure Key Vault, and HashiCorp Vault.
    """
    ctx.info_name = COMMAND_INFO
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def init(
    release_name: str = typer.Option(..., "--release", "-r", help="Name of the Helm release"),
):
    """Initialize a new values manager configuration."""
    try:
        command = InitCommand()
        result = command.execute(release_name=release_name)
        typer.echo(result)
    except Exception as e:
        HelmLogger.error("Failed to initialize: %s", str(e))
        raise typer.Exit(code=1) from e


@app.command("add-value-config")
def add_value_config(
    path: str = typer.Option(..., "--path", "-p", help="Configuration path (e.g., 'app.replicas')"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Description of what this configuration does"
    ),
    required: bool = typer.Option(False, "--required", "-r", help="Whether this configuration is required"),
    sensitive: bool = typer.Option(
        False, "--sensitive", "-s", help="Whether this configuration contains sensitive data"
    ),
):
    """Add a new value configuration with metadata."""
    try:
        command = AddValueConfigCommand()
        result = command.execute(path=path, description=description, required=required, sensitive=sensitive)
        typer.echo(result)
    except Exception as e:
        HelmLogger.error("Failed to add value config: %s", str(e))
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app(prog_name=COMMAND_INFO)
