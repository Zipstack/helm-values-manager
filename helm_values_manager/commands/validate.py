"""Validate command for helm-values-manager."""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from helm_values_manager.errors import ErrorHandler
from helm_values_manager.models import Schema
from helm_values_manager.utils import load_values
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
        ErrorHandler.print_error("validate", "Schema file not found")

    # Load schema
    try:
        with open(schema_path) as f:
            data = json.load(f)
        schema_obj = Schema(**data)
    except json.JSONDecodeError:
        ErrorHandler.print_error("validate", "Invalid JSON in schema file")
    except Exception as e:
        ErrorHandler.print_error("validate", f"Invalid schema: {e}")

    # Load values
    values_data = load_values(env, values)

    # Run validation
    errors = validate_single_environment(schema_obj, values_data, env)

    if errors:
        ErrorHandler.print_errors(errors, f"validate --env {env}")
    else:
        console.print(f"[green]✅[/green] Validation passed for environment: {env}")
