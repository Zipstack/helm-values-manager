"""Tests for the generator module."""

import json

import pytest
import yaml
from typer.testing import CliRunner

from helm_values_manager.cli import app
from helm_values_manager.generator import (
    GeneratorError,
    build_nested_dict,
    generate_values,
    resolve_secret,
)
from helm_values_manager.models import Schema, SchemaValue

runner = CliRunner()


def test_resolve_secret_env_var(monkeypatch):
    """Test resolving environment variable secrets."""
    monkeypatch.setenv("TEST_SECRET", "secret-value")

    secret = {"type": "env", "name": "TEST_SECRET"}
    result = resolve_secret(secret, "test-key")

    assert result == "secret-value"


def test_resolve_secret_missing_env_var():
    """Test error when environment variable is missing."""
    secret = {"type": "env", "name": "NONEXISTENT_VAR"}

    with pytest.raises(GeneratorError) as exc_info:
        resolve_secret(secret, "test-key")

    assert "Environment variable 'NONEXISTENT_VAR' not found" in str(exc_info.value)


def test_resolve_secret_unsupported_type():
    """Test error for unsupported secret types."""
    secret = {"type": "vault", "name": "secret/path"}

    with pytest.raises(GeneratorError) as exc_info:
        resolve_secret(secret, "test-key")

    assert "Unsupported secret type 'vault'" in str(exc_info.value)


def test_build_nested_dict_simple():
    """Test building nested dict with simple paths."""
    schema = Schema(
        version="1.0",
        values=[
            SchemaValue(
                key="host", path="database.host", description="", type="string", required=True
            ),
            SchemaValue(
                key="port", path="database.port", description="", type="number", required=True
            ),
            SchemaValue(key="name", path="app.name", description="", type="string", required=True),
        ],
    )

    flat_values = {"host": "localhost", "port": 5432, "name": "myapp"}

    result = build_nested_dict(flat_values, schema)

    assert result == {"database": {"host": "localhost", "port": 5432}, "app": {"name": "myapp"}}


def test_build_nested_dict_deep_paths():
    """Test building nested dict with deep paths."""
    schema = Schema(
        version="1.0",
        values=[
            SchemaValue(
                key="cpu",
                path="resources.requests.cpu",
                description="",
                type="string",
                required=True,
            ),
            SchemaValue(
                key="memory",
                path="resources.requests.memory",
                description="",
                type="string",
                required=True,
            ),
        ],
    )

    flat_values = {"cpu": "100m", "memory": "256Mi"}

    result = build_nested_dict(flat_values, schema)

    assert result == {"resources": {"requests": {"cpu": "100m", "memory": "256Mi"}}}


def test_generate_values_with_defaults():
    """Test generating values with schema defaults."""
    schema = Schema(
        version="1.0",
        values=[
            SchemaValue(
                key="replicas",
                path="deployment.replicas",
                description="",
                type="number",
                required=False,
                default=3,
            ),
            SchemaValue(
                key="port", path="service.port", description="", type="number", required=True
            ),
        ],
    )

    values = {"port": 8080}

    yaml_str = generate_values(schema, values, "test")
    result = yaml.safe_load(yaml_str)

    assert result == {
        "deployment": {
            "replicas": 3  # From default
        },
        "service": {
            "port": 8080  # From values
        },
    }


def test_generate_values_override_defaults():
    """Test that environment values override defaults."""
    schema = Schema(
        version="1.0",
        values=[
            SchemaValue(
                key="replicas",
                path="deployment.replicas",
                description="",
                type="number",
                required=False,
                default=3,
            ),
        ],
    )

    values = {"replicas": 5}

    yaml_str = generate_values(schema, values, "test")
    result = yaml.safe_load(yaml_str)

    assert result == {
        "deployment": {
            "replicas": 5  # Override default
        }
    }


