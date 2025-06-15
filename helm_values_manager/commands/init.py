import json
from pathlib import Path

import typer
from rich.console import Console

from helm_values_manager.errors import ErrorHandler

console = Console()

SCHEMA_FILE = "schema.json"


def init_command(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing schema.json"),
):
    """Initialize a new schema.json file with empty schema."""
    schema_path = Path(SCHEMA_FILE)

    if schema_path.exists() and not force:
        ErrorHandler.print_error("init", f"{SCHEMA_FILE} already exists. Use --force to overwrite.")

    initial_schema = {"values": []}

    try:
        with open(schema_path, "w") as f:
            json.dump(initial_schema, f, indent=2)

        console.print(f"[green]✓[/green] Created {SCHEMA_FILE}")
    except Exception as e:
        ErrorHandler.handle_exception(e, "init")
