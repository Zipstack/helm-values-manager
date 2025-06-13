import json
import os
from typing import Any, Optional

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from helm_values_manager.commands.schema import parse_value_by_type
from helm_values_manager.models import SchemaValue, SecretReference
from helm_values_manager.utils import (
    get_values_file_path,
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
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation for existing values"),
):
    """Set a value for a specific environment."""
    # Load schema
    schema = load_schema(schema_path)
    if not schema:
        console.print("[red]Error:[/red] No schema.json found. Run 'init' first.")
        raise typer.Exit(1)
    
    # Find the schema value
    schema_value = find_schema_value(schema, key)
    if not schema_value:
        console.print(f"[red]Error:[/red] Key '{key}' not found in schema")
        raise typer.Exit(1)
    
    # Check if value is sensitive
    if schema_value.sensitive:
        console.print(f"[red]Error:[/red] Key '{key}' is marked as sensitive. Use 'values set-secret' instead.")
        raise typer.Exit(1)
    
    # Parse the value according to type
    try:
        parsed_value = parse_value_by_type(value, schema_value.type)
    except typer.BadParameter as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    
    # Load existing values
    values = load_values(env, values_path)
    
    # Check if key already exists and confirm overwrite
    if key in values and not force:
        current_value = values[key]
        
        # Display current value
        if is_secret_reference(current_value):
            console.print(f"Key '{key}' already set as [red][SECRET - {current_value['name']}][/red]")
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
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation for existing values"),
):
    """Set a secret value for a specific environment."""
    # Load schema
    schema = load_schema(schema_path)
    if not schema:
        console.print("[red]Error:[/red] No schema.json found. Run 'init' first.")
        raise typer.Exit(1)
    
    # Find the schema value
    schema_value = find_schema_value(schema, key)
    if not schema_value:
        console.print(f"[red]Error:[/red] Key '{key}' not found in schema")
        raise typer.Exit(1)
    
    # Check if value is sensitive
    if not schema_value.sensitive:
        console.print(f"[yellow]Warning:[/yellow] Key '{key}' is not marked as sensitive in schema")
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
            console.print(f"[yellow]Warning:[/yellow] Environment variable '{env_var_name}' is not set")
        
        # Load existing values
        values = load_values(env, values_path)
        
        # Check if key already exists and confirm overwrite
        if key in values and not force:
            current_value = values[key]
            
            # Display current value
            if is_secret_reference(current_value):
                console.print(f"Key '{key}' already set as [red]{current_value['type']}:{current_value['name']}[/red]")
            else:
                # Show non-secret value (shouldn't happen for set-secret, but handle gracefully)
                if isinstance(current_value, (dict, list)):
                    display_value = json.dumps(current_value)
                    if len(display_value) > 50:
                        display_value = display_value[:47] + "..."
                else:
                    display_value = str(current_value)
                console.print(f"Key '{key}' currently set to: {display_value}")
                console.print("[yellow]Warning:[/yellow] This will overwrite a non-secret value with a secret")
            
            if not Confirm.ask("Overwrite?", default=False):
                console.print("Cancelled")
                raise typer.Exit(0)
        
        # Set the secret reference
        values[key] = {"type": "env", "name": env_var_name}
    else:
        console.print("[red]Error:[/red] Only environment variable secrets are supported in this version")
        raise typer.Exit(1)
    
    # Save values
    save_values(values, env, values_path)
    
    console.print(f"[green]✓[/green] Set secret '{key}' to use environment variable '{env_var_name}' for environment '{env}'")


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
        console.print(f"[red]Error:[/red] Value '{key}' not set for environment '{env}'")
        raise typer.Exit(1)
    
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
        console.print(f"[red]Error:[/red] Value '{key}' not set for environment '{env}'")
        raise typer.Exit(1)
    
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