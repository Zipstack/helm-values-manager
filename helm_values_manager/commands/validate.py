"""Validate command for helm-values-manager."""
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from helm_values_manager.models import Schema
from helm_values_manager.utils import load_schema, load_values, get_values_file_path
from helm_values_manager.validator import validate_single_environment

console = Console()


def validate_command(
    env: str = typer.Option(..., "--env", "-e", help="Environment to validate"),
    schema: str = typer.Option(
        "schema.json",
        "--schema",
        "-s",
        help="Path to schema file",
    ),
    values: Optional[str] = typer.Option(
        None,
        "--values",
        help="Path to values file (default: values-{env}.json)",
    ),
):
    """Validate schema and values file for a specific environment."""
    # Check if schema file exists first
    schema_path = Path(schema)
    if not schema_path.exists():
        console.print("[red]Error:[/red] Schema file not found")
        raise typer.Exit(1)
    
    # Load schema
    try:
        with open(schema_path) as f:
            data = json.load(f)
        schema_obj = Schema(**data)
    except json.JSONDecodeError:
        console.print("[red]Error:[/red] Invalid JSON in schema file")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Invalid schema: {e}")
        raise typer.Exit(1)
    
    # Load values
    values_data = load_values(env, values)
    
    # Run validation
    errors = validate_single_environment(schema_obj, values_data, env)
    
    if errors:
        console.print("[red]Error:[/red] Validation failed:")
        for error in errors:
            # Escape square brackets for Rich
            escaped_error = error.replace("[", "\\[").replace("]", "]")
            console.print(f"  - {escaped_error}")
        raise typer.Exit(1)
    else:
        console.print(f"[green]✅[/green] Validation passed for environment: {env}")