def test_generate_values_with_secrets(monkeypatch):
    """Test generating values with secret resolution."""
    monkeypatch.setenv("DB_PASSWORD", "super-secret")

    schema = Schema(
        version="1.0",
        values=[
            SchemaValue(
                key="password",
                path="database.password",
                description="",
                type="string",
                required=True,
                sensitive=True,
            ),
        ],
    )

    values = {"password": {"type": "env", "name": "DB_PASSWORD"}}

    yaml_str = generate_values(schema, values, "test")
    result = yaml.safe_load(yaml_str)

    assert result == {"database": {"password": "super-secret"}}


def test_generate_values_arrays_and_objects():
    """Test generating values with complex types."""
    schema = Schema(
        version="1.0",
        values=[
            SchemaValue(
                key="hosts", path="ingress.hosts", description="", type="array", required=True
            ),
            SchemaValue(
                key="annotations",
                path="ingress.annotations",
                description="",
                type="object",
                required=True,
            ),
        ],
    )

    values = {
        "hosts": ["example.com", "www.example.com"],
        "annotations": {
            "nginx.ingress.kubernetes.io/rewrite-target": "/",
            "cert-manager.io/cluster-issuer": "letsencrypt",
        },
    }

    yaml_str = generate_values(schema, values, "test")
    result = yaml.safe_load(yaml_str)

    assert result == {
        "ingress": {
            "hosts": ["example.com", "www.example.com"],
            "annotations": {
                "nginx.ingress.kubernetes.io/rewrite-target": "/",
                "cert-manager.io/cluster-issuer": "letsencrypt",
            },
        }
    }


def test_generate_command_success(tmp_path, monkeypatch):
    """Test successful generate command execution."""
    monkeypatch.setenv("API_KEY", "test-api-key")

    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create schema
        schema_data = {
            "version": "1.0",
            "values": [
                {
                    "key": "name",
                    "path": "app.name",
                    "description": "App name",
                    "type": "string",
                    "required": True,
                    "default": "myapp",
                },
                {
                    "key": "replicas",
                    "path": "app.replicas",
                    "description": "Number of replicas",
                    "type": "number",
                    "required": True,
                },
                {
                    "key": "api-key",
                    "path": "app.apiKey",
                    "description": "API key",
                    "type": "string",
                    "required": True,
                    "sensitive": True,
                },
            ],
        }
        with open("schema.json", "w") as f:
            json.dump(schema_data, f)

        # Create values (flat structure)
        values_data = {"replicas": 2, "api-key": {"type": "env", "name": "API_KEY"}}
        with open("values-dev.json", "w") as f:
            json.dump(values_data, f)

        # Run generate command
        result = runner.invoke(app, ["generate", "--env", "dev"])

        assert result.exit_code == 0

        # Parse the output YAML
        output_yaml = yaml.safe_load(result.stdout)
        assert output_yaml == {
            "app": {
                "name": "myapp",  # From default
                "replicas": 2,  # From values
                "apiKey": "test-api-key",  # Resolved secret
            }
        }


def test_generate_command_validation_fails(tmp_path):
    """Test generate command fails when validation fails."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create schema with required field
        schema_data = {
            "version": "1.0",
            "values": [
                {
                    "key": "required-field",
                    "path": "app.required",
                    "description": "Required field",
                    "type": "string",
                    "required": True,
                }
            ],
        }
        with open("schema.json", "w") as f:
            json.dump(schema_data, f)

        # Create empty values (flat structure)
        with open("values-dev.json", "w") as f:
            json.dump({}, f)

        # Run generate command
        result = runner.invoke(app, ["generate", "--env", "dev"])

        assert result.exit_code == 1
        assert "Validation failed" in result.output
        assert "Missing required value: required-field" in result.output


def test_generate_command_missing_env_var(tmp_path):
    """Test generate command fails when env var is missing."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create schema
        schema_data = {
            "version": "1.0",
            "values": [
                {
                    "key": "secret",
                    "path": "app.secret",
                    "description": "Secret value",
                    "type": "string",
                    "required": True,
                    "sensitive": True,
                }
            ],
        }
        with open("schema.json", "w") as f:
            json.dump(schema_data, f)

        # Create values with env var reference (flat structure)
        values_data = {"secret": {"type": "env", "name": "MISSING_VAR"}}
        with open("values-prod.json", "w") as f:
            json.dump(values_data, f)

        # Run generate command
        result = runner.invoke(app, ["generate", "--env", "prod"])

        assert result.exit_code == 1
        assert "Environment variable 'MISSING_VAR' not found" in result.output


