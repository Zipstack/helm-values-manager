"""Generator module for creating values.yaml from schema and values."""

import os
from typing import Any

import yaml

from helm_values_manager.errors import GeneratorError
from helm_values_manager.models import Schema
from helm_values_manager.utils import is_secret_reference


def resolve_secret(secret: dict[str, Any], key: str) -> str:
    """Resolve a secret reference to its actual value.

    Args:
        secret: Secret reference with type and name
        key: The key name (for error messages)

    Returns:
        The resolved secret value

    Raises:
        GeneratorError: If secret cannot be resolved
    """
    if secret.get("type") != "env":
        raise GeneratorError(f"Unsupported secret type '{secret.get('type')}' for key '{key}'")

    env_var = secret.get("name")
    if not env_var:
        raise GeneratorError(f"Missing environment variable name for secret '{key}'")

    value = os.environ.get(env_var)
    if value is None:
        raise GeneratorError(f"Environment variable '{env_var}' not found for secret '{key}'")

    return value


def build_nested_dict(flat_values: dict[str, Any], schema: Schema) -> dict[str, Any]:
    """Build a nested dictionary from flat values using schema paths.

    Args:
        flat_values: Flat dictionary with keys and values
        schema: Schema containing path information

    Returns:
        Nested dictionary following YAML structure
    """
    result = {}

    # Create a mapping of keys to schema values for easy lookup
    key_to_schema = {sv.key: sv for sv in schema.values}

    for key, value in flat_values.items():
        schema_value = key_to_schema.get(key)
        if not schema_value:
            # Skip unknown keys (validation should catch this)
            continue

        # Split the path into parts
        path_parts = schema_value.path.split(".")

        # Navigate/create the nested structure
        current = result
        for i, part in enumerate(path_parts[:-1]):
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                # Path conflict - this shouldn't happen with valid schema
                raise GeneratorError(
                    f"Path conflict at '{'.'.join(path_parts[: i + 1])}' for key '{key}'"
                )
            current = current[part]

        # Set the final value
        final_key = path_parts[-1]
        current[final_key] = value

    return result


def generate_values(schema: Schema, values: dict[str, Any], env: str) -> str:
    """Generate values.yaml content from schema and environment values.

    Args:
        schema: The schema definition
        values: The environment-specific values
        env: Environment name (for error messages)

    Returns:
        YAML content as string

    Raises:
        GeneratorError: If generation fails
    """
    # Start with defaults from schema
    merged_values = {}

    for schema_value in schema.values:
        if schema_value.default is not None:
            merged_values[schema_value.key] = schema_value.default

    # Override with environment values and resolve secrets
    for key, value in values.items():
        if is_secret_reference(value):
            try:
                merged_values[key] = resolve_secret(value, key)
            except GeneratorError as e:
                raise GeneratorError(f"[{env}] {e}")
        else:
            merged_values[key] = value

    # Build nested structure
    nested_values = build_nested_dict(merged_values, schema)

    # Convert to YAML
    yaml_content = yaml.dump(
        nested_values,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=1000,  # Avoid line wrapping for long strings
    )

    return yaml_content
