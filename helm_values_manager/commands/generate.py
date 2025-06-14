"""Generate command implementation."""
import sys
from typing import Optional

import typer
from rich.console import Console

from helm_values_manager.generator import GeneratorError, generate_values
from helm_values_manager.utils import get_values_file_path, load_schema, load_values
from helm_values_manager.validator import validate_single_environment

console = Console()
err_console = Console(stderr=True)
app = typer.Typer()


@app.command()
def generate_command(
    env: str = typer.Option(..., "--env", "-e", help="Environment to generate values for"),
    schema: str = typer.Option("schema.json", "--schema", "-s", help="Path to schema file"),
    values: Optional[str] = typer.Option(None, "--values", help="Path to values file (default: values-{env}.json)"),
):
    """Generate values.yaml for a specific environment."""
    # Load schema
    schema_obj = load_schema(schema)
    if not schema_obj:
        err_console.print("[red]Error:[/red] Schema file not found")
        raise typer.Exit(1)
    
    # Determine values file path
    values_path = values or get_values_file_path(env)
    
    # Load values
    values_data = load_values(env, values)
    
    # Run validation first
    errors = validate_single_environment(schema_obj, values_data, env)
    
    if errors:
        err_console.print("[red]Error:[/red] Validation failed. Please fix the following issues:")
        for error in errors:
            err_console.print(f"  - {error}")
        raise typer.Exit(1)
    
    # Generate values.yaml
    try:
        yaml_content = generate_values(schema_obj, values_data, env)
        # Output to stdout
        print(yaml_content, end='')
    except GeneratorError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        err_console.print(f"[red]Error:[/red] Failed to generate values: {e}")
        raise typer.Exit(1)