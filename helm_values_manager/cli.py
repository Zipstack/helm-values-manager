import typer
from rich.console import Console

from helm_values_manager import __version__
from helm_values_manager.commands.init import init_command

app = typer.Typer(
    name="helm-values-manager",
    help="Manage Helm value configurations across multiple environments",
    no_args_is_help=True,
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


if __name__ == "__main__":
    app()