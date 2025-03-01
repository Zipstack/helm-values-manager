"""Command line interface for the helm-values-manager plugin."""

import typer

from helm_values_manager.commands.add_deployment_command import AddDeploymentCommand
from helm_values_manager.commands.add_value_config_command import AddValueConfigCommand
from helm_values_manager.commands.init_command import InitCommand
from helm_values_manager.commands.set_value_command import SetValueCommand
from helm_values_manager.models.config_metadata import ConfigMetadata
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
    description: str = typer.Option(
        ConfigMetadata.DEFAULT_DESCRIPTION, "--description", "-d", help="Description of what this configuration does"
    ),
    required: bool = typer.Option(
        ConfigMetadata.DEFAULT_REQUIRED, "--required", "-r", help="Whether this configuration is required"
    ),
    sensitive: bool = typer.Option(
        ConfigMetadata.DEFAULT_SENSITIVE,
        "--sensitive",
        "-s",
        help="Whether this configuration contains sensitive data (coming in v0.2.0)",
        hidden=True,  # Hide from help text until v0.2.0
    ),
):
    """Add a new value configuration with metadata."""
    try:
        command = AddValueConfigCommand()

        # Add warning for sensitive flag until it's fully implemented
        if sensitive:
            HelmLogger.warning("Sensitive value support will be available in version 0.2.0. Flag will be ignored.")
            sensitive = False  # Ignore the flag for now

        result = command.execute(path=path, description=description, required=required, sensitive=sensitive)
        typer.echo(result)
    except Exception as e:
        HelmLogger.error("Failed to add value config: %s", str(e))
        raise typer.Exit(code=1) from e


@app.command("add-deployment")
def add_deployment(
    name: str = typer.Argument(..., help="Deployment name (e.g., 'dev', 'prod')"),
):
    """Add a new deployment configuration."""
    try:
        command = AddDeploymentCommand()

        # Create kwargs for command execution
        kwargs = {
            "name": name,
        }

        result = command.execute(**kwargs)
        typer.echo(result)
    except Exception as e:
        HelmLogger.error("Failed to add deployment: %s", str(e))
        raise typer.Exit(code=1) from e


@app.command("set-value")
def set_value(
    path: str = typer.Option(..., "--path", "-p", help="Configuration path (e.g., 'app.replicas')"),
    deployment: str = typer.Option(
        ..., "--deployment", "-d", help="Deployment to set the value for (e.g., 'dev', 'prod')"
    ),
    value: str = typer.Option(..., "--value", "-v", help="Value to set"),
):
    """Set a value for a specific path and deployment."""
    try:
        command = SetValueCommand()

        # Create kwargs for command execution
        kwargs = {
            "path": path,
            "environment": deployment,  # Map deployment to environment for API compatibility
            "value": value,
        }

        result = command.execute(**kwargs)
        typer.echo(result)
    except Exception as e:
        HelmLogger.error("Failed to set value: %s", str(e))
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app(prog_name=COMMAND_INFO)
