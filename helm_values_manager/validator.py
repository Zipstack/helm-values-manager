"""Validation module for helm-values-manager."""

import json
import os
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.text import Text

from helm_values_manager.models import Schema, SchemaValue

console = Console()


class ErrorMessage(Text):
    """Error message styled text."""

    def __init__(self, text: str):
        super().__init__(text, style="bold red")


class WarningMessage(Text):
    """Warning message styled text."""

    def __init__(self, text: str):
        super().__init__(text, style="bold yellow")


class ValidationError:
    """Represents a single validation error."""

    def __init__(self, context: str, message: str, env: Optional[str] = None):
        self.context = context
        self.message = message
        self.env = env

    def __str__(self):
        if self.env:
            return f"\\[{self.env}] {self.context}: {self.message}"
        return f"{self.context}: {self.message}"


class Validator:
    """Validates schema and values files."""

    def __init__(self, schema_path: Path, values_base_path: Optional[Path] = None):
        self.schema_path = schema_path
        self.values_base_path = values_base_path or Path(".")
        self.errors: list[ValidationError] = []

    def validate_all(self, env: Optional[str] = None) -> bool:
        """Validate schema and optionally values for specific environment."""
        self.errors = []

        # Validate schema
        self._validate_schema()

        # Validate values
        if env:
            self._validate_values_for_env(env)
        else:
            # Validate all environments
            self._validate_all_values()

        return len(self.errors) == 0

    def _validate_schema(self):
        """Validate schema structure and integrity."""
        try:
            if not self.schema_path.exists():
                self.errors.append(ValidationError("Schema", f"File not found: {self.schema_path}"))
                return

            with open(self.schema_path) as f:
                data = json.load(f)

            schema = Schema(**data)
        except json.JSONDecodeError as e:
            self.errors.append(ValidationError("Schema", f"Invalid JSON: {e}"))
            return
        except Exception as e:
            self.errors.append(ValidationError("Schema", f"Invalid schema: {e}"))
            return

        # Check schema version
        if schema.version != "1.0":
            self.errors.append(ValidationError("Schema", f"Unsupported version: {schema.version}"))

        # Validate each entry
        seen_keys: set[str] = set()
        seen_paths: set[str] = set()

        for entry in schema.values:
            # Check for duplicate keys
            if entry.key in seen_keys:
                self.errors.append(ValidationError("Schema", f"Duplicate key: {entry.key}"))
            seen_keys.add(entry.key)

            # Check for duplicate paths
            if entry.path in seen_paths:
                self.errors.append(ValidationError("Schema", f"Duplicate path: {entry.path}"))
            seen_paths.add(entry.path)

            # Validate path format (alphanumeric + dots)
            if not all(c.isalnum() or c in ".-_" for c in entry.path):
                self.errors.append(ValidationError("Schema", f"Invalid path format: {entry.path}"))

            # Validate type
            valid_types = ["string", "number", "boolean", "array", "object"]
            if entry.type not in valid_types:
                self.errors.append(
                    ValidationError("Schema", f"Invalid type for {entry.key}: {entry.type}")
                )

            # Validate default value type if present
            if entry.default is not None:
                if not self._validate_value_type(entry.default, entry.type):
                    self.errors.append(
                        ValidationError("Schema", f"Default value type mismatch for {entry.key}")
                    )

    def _validate_values_for_env(self, env: str, values_file_path: Optional[str] = None):
        """Validate values for a specific environment."""
        if values_file_path:
            values_file = Path(values_file_path)
        else:
            values_file = self.values_base_path / f"values-{env}.json"

        if not values_file.exists():
            # Not an error if no values file exists
            return

        try:
            with open(values_file) as f:
                env_values = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(
                ValidationError("Values", f"Invalid JSON in {values_file}: {e}", env)
            )
            return

        # Load schema
        try:
            if not self.schema_path.exists():
                return

            with open(self.schema_path) as f:
                data = json.load(f)

            schema = Schema(**data)
        except Exception:
            # Schema errors already reported
            return

        # Create lookup maps
        schema_map = {entry.key: entry for entry in schema.values}

        # Check each value in the file
        for key, value in env_values.items():
            if key not in schema_map:
                self.errors.append(ValidationError("Values", f"Unknown key: {key}", env))
                continue

            entry = schema_map[key]

            # Validate based on whether it's a secret
            if entry.sensitive:
                if not self._validate_secret_structure(value):
                    self.errors.append(
                        ValidationError("Values", f"Invalid secret structure for {key}", env)
                    )
                else:
                    # Validate environment variable exists
                    if isinstance(value, dict) and value.get("type") == "env":
                        env_var = value.get("name", "")
                        if env_var and not os.environ.get(env_var):
                            # This is a warning, not an error
                            console.print(
                                WarningMessage(
                                    f"Environment variable not found: {env_var} (key: {key}, env: {env})"
                                )
                            )
            else:
                # Validate value type
                if not self._validate_value_type(value, entry.type):
                    self.errors.append(
                        ValidationError(
                            "Values", f"Type mismatch for {key}: expected {entry.type}", env
                        )
                    )

        # Check for missing required values
        for entry in schema.values:
            if entry.required and entry.key not in env_values and entry.default is None:
                self.errors.append(
                    ValidationError("Values", f"Missing required value: {entry.key}", env)
                )

    def _validate_all_values(self):
        """Validate values for all environments found."""
        # Find all values files
        pattern = "values-*.json"
        for values_file in self.values_base_path.glob(pattern):
            # Extract environment from filename
            env = values_file.stem.replace("values-", "")
            # Debug: print(f"Validating environment: {env}")
            self._validate_values_for_env(env)

    def _validate_value_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        return False

    def _validate_secret_structure(self, value: Any) -> bool:
        """Validate secret value structure."""
        if not isinstance(value, dict):
            return False

        if "type" not in value:
            return False

        # Currently only support 'env' type
        if value["type"] == "env":
            return "name" in value and isinstance(value["name"], str)

        # Unknown type
        self.errors.append(ValidationError("Values", f"Unsupported secret type: {value['type']}"))
        return False

    def print_errors(self):
        """Print all validation errors."""
        if not self.errors:
            return

        console.print(ErrorMessage("Validation failed:"))
        for error in self.errors:
            # Debug: print(f"DEBUG: error.env={error.env}, error={error}")
            console.print(f"  - {str(error)}")


