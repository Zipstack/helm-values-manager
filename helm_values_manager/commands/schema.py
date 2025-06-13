import json
from typing import Any, Optional

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

from helm_values_manager.models import SchemaValue, ValueType
from helm_values_manager.utils import load_schema, save_schema, validate_key_unique, validate_path_format

console = Console()
app = typer.Typer()


def parse_value_by_type(value_str: str, value_type: ValueType) -> Any:
    """Parse string input based on the specified type."""
    if value_type == "string":
        return value_str
    elif value_type == "number":
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            raise typer.BadParameter(f"Invalid number: {value_str}")
    elif value_type == "boolean":
        lower = value_str.lower()
        if lower in ("true", "yes", "y", "1"):
            return True
        elif lower in ("false", "no", "n", "0"):
            return False
        else:
            raise typer.BadParameter(f"Invalid boolean: {value_str}")
    elif value_type == "array":
        try:
            return json.loads(value_str)
        except json.JSONDecodeError:
            # Try simple comma-separated values
            return [v.strip() for v in value_str.split(",") if v.strip()]
    elif value_type == "object":
        try:
            return json.loads(value_str)
        except json.JSONDecodeError:
            raise typer.BadParameter(f"Invalid JSON object: {value_str}")


@app.command("add")
def add_command(
    schema_path: str = typer.Option("schema.json", "--schema", help="Path to schema file"),
):
    """Add a new value to the schema interactively."""
    # Load existing schema
    schema = load_schema(schema_path)
    if not schema:
        console.print("[red]Error:[/red] No schema.json found. Run 'init' first.")
        raise typer.Exit(1)
    
    console.print("[bold]Add new value to schema[/bold]\n")
    
    # Prompt for key
    while True:
        key = Prompt.ask("Key (unique identifier)")
        if not key:
            console.print("[red]Key cannot be empty[/red]")
            continue
        
        if not validate_key_unique(schema, key):
            console.print(f"[red]Key '{key}' already exists in schema[/red]")
            continue
        
        break
    
    # Prompt for path
    while True:
        path = Prompt.ask("Path (dot-separated YAML path)")
        if not validate_path_format(path):
            console.print("[red]Invalid path format. Use alphanumeric characters and dots only.[/red]")
            continue
        break
    
    # Prompt for description
    description = Prompt.ask("Description")
    
    # Prompt for type
    type_choices = ["string", "number", "boolean", "array", "object"]
    console.print("\nType options: " + ", ".join(type_choices))
    while True:
        value_type = Prompt.ask("Type", default="string").lower()
        if value_type in type_choices:
            break
        console.print(f"[red]Invalid type. Choose from: {', '.join(type_choices)}[/red]")
    
    # Prompt for required
    required = Confirm.ask("Required?", default=True)
    
    # Prompt for default value
    default = None
    if Confirm.ask("Set default value?", default=False):
        while True:
            default_str = Prompt.ask(f"Default value ({value_type})")
            try:
                default = parse_value_by_type(default_str, value_type)
                break
            except typer.BadParameter as e:
                console.print(f"[red]{e}[/red]")
    
    # Prompt for sensitive
    sensitive = Confirm.ask("Sensitive value?", default=False)
    
    # Create and add the new value
    new_value = SchemaValue(
        key=key,
        path=path,
        description=description,
        type=value_type,
        required=required,
        default=default,
        sensitive=sensitive,
    )
    
    schema.values.append(new_value)
    
    # Save the updated schema
    save_schema(schema, schema_path)
    
    console.print(f"\n[green]✓[/green] Added '{key}' to schema")
    console.print(f"  Path: {path}")
    console.print(f"  Type: {value_type}")
    console.print(f"  Required: {required}")
    if default is not None:
        console.print(f"  Default: {default}")
    console.print(f"  Sensitive: {sensitive}")


@app.command("list")
def list_command(
    schema_path: str = typer.Option("schema.json", "--schema", help="Path to schema file"),
):
    """List all values in the schema."""
    schema = load_schema(schema_path)
    if not schema:
        console.print("[red]Error:[/red] No schema.json found. Run 'init' first.")
        raise typer.Exit(1)
    
    if not schema.values:
        console.print("No values defined in schema.")
        return
    
    console.print("[bold]Schema Values:[/bold]\n")
    
    for value in schema.values:
        status = "[green]●[/green]" if value.required else "[yellow]○[/yellow]"
        sensitive = " 🔒" if value.sensitive else ""
        console.print(f"{status} [bold]{value.key}[/bold]{sensitive}")
        console.print(f"  Path: {value.path}")
        console.print(f"  Type: {value.type}")
        console.print(f"  Description: {value.description}")
        if value.default is not None:
            console.print(f"  Default: {value.default}")
        console.print()


