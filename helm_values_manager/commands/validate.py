"""Validate command for helm-values-manager."""
from pathlib import Path
from typing import Optional

import typer

from rich.console import Console

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
    # Import here to avoid circular imports
    from helm_values_manager.validator import validate_single_environment
    
    schema_path = Path(schema)
    
    # Run validation for single environment
    success = validate_single_environment(schema_path, env, values)
    
    if not success:
        raise typer.Exit(code=1)