import os
import typer
from rich.console import Console

from helm_values_manager import __version__
from helm_values_manager.commands.init import init_command
from helm_values_manager.commands import schema, values, validate, generate

# Detect if running as helm plugin
is_helm_plugin = os.environ.get("HELM_PLUGIN_DIR") is not None

app = typer.Typer(
    name="helm-values-manager",
    help="Manage Helm value configurations across multiple environments",
    no_args_is_help=True,
    add_completion=not is_helm_plugin,  # Disable completion for helm plugin
)
console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"helm-values-manager version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
):
    pass


app.command("init")(init_command)
app.add_typer(schema.app, name="schema", help="Manage schema values")
app.add_typer(values.app, name="values", help="Manage environment values")
app.command("validate")(validate.validate_command)
app.command("generate")(generate.generate_command)


if __name__ == "__main__":
    app()
