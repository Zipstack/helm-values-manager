"""Validate command for helm-values-manager."""
from pathlib import Path
from typing import Optional

import typer

from rich.console import Console

console = Console()


def validate_command(
    schema: str = typer.Option(
        "schema.json",
        "--schema",
        "-s",
        help="Path to schema file",
    ),
    values: Optional[str] = typer.Option(
        None,
        "--values",
        help="Base path for values files (directory containing values-{env}.json files)",
    ),
    env: Optional[str] = typer.Option(
        None,
        "--env",
        "-e",
        help="Validate specific environment only",
    ),
):
    """Validate schema and values files."""
    # Import here to avoid circular imports
    from helm_values_manager.validator import validate_command as run_validation
    
    schema_path = Path(schema)
    values_base_path = Path(values) if values else Path(".")
    
    # Run validation
    success = run_validation(schema_path, values_base_path, env)
    
    if not success:
        raise typer.Exit(code=1)