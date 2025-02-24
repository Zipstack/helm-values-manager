"""Command line interface for the helm-values-manager plugin."""

import typer

from helm_values_manager.commands.init_command import InitCommand
from helm_values_manager.commands.registry import CommandRegistry
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
        # Initialize command registry and register commands
        registry = CommandRegistry()
        registry.register("init", InitCommand)
        command = registry.get_command("init")()
        result = command.execute(release_name=release_name)
        typer.echo(result)
    except Exception as e:
        HelmLogger.error("Failed to initialize: %s", str(e))
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app(prog_name=COMMAND_INFO)
