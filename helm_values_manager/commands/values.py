import json
import os
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from helm_values_manager.commands.schema import parse_value_by_type
from helm_values_manager.models import SchemaValue
from helm_values_manager.errors import ErrorHandler, SchemaError
from helm_values_manager.utils import (
    is_secret_reference,
    load_schema,
    load_values,
    save_values,
)

console = Console()
app = typer.Typer()


def find_schema_value(schema, key: str) -> Optional[SchemaValue]:
    """Find a schema value by key."""
    return next((v for v in schema.values if v.key == key), None)


@app.command("set")
def set_command(
    key: str = typer.Argument(..., help="Key of the value to set"),
    value: str = typer.Argument(..., help="Value to set"),
    env: str = typer.Option(..., "--env", "-e", help="Environment name"),
    schema_path: str = typer.Option("schema.json", "--schema", help="Path to schema file"),
    values_path: Optional[str] = typer.Option(None, "--values", help="Path to values file"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Skip confirmation for existing values"
    ),
):
    """Set a value for a specific environment."""
    # Load schema
    schema = load_schema(schema_path)
    if not schema:
        ErrorHandler.print_error("values set", "No schema.json found. Run 'init' first.")

    # Find the schema value
    schema_value = find_schema_value(schema, key)
    if not schema_value:
        ErrorHandler.print_error("values set", f"Key '{key}' not found in schema")

    # Check if value is sensitive
    if schema_value.sensitive:
        ErrorHandler.print_error(
            "values set", f"Key '{key}' is marked as sensitive. Use 'values set-secret' instead."
        )

    # Parse the value according to type
    try:
        parsed_value = parse_value_by_type(value, schema_value.type)
    except (typer.BadParameter, SchemaError) as e:
        ErrorHandler.print_error("values set", str(e))

    # Load existing values
    values = load_values(env, values_path)

    # Check if key already exists and confirm overwrite
    if key in values and not force:
        current_value = values[key]

        # Display current value
        if is_secret_reference(current_value):
            console.print(
                f"Key '{key}' already set as [red][SECRET - {current_value['name']}][/red]"
            )
        else:
            if isinstance(current_value, (dict, list)):
                display_value = json.dumps(current_value)
                if len(display_value) > 50:
                    display_value = display_value[:47] + "..."
            else:
                display_value = str(current_value)
            console.print(f"Key '{key}' already set to: {display_value}")

        if not Confirm.ask("Value already exists. Overwrite?", default=False):
            console.print("Cancelled")
            raise typer.Exit(0)

    # Set the value
    values[key] = parsed_value

    # Save values
    save_values(values, env, values_path)

    console.print(f"[green]✓[/green] Set '{key}' = {parsed_value} for environment '{env}'")


@app.command("set-secret")
def set_secret_command(
    key: str = typer.Argument(..., help="Key of the secret value to set"),
    env: str = typer.Option(..., "--env", "-e", help="Environment name"),
    schema_path: str = typer.Option("schema.json", "--schema", help="Path to schema file"),
    values_path: Optional[str] = typer.Option(None, "--values", help="Path to values file"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Skip confirmation for existing values"
    ),
):
    """Set a secret value for a specific environment."""
    # Load schema
    schema = load_schema(schema_path)
    if not schema:
        ErrorHandler.print_error("values set-secret", "No schema.json found. Run 'init' first.")

    # Find the schema value
    schema_value = find_schema_value(schema, key)
    if not schema_value:
        ErrorHandler.print_error("values set-secret", f"Key '{key}' not found in schema")

    # Check if value is sensitive
    if not schema_value.sensitive:
        ErrorHandler.print_warning(f"Key '{key}' is not marked as sensitive in schema")
        if not Confirm.ask("Continue anyway?", default=False):
            raise typer.Exit(0)

    # Prompt for secret type
    console.print("\n[bold]Secret configuration types:[/bold]")
    console.print("1. Environment variable (env) - Available")
    console.print("2. Vault secrets - [dim]Coming soon[/dim]")
    console.print("3. AWS Secrets Manager - [dim]Coming soon[/dim]")
    console.print("4. Azure Key Vault - [dim]Coming soon[/dim]")

    secret_type = Prompt.ask("Select secret type", choices=["1"], default="1")

    if secret_type == "1":
        # Environment variable configuration
        env_var_name = Prompt.ask("Environment variable name")

        # Check if environment variable exists
        if env_var_name not in os.environ:
            ErrorHandler.print_warning(f"Environment variable '{env_var_name}' is not set")

        # Load existing values
        values = load_values(env, values_path)

        # Check if key already exists and confirm overwrite
        if key in values and not force:
            current_value = values[key]

            # Display current value
            if is_secret_reference(current_value):
                console.print(
                    f"Key '{key}' already set as [red]{current_value['type']}:{current_value['name']}[/red]"
                )
            else:
                # Show non-secret value (shouldn't happen for set-secret, but handle gracefully)
                if isinstance(current_value, (dict, list)):
                    display_value = json.dumps(current_value)
                    if len(display_value) > 50:
                        display_value = display_value[:47] + "..."
                else:
                    display_value = str(current_value)
                console.print(f"Key '{key}' currently set to: {display_value}")
                ErrorHandler.print_warning("This will overwrite a non-secret value with a secret")

            if not Confirm.ask("Overwrite?", default=False):
                console.print("Cancelled")
                raise typer.Exit(0)

        # Set the secret reference
        values[key] = {"type": "env", "name": env_var_name}
    else:
        ErrorHandler.print_error(
            "values set-secret", "Only environment variable secrets are supported in this version"
        )

    # Save values
    save_values(values, env, values_path)

    console.print(
        f"[green]✓[/green] Set secret '{key}' to use environment variable '{env_var_name}' for environment '{env}'"
    )