def test_generate_command_complex_example(tmp_path, monkeypatch):
    """Test generate command with a complex real-world example."""
    # Set up environment variables
    monkeypatch.setenv("DB_PASSWORD", "postgres123")
    monkeypatch.setenv("REDIS_PASSWORD", "redis456")

    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create complex schema
        schema_data = {
            "version": "1.0",
            "values": [
                {
                    "key": "app-name",
                    "path": "global.appName",
                    "description": "Application name",
                    "type": "string",
                    "required": True,
                    "default": "web-service",
                },
                {
                    "key": "image-tag",
                    "path": "image.tag",
                    "description": "Docker image tag",
                    "type": "string",
                    "required": True,
                },
                {
                    "key": "db-host",
                    "path": "postgresql.host",
                    "description": "Database host",
                    "type": "string",
                    "required": True,
                },
                {
                    "key": "db-password",
                    "path": "postgresql.auth.password",
                    "description": "Database password",
                    "type": "string",
                    "required": True,
                    "sensitive": True,
                },
                {
                    "key": "redis-enabled",
                    "path": "redis.enabled",
                    "description": "Enable Redis",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                },
                {
                    "key": "redis-password",
                    "path": "redis.auth.password",
                    "description": "Redis password",
                    "type": "string",
                    "required": False,
                    "sensitive": True,
                },
                {
                    "key": "ingress-hosts",
                    "path": "ingress.hosts",
                    "description": "Ingress hostnames",
                    "type": "array",
                    "required": True,
                },
                {
                    "key": "resources",
                    "path": "resources",
                    "description": "Resource limits and requests",
                    "type": "object",
                    "required": False,
                    "default": {
                        "requests": {"cpu": "100m", "memory": "128Mi"},
                        "limits": {"cpu": "500m", "memory": "512Mi"},
                    },
                },
            ],
        }
        with open("schema.json", "w") as f:
            json.dump(schema_data, f)

        # Create production values (flat structure)
        values_data = {
            "image-tag": "v1.2.3",
            "db-host": "prod-db.example.com",
            "db-password": {"type": "env", "name": "DB_PASSWORD"},
            "redis-enabled": True,
            "redis-password": {"type": "env", "name": "REDIS_PASSWORD"},
            "ingress-hosts": ["api.example.com", "www.example.com"],
            "resources": {
                "requests": {"cpu": "250m", "memory": "256Mi"},
                "limits": {"cpu": "1000m", "memory": "1Gi"},
            },
        }
        with open("values-production.json", "w") as f:
            json.dump(values_data, f)

        # Run generate command
        result = runner.invoke(app, ["generate", "--env", "production"])

        assert result.exit_code == 0

        # Parse and verify the output
        output_yaml = yaml.safe_load(result.stdout)
        assert output_yaml == {
            "global": {
                "appName": "web-service"  # From default
            },
            "image": {"tag": "v1.2.3"},
            "postgresql": {
                "host": "prod-db.example.com",
                "auth": {
                    "password": "postgres123"  # Resolved from env
                },
            },
            "redis": {
                "enabled": True,
                "auth": {
                    "password": "redis456"  # Resolved from env
                },
            },
            "ingress": {"hosts": ["api.example.com", "www.example.com"]},
            "resources": {
                "requests": {"cpu": "250m", "memory": "256Mi"},
                "limits": {"cpu": "1000m", "memory": "1Gi"},
            },
        }