def validate_single_environment(schema: Schema, values: dict[str, Any], env: str) -> list[str]:
    """Validate schema and values for a single environment and return list of errors.

    Args:
        schema: The loaded schema object
        values: The loaded values dictionary
        env: Environment name (for error messages)

    Returns:
        List of error messages (empty if validation passed)
    """
    errors = []

    # Validate schema first
    schema_errors = _validate_schema_integrity(schema)
    errors.extend(schema_errors)

    # Check for required values
    for schema_value in schema.values:
        if schema_value.required and schema_value.key not in values:
            # Check if there's a default value
            if schema_value.default is None:
                errors.append(f"[{env}] Values: Missing required value: {schema_value.key}")

    # Validate each value
    for key, value in values.items():
        # Find corresponding schema value
        schema_value = next((sv for sv in schema.values if sv.key == key), None)

        if not schema_value:
            errors.append(f"[{env}] Values: Unknown key: {key}")
            continue

        # Check type
        if not _is_valid_type(value, schema_value):
            errors.append(f"[{env}] Values: Type mismatch for {key}: expected {schema_value.type}")
            continue

        # Validate secrets
        if schema_value.sensitive and not isinstance(value, dict):
            errors.append(
                f"[{env}] Values: Invalid secret structure for {key}: expected object with 'type' and 'name'"
            )
        elif isinstance(value, dict) and "type" in value:
            # It's a secret reference
            if not _is_valid_secret_reference(value):
                errors.append(f"[{env}] Values: Invalid secret structure for {key}")
            elif value["type"] != "env":
                errors.append(
                    f"[{env}] Values: Unsupported secret type '{value['type']}' for {key}"
                )

    return errors


def _validate_schema_integrity(schema: Schema) -> list[str]:
    """Validate schema for duplicate keys and paths."""
    errors = []

    # Check for duplicate keys
    seen_keys = set()
    for schema_value in schema.values:
        if schema_value.key in seen_keys:
            errors.append(f"Schema: Duplicate key: {schema_value.key}")
        seen_keys.add(schema_value.key)

    # Check for duplicate paths
    seen_paths = set()
    for schema_value in schema.values:
        if schema_value.path in seen_paths:
            errors.append(f"Schema: Duplicate path: {schema_value.path}")
        seen_paths.add(schema_value.path)

    return errors


def _is_valid_type(value: Any, schema_value: SchemaValue) -> bool:
    """Check if value matches expected type."""
    # If it's a secret reference, type check doesn't apply
    if isinstance(value, dict) and "type" in value and "name" in value:
        return True

    if schema_value.type == "string":
        return isinstance(value, str)
    elif schema_value.type == "number":
        return isinstance(value, (int, float))
    elif schema_value.type == "boolean":
        return isinstance(value, bool)
    elif schema_value.type == "array":
        return isinstance(value, list)
    elif schema_value.type == "object":
        return isinstance(value, dict)

    return False


def _is_valid_secret_reference(value: Any) -> bool:
    """Check if value is a valid secret reference."""
    if not isinstance(value, dict):
        return False

    if "type" not in value or "name" not in value:
        return False

    return isinstance(value["type"], str) and isinstance(value["name"], str)


def validate_command(
    schema_path: Path, values_base_path: Optional[Path] = None, env: Optional[str] = None
) -> bool:
    """Run validation and report results."""
    validator = Validator(schema_path, values_base_path)

    if validator.validate_all(env):
        if env:
            console.print(f"✅ Validation passed for environment: {env}")
        else:
            console.print("✅ All validations passed")
        return True
    else:
        validator.print_errors()
        return False