@app.command("get")
def get_command(
    key: str = typer.Argument(..., help="Key of the value to get"),
    env: str = typer.Option(..., "--env", "-e", help="Environment name"),
    schema_path: str = typer.Option("schema.json", "--schema", help="Path to schema file"),
    values_path: Optional[str] = typer.Option(None, "--values", help="Path to values file"),
):
    """Get a specific value for an environment."""
    # Load values
    values = load_values(env, values_path)

    if key not in values:
        ErrorHandler.print_error("values get", f"Value '{key}' not set for environment '{env}'")

    value = values[key]

    # Mask secrets
    if is_secret_reference(value):
        console.print(f"{key}: [SECRET - env var: {value['name']}]")
    else:
        if isinstance(value, (dict, list)):
            console.print(f"{key}: {json.dumps(value, indent=2)}")
        else:
            console.print(f"{key}: {value}")


@app.command("list")
def list_command(
    env: str = typer.Option(..., "--env", "-e", help="Environment name"),
    schema_path: str = typer.Option("schema.json", "--schema", help="Path to schema file"),
    values_path: Optional[str] = typer.Option(None, "--values", help="Path to values file"),
):
    """List all values for an environment."""
    # Load schema and values
    schema = load_schema(schema_path)
    values = load_values(env, values_path)

    if not values:
        console.print(f"No values set for environment '{env}'")
        return

    # Create table
    table = Table(title=f"Values for environment: {env}")
    table.add_column("Key", style="bold")
    table.add_column("Value")
    table.add_column("Type")

    # Add rows
    for key, value in sorted(values.items()):
        # Find schema info if available
        schema_value = find_schema_value(schema, key) if schema else None
        type_str = schema_value.type if schema_value else "unknown"

        # Format value
        if is_secret_reference(value):
            value_str = f"[red][SECRET - {value['name']}][/red]"
        elif isinstance(value, (dict, list)):
            value_str = json.dumps(value)
            if len(value_str) > 50:
                value_str = value_str[:47] + "..."
        else:
            value_str = str(value)

        table.add_row(key, value_str, type_str)

    console.print(table)


