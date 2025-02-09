"""Command line interface for the helm-values-manager plugin."""

import typer

app = typer.Typer(
    name="values-manager",
    help="A Helm plugin to manage values and secrets across environments.",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Helm Values Manager - A plugin to manage values and secrets across environments.

    This plugin helps you manage Helm values and secrets across different
    environments while supporting multiple secret backends like AWS Secrets
    Manager, Azure Key Vault, and HashiCorp Vault.
    """
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def init(
    config_file: str = typer.Option(
        "values-manager.yaml",
        "--config",
        "-c",
        help="Path to the values manager configuration file",
    )
):
    """Initialize a new values manager configuration."""
    typer.echo(f"Initializing values manager with config file: {config_file}")
    # TODO: Implement initialization logic


if __name__ == "__main__":
    app()