@app.command("get")
def get_command(
    key: str = typer.Argument(..., help="Key of the value to show"),
    schema_path: str = typer.Option("schema.json", "--schema", help="Path to schema file"),
):
    """Show details of a specific schema value."""
    schema = load_schema(schema_path)
    if not schema:
        console.print("[red]Error:[/red] No schema.json found. Run 'init' first.")
        raise typer.Exit(1)
    
    # Find the value
    value = next((v for v in schema.values if v.key == key), None)
    if not value:
        console.print(f"[red]Error:[/red] Value with key '{key}' not found")
        raise typer.Exit(1)
    
    # Display details
    console.print(f"\n[bold]{value.key}[/bold]")
    console.print(f"Path: {value.path}")
    console.print(f"Type: {value.type}")
    console.print(f"Description: {value.description}")
    console.print(f"Required: {value.required}")
    if value.default is not None:
        console.print(f"Default: {json.dumps(value.default, indent=2) if value.type in ['array', 'object'] else value.default}")
    console.print(f"Sensitive: {value.sensitive}")


@app.command("update")
def update_command(
    key: str = typer.Argument(..., help="Key of the value to update"),
    schema_path: str = typer.Option("schema.json", "--schema", help="Path to schema file"),
):
    """Update an existing schema value."""
    schema = load_schema(schema_path)
    if not schema:
        console.print("[red]Error:[/red] No schema.json found. Run 'init' first.")
        raise typer.Exit(1)
    
    # Find the value
    value_index = next((i for i, v in enumerate(schema.values) if v.key == key), None)
    if value_index is None:
        console.print(f"[red]Error:[/red] Value with key '{key}' not found")
        raise typer.Exit(1)
    
    value = schema.values[value_index]
    console.print(f"[bold]Updating '{key}'[/bold]\n")
    console.print("Press Enter to keep current value\n")
    
    # Update path
    new_path = Prompt.ask(f"Path [{value.path}]", default=value.path)
    if new_path != value.path:
        while not validate_path_format(new_path):
            console.print("[red]Invalid path format. Use alphanumeric characters and dots only.[/red]")
            new_path = Prompt.ask(f"Path [{value.path}]", default=value.path)
        value.path = new_path
    
    # Update description
    new_description = Prompt.ask(f"Description [{value.description}]", default=value.description)
    value.description = new_description
    
    # Update type
    type_choices = ["string", "number", "boolean", "array", "object"]
    console.print(f"\nType options: {', '.join(type_choices)}")
    new_type = Prompt.ask(f"Type [{value.type}]", default=value.type).lower()
    if new_type != value.type:
        while new_type not in type_choices:
            console.print(f"[red]Invalid type. Choose from: {', '.join(type_choices)}[/red]")
            new_type = Prompt.ask(f"Type [{value.type}]", default=value.type).lower()
        value.type = new_type
        # Clear default if type changed
        if value.default is not None:
            if Confirm.ask("Type changed. Clear default value?", default=True):
                value.default = None
    
    # Update required
    value.required = Confirm.ask("Required?", default=value.required)
    
    # Update default
    if value.default is None:
        if Confirm.ask("Set default value?", default=False):
            while True:
                default_str = Prompt.ask(f"Default value ({value.type})")
                try:
                    value.default = parse_value_by_type(default_str, value.type)
                    break
                except typer.BadParameter as e:
                    console.print(f"[red]{e}[/red]")
    else:
        default_display = json.dumps(value.default) if value.type in ['array', 'object'] else str(value.default)
        if Confirm.ask(f"Update default value? [current: {default_display}]", default=False):
            while True:
                default_str = Prompt.ask(f"Default value ({value.type})")
                try:
                    value.default = parse_value_by_type(default_str, value.type)
                    break
                except typer.BadParameter as e:
                    console.print(f"[red]{e}[/red]")
    
    # Update sensitive
    value.sensitive = Confirm.ask("Sensitive value?", default=value.sensitive)
    
    # Save the updated schema
    save_schema(schema, schema_path)
    
    console.print(f"\n[green]✓[/green] Updated '{key}' in schema")


@app.command("remove")
def remove_command(
    key: str = typer.Argument(..., help="Key of the value to remove"),
    schema_path: str = typer.Option("schema.json", "--schema", help="Path to schema file"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Remove a value from the schema."""
    schema = load_schema(schema_path)
    if not schema:
        console.print("[red]Error:[/red] No schema.json found. Run 'init' first.")
        raise typer.Exit(1)
    
    # Find the value
    value_index = next((i for i, v in enumerate(schema.values) if v.key == key), None)
    if value_index is None:
        console.print(f"[red]Error:[/red] Value with key '{key}' not found")
        raise typer.Exit(1)
    
    value = schema.values[value_index]
    
    # Confirm removal
    if not force:
        console.print(f"\n[bold]Value to remove:[/bold]")
        console.print(f"Key: {value.key}")
        console.print(f"Path: {value.path}")
        console.print(f"Description: {value.description}")
        
        if not Confirm.ask("\nRemove this value?", default=False):
            console.print("Cancelled")
            raise typer.Exit(0)
    
    # Remove the value
    schema.values.pop(value_index)
    
    # Save the updated schema
    save_schema(schema, schema_path)
    
    console.print(f"\n[green]✓[/green] Removed '{key}' from schema")