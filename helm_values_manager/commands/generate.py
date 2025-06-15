"""Generate command implementation."""

from typing import Optional

import typer
from rich.console import Console

from helm_values_manager.errors import ErrorHandler, GeneratorError
from helm_values_manager.generator import generate_values
from helm_values_manager.utils import load_schema, load_values
from helm_values_manager.validator import validate_single_environment

console = Console()
app = typer.Typer()


@app.command()
def generate_command(
    env: str = typer.Option(..., "--env", "-e", help="Environment to generate values for"),
    schema: str = typer.Option("schema.json", "--schema", "-s", help="Path to schema file"),
    values: Optional[str] = typer.Option(
        None, "--values", help="Path to values file (default: values-{env}.json)"
    ),
):
    """Generate values.yaml for a specific environment."""
    # Load schema
    schema_obj = load_schema(schema)
    if not schema_obj:
        ErrorHandler.print_error("generate", "Schema file not found")

    # Load values
    values_data = load_values(env, values)

    # Run validation first
    errors = validate_single_environment(schema_obj, values_data, env)

    if errors:
        ErrorHandler.print_errors(errors, f"generate --env {env}")

    # Generate values.yaml
    try:
        yaml_content = generate_values(schema_obj, values_data, env)
        # Output to stdout
        print(yaml_content, end="")
    except GeneratorError as e:
        ErrorHandler.handle_exception(e, "generate")
    except Exception as e:
        ErrorHandler.handle_exception(e, "generate")