@app.command("remove")
def remove_command(
    key: str = typer.Argument(..., help="Key of the value to remove"),
    env: str = typer.Option(..., "--env", "-e", help="Environment name"),
    values_path: Optional[str] = typer.Option(None, "--values", help="Path to values file"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Remove a value from an environment."""
    # Load values
    values = load_values(env, values_path)

    if key not in values:
        ErrorHandler.print_error("values remove", f"Value '{key}' not set for environment '{env}'")

    # Confirm removal
    if not force:
        value = values[key]
        if is_secret_reference(value):
            console.print(f"Value to remove: {key} = [SECRET - {value['name']}]")
        else:
            console.print(f"Value to remove: {key} = {value}")

        if not Confirm.ask(f"\nRemove this value from environment '{env}'?", default=False):
            console.print("Cancelled")
            raise typer.Exit(0)

    # Remove the value
    del values[key]

    # Save values
    save_values(values, env, values_path)

    console.print(f"[green]✓[/green] Removed '{key}' from environment '{env}'")


@app.command("init")
def init_command(
    env: str = typer.Option(..., "--env", "-e", help="Environment name"),
    schema_path: str = typer.Option("schema.json", "--schema", "-s", help="Path to schema file"),
    values_path: Optional[str] = typer.Option(None, "--values", help="Path to values file"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Use defaults where possible, prompt only for required fields without defaults",
    ),
    skip_defaults: bool = typer.Option(
        False, "--skip-defaults", help="Skip fields with default values entirely"
    ),
):
    """Interactively set up values for an environment."""
    # Load schema
    schema = load_schema(schema_path)
    if not schema:
        ErrorHandler.print_error("values init", "Schema file not found")

    # Load existing values
    values = load_values(env, values_path)

    # Track statistics
    set_count = 0
    skipped_count = 0
    skipped_required = []

    # Sort values: required first, then by key
    sorted_values = sorted(schema.values, key=lambda v: (not v.required, v.key))

    console.print(f"\n[bold]Setting up values for environment: {env}[/bold]\n")

    skip_all = False

    for schema_value in sorted_values:
        # Skip if already set
        if schema_value.key in values:
            continue

        # Skip if user chose to skip all
        if skip_all:
            skipped_count += 1
            if schema_value.required:
                skipped_required.append(schema_value.key)
            continue

        # Display field info
        console.print(f"\n[bold cyan]{schema_value.key}[/bold cyan]")
        console.print(f"  Description: {schema_value.description}")
        console.print(f"  Type: {schema_value.type}")
        console.print(f"  Required: {'Yes' if schema_value.required else 'No'}")
        if schema_value.default is not None:
            console.print(f"  Default: {schema_value.default}")

        # Determine behavior based on flags
        has_default = schema_value.default is not None

        # Handle skip-defaults flag
        if skip_defaults and has_default:
            skipped_count += 1
            console.print("  → Skipping field with default value")
            continue

        # Handle force mode
        if force and has_default:
            # Use defaults automatically in force mode
            values[schema_value.key] = schema_value.default
            set_count += 1
            console.print(f"  → Using default value: {schema_value.default}")
            continue
        elif force and not has_default and not schema_value.required:
            # Skip optional fields without defaults in force mode
            skipped_count += 1
            console.print("  → Skipping optional field without default")
            continue
        elif force and not has_default and schema_value.required:
            # Required fields without defaults must be prompted even in force mode
            console.print("  → Required field with no default, prompting...")
            # Skip the "Set value?" prompt and go directly to value input
            action = "y"  # Force yes for required fields in force mode
        else:
            # Interactive mode - ask if user wants to set value
            action = Prompt.ask(
                f"\nSet value for '{schema_value.key}'?", choices=["y", "n", "skip"], default="y"
            )

        if action == "skip":
            skip_all = True
            skipped_count += 1
            if schema_value.required:
                skipped_required.append(schema_value.key)
            continue
        elif action == "n":
            skipped_count += 1
            if schema_value.required:
                skipped_required.append(schema_value.key)
            continue

        # Set the value
        if schema_value.sensitive:
            # Use set-secret workflow
            console.print("\n[cyan]This is a sensitive value. Setting up as secret...[/cyan]")

            # Display secret type options
            console.print("  1. Environment variable")
            console.print("  [dim]2. HashiCorp Vault (coming soon)[/dim]")
            console.print("  [dim]3. AWS Secrets Manager (coming soon)[/dim]")
            console.print("  [dim]4. Azure Key Vault (coming soon)[/dim]")

            # Select secret type
            secret_type = Prompt.ask("Select secret type", choices=["1"], default="1")

            if secret_type == "1":
                env_var_name = Prompt.ask("Environment variable name")

                # Check if environment variable exists
                if not os.environ.get(env_var_name):
                    ErrorHandler.print_warning(f"Environment variable '{env_var_name}' is not set")

                values[schema_value.key] = {"type": "env", "name": env_var_name}
                set_count += 1
        else:
            # Regular value
            if schema_value.default is not None:
                prompt_text = f"Value (default: {schema_value.default})"
                default_str = str(schema_value.default)
            else:
                prompt_text = "Value"
                default_str = None

            while True:
                value_str = Prompt.ask(prompt_text, default=default_str)

                try:
                    parsed_value = parse_value_by_type(value_str, schema_value.type)
                    values[schema_value.key] = parsed_value
                    set_count += 1
                    break
                except (ValueError, json.JSONDecodeError, typer.BadParameter, SchemaError) as e:
                    console.print(f"[red]Invalid value:[/red] {e}")
                    continue

    # Save values
    save_values(values, env, values_path)

    # Show summary
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Set {set_count} values")
    console.print(f"  Skipped {skipped_count} values")

    if skipped_required:
        ErrorHandler.print_warning("The following required values were not set:")
        for key in skipped_required:
            console.print(f"  - {key}")

    console.print(f"\n[green]✓[/green] Initialization complete for environment '{env}'")
