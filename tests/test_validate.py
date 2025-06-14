"""Tests for the validate command."""
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from helm_values_manager.cli import app

runner = CliRunner()


def test_validate_missing_schema(tmp_path):
    """Test validation with missing schema file."""
    result = runner.invoke(app, ["validate", "--schema", str(tmp_path / "missing.json")])
    assert result.exit_code == 1
    assert "File not found" in result.stdout


def test_validate_invalid_schema_json(tmp_path):
    """Test validation with invalid JSON in schema."""
    schema_file = tmp_path / "schema.json"
    schema_file.write_text("invalid json")
    
    result = runner.invoke(app, ["validate", "--schema", str(schema_file)])
    assert result.exit_code == 1
    assert "Invalid JSON" in result.stdout


def test_validate_valid_schema_only(tmp_path):
    """Test validation with valid schema and no values files."""
    schema_file = tmp_path / "schema.json"
    schema_data = {
        "version": "1.0",
        "values": [
            {
                "key": "app-name",
                "path": "app.name",
                "description": "Application name",
                "type": "string",
                "required": True,
                "default": "myapp"
            }
        ]
    }
    schema_file.write_text(json.dumps(schema_data, indent=2))
    
    result = runner.invoke(app, ["validate", "--schema", str(schema_file)])
    assert result.exit_code == 0
    assert "All validations passed" in result.stdout


def test_validate_duplicate_keys(tmp_path):
    """Test validation with duplicate keys in schema."""
    schema_file = tmp_path / "schema.json"
    schema_data = {
        "version": "1.0",
        "values": [
            {
                "key": "database",
                "path": "db.host",
                "description": "Database host",
                "type": "string",
                "required": True
            },
            {
                "key": "database",  # Duplicate key
                "path": "db.port",
                "description": "Database port",
                "type": "number",
                "required": True
            }
        ]
    }
    schema_file.write_text(json.dumps(schema_data, indent=2))
    
    result = runner.invoke(app, ["validate", "--schema", str(schema_file)])
    assert result.exit_code == 1
    assert "Duplicate key: database" in result.stdout


def test_validate_duplicate_paths(tmp_path):
    """Test validation with duplicate paths in schema."""
    schema_file = tmp_path / "schema.json"
    schema_data = {
        "version": "1.0",
        "values": [
            {
                "key": "db-host",
                "path": "database.host",
                "description": "Database host",
                "type": "string",
                "required": True
            },
            {
                "key": "db-hostname",
                "path": "database.host",  # Duplicate path
                "description": "Database hostname",
                "type": "string",
                "required": True
            }
        ]
    }
    schema_file.write_text(json.dumps(schema_data, indent=2))
    
    result = runner.invoke(app, ["validate", "--schema", str(schema_file)])
    assert result.exit_code == 1
    assert "Duplicate path: database.host" in result.stdout


def test_validate_invalid_type(tmp_path):
    """Test validation with invalid type in schema."""
    schema_file = tmp_path / "schema.json"
    schema_data = {
        "version": "1.0",
        "values": [
            {
                "key": "config",
                "path": "app.config",
                "description": "App config",
                "type": "invalid-type",
                "required": True
            }
        ]
    }
    schema_file.write_text(json.dumps(schema_data, indent=2))
    
    result = runner.invoke(app, ["validate", "--schema", str(schema_file)])
    assert result.exit_code == 1
    assert ("Invalid schema" in result.stdout or "Invalid type" in result.stdout)


def test_validate_values_type_mismatch(tmp_path):
    """Test validation with type mismatch in values."""
    # Create schema
    schema_file = tmp_path / "schema.json"
    schema_data = {
        "version": "1.0",
        "values": [
            {
                "key": "port",
                "path": "app.port",
                "description": "Application port",
                "type": "number",
                "required": True
            }
        ]
    }
    schema_file.write_text(json.dumps(schema_data, indent=2))
    
    # Create values with wrong type
    values_file = tmp_path / "values-dev.json"
    values_data = {
        "dev": {
            "port": "8080"  # String instead of number
        }
    }
    values_file.write_text(json.dumps(values_data, indent=2))
    
    result = runner.invoke(app, [
        "validate",
        "--schema", str(schema_file),
        "--values", str(tmp_path),
        "--env", "dev"
    ])
    assert result.exit_code == 1
    assert "Type mismatch for port" in result.stdout


def test_validate_missing_required_value(tmp_path):
    """Test validation with missing required value."""
    # Create schema
    schema_file = tmp_path / "schema.json"
    schema_data = {
        "version": "1.0",
        "values": [
            {
                "key": "database-host",
                "path": "db.host",
                "description": "Database host",
                "type": "string",
                "required": True
            }
        ]
    }
    schema_file.write_text(json.dumps(schema_data, indent=2))
    
    # Create empty values file
    values_file = tmp_path / "values-prod.json"
    values_data = {"prod": {}}
    values_file.write_text(json.dumps(values_data, indent=2))
    
    result = runner.invoke(app, [
        "validate",
        "--schema", str(schema_file),
        "--values", str(tmp_path),
        "--env", "prod"
    ])
    assert result.exit_code == 1
    assert "Missing required value: database-host" in result.stdout


