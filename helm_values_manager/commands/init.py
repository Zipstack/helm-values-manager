import json
from pathlib import Path

import typer
from rich.console import Console

console = Console()

SCHEMA_FILE = "schema.json"


def init_command(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing schema.json"),
):
    """Initialize a new schema.json file with empty schema."""
    schema_path = Path(SCHEMA_FILE)
    
    if schema_path.exists() and not force:
        console.print(f"[red]Error:[/red] {SCHEMA_FILE} already exists. Use --force to overwrite.")
        raise typer.Exit(1)
    
    initial_schema = {
        "values": []
    }
    
    try:
        with open(schema_path, "w") as f:
            json.dump(initial_schema, f, indent=2)
        
        console.print(f"[green]✓[/green] Created {SCHEMA_FILE}")
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to create schema file: {e}")
        raise typer.Exit(1)