def test_validate_secret_structure(tmp_path):
    """Test validation of secret structure."""
    # Create schema
    schema_file = tmp_path / "schema.json"
    schema_data = {
        "version": "1.0",
        "values": [
            {
                "key": "api-key",
                "path": "api.key",
                "description": "API key",
                "type": "string",
                "required": True,
                "sensitive": True
            }
        ]
    }
    schema_file.write_text(json.dumps(schema_data, indent=2))
    
    # Create values with invalid secret structure
    values_file = tmp_path / "values-dev.json"
    values_data = {
        "dev": {
            "api-key": "plain-text-secret"  # Should be object with type and name
        }
    }
    values_file.write_text(json.dumps(values_data, indent=2))
    
    result = runner.invoke(app, [
        "validate",
        "--schema", str(schema_file),
        "--values", str(tmp_path),
        "--env", "dev"
    ])
    assert result.exit_code == 1
    assert "Invalid secret structure for api-key" in result.stdout


def test_validate_valid_secret(tmp_path, monkeypatch):
    """Test validation with valid secret structure."""
    # Set environment variable
    monkeypatch.setenv("API_KEY", "test-key")
    
    # Create schema
    schema_file = tmp_path / "schema.json"
    schema_data = {
        "version": "1.0",
        "values": [
            {
                "key": "api-key",
                "path": "api.key",
                "description": "API key",
                "type": "string",
                "required": True,
                "sensitive": True
            }
        ]
    }
    schema_file.write_text(json.dumps(schema_data, indent=2))
    
    # Create values with valid secret
    values_file = tmp_path / "values-dev.json"
    values_data = {
        "dev": {
            "api-key": {
                "type": "env",
                "name": "API_KEY"
            }
        }
    }
    values_file.write_text(json.dumps(values_data, indent=2))
    
    result = runner.invoke(app, [
        "validate",
        "--schema", str(schema_file),
        "--values", str(tmp_path),
        "--env", "dev"
    ])
    assert result.exit_code == 0
    assert "Validation passed for environment: dev" in result.stdout


def test_validate_all_environments(tmp_path):
    """Test validation of all environments."""
    # Create schema
    schema_file = tmp_path / "schema.json"
    schema_data = {
        "version": "1.0",
        "values": [
            {
                "key": "replicas",
                "path": "deployment.replicas",
                "description": "Number of replicas",
                "type": "number",
                "required": True
            }
        ]
    }
    schema_file.write_text(json.dumps(schema_data, indent=2))
    
    # Create values for multiple environments
    values_dev = tmp_path / "values-dev.json"
    values_dev.write_text(json.dumps({"dev": {"replicas": 1}}))
    
    values_prod = tmp_path / "values-prod.json"
    values_prod.write_text(json.dumps({"prod": {"replicas": 3}}))
    
    result = runner.invoke(app, [
        "validate",
        "--schema", str(schema_file),
        "--values", str(tmp_path)
    ])
    assert result.exit_code == 0
    assert "All validations passed" in result.stdout


def test_validate_unknown_key_in_values(tmp_path):
    """Test validation with unknown key in values."""
    # Create schema
    schema_file = tmp_path / "schema.json"
    schema_data = {
        "version": "1.0",
        "values": []
    }
    schema_file.write_text(json.dumps(schema_data, indent=2))
    
    # Create values with unknown key
    values_file = tmp_path / "values-dev.json"
    values_data = {
        "dev": {
            "unknown-key": "value"
        }
    }
    values_file.write_text(json.dumps(values_data, indent=2))
    
    result = runner.invoke(app, [
        "validate",
        "--schema", str(schema_file),
        "--values", str(tmp_path),
        "--env", "dev"
    ])
    assert result.exit_code == 1
    assert "Unknown key: unknown-key" in result.stdout


def test_validate_multi_env_shows_environment_names(tmp_path):
    """Test that validation errors show which environment has issues."""
    # Create schema
    schema_file = tmp_path / "schema.json"
    schema_data = {
        "version": "1.0",
        "values": [
            {
                "key": "database-host",
                "path": "db.host",
                "description": "Database hostname",
                "type": "string",
                "required": True
            }
        ]
    }
    schema_file.write_text(json.dumps(schema_data, indent=2))
    
    # Create values for multiple environments with different errors
    values_dev = tmp_path / "values-dev.json"
    values_dev.write_text(json.dumps({
        "dev": {}  # Missing required value
    }))
    
    values_staging = tmp_path / "values-staging.json"
    values_staging.write_text(json.dumps({
        "staging": {
            "database-host": 123  # Wrong type
        }
    }))
    
    values_prod = tmp_path / "values-prod.json"
    values_prod.write_text(json.dumps({
        "prod": {
            "database-host": "prod-db.example.com"  # Correct
        }
    }))
    
    # Validate all environments
    result = runner.invoke(app, [
        "validate",
        "--schema", str(schema_file),
        "--values", str(tmp_path)
    ])
    
    assert result.exit_code == 1
    assert "[dev] Values: Missing required value: database-host" in result.stdout
    assert "[staging] Values: Type mismatch for database-host: expected string" in result.stdout
    # prod should not appear in errors since it's correct
    assert "[prod]" not in result.stdout