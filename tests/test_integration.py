"""Integration tests for end-to-end workflows."""

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from helm_values_manager.cli import app

runner = CliRunner()


def test_complete_vendor_workflow(tmp_path, monkeypatch):
    """Test complete vendor workflow: init schema, add values, validate."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # 1. Initialize schema
        result = runner.invoke(app, ["init", "--force"])
        assert result.exit_code == 0
        assert Path("schema.json").exists()

        # 2. Add various types of schema values
        schema_commands = [
            # String value with default
            ["schema", "add"],
            # Input: app-name, app.name, Application name, string, y, myapp, n
            # Number value without default
            ["schema", "add"],
            # Input: port, app.port, Application port, number, y, n, n
            # Boolean value with default
            ["schema", "add"],
            # Input: debug, app.debug, Debug mode, boolean, n, y, false, n
            # Secret value
            ["schema", "add"],
            # Input: api-key, app.apiKey, API key, string, y, n, y
            # Array value
            ["schema", "add"],
            # Input: features, app.features, Feature flags, array, n, n, n
        ]

        # Add app-name with default
        result = runner.invoke(
            app,
            schema_commands[0],
            input="app-name\napp.name\nApplication name\nstring\ny\ny\nmyapp\nn\n",
        )
        assert result.exit_code == 0

        # Add port (required, no default)
        result = runner.invoke(
            app, schema_commands[1], input="port\napp.port\nApplication port\nnumber\ny\nn\nn\n"
        )
        assert result.exit_code == 0

        # Add debug (optional with default)
        result = runner.invoke(
            app, schema_commands[2], input="debug\napp.debug\nDebug mode\nboolean\nn\ny\nfalse\nn\n"
        )
        assert result.exit_code == 0

        # Add api-key (required, sensitive)
        result = runner.invoke(
            app, schema_commands[3], input="api-key\napp.apiKey\nAPI key\nstring\ny\nn\ny\n"
        )
        assert result.exit_code == 0

        # Add features (optional array)
        result = runner.invoke(
            app, schema_commands[4], input="features\napp.features\nFeature flags\narray\nn\nn\nn\n"
        )
        assert result.exit_code == 0

        # 3. Verify schema was created correctly
        result = runner.invoke(app, ["schema", "list"])
        assert result.exit_code == 0
        assert "app-name" in result.output
        assert "port" in result.output
        assert "debug" in result.output
        assert "api-key" in result.output
        assert "features" in result.output


def test_complete_customer_workflow(tmp_path, monkeypatch):
    """Test complete customer workflow: use schema, set values, generate."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create pre-existing schema (as if from vendor)
        schema_data = {
            "version": "1.0",
            "values": [
                {
                    "key": "app-name",
                    "path": "app.name",
                    "description": "Application name",
                    "type": "string",
                    "required": True,
                    "default": "myapp",
                },
                {
                    "key": "port",
                    "path": "app.port",
                    "description": "Application port",
                    "type": "number",
                    "required": True,
                },
                {
                    "key": "replicas",
                    "path": "deployment.replicas",
                    "description": "Number of replicas",
                    "type": "number",
                    "required": False,
                    "default": 1,
                },
                {
                    "key": "api-key",
                    "path": "app.apiKey",
                    "description": "API key",
                    "type": "string",
                    "required": True,
                    "sensitive": True,
                },
                {
                    "key": "features",
                    "path": "app.features",
                    "description": "Feature flags",
                    "type": "array",
                    "required": False,
                },
            ],
        }

        with open("schema.json", "w") as f:
            json.dump(schema_data, f, indent=2)

        # Set environment variable for secret
        monkeypatch.setenv("PROD_API_KEY", "super-secret-key")

        # 1. Set values for production environment

        # Set port (required)
        result = runner.invoke(app, ["values", "set", "port", "8080", "--env", "prod"])
        assert result.exit_code == 0

        # Set secret
        result = runner.invoke(
            app, ["values", "set-secret", "api-key", "--env", "prod"], input="1\nPROD_API_KEY\n"
        )
        assert result.exit_code == 0

        # Set optional array
        result = runner.invoke(
            app, ["values", "set", "features", '["auth", "logging"]', "--env", "prod"]
        )
        assert result.exit_code == 0

        # Override default for replicas
        result = runner.invoke(app, ["values", "set", "replicas", "3", "--env", "prod"])
        assert result.exit_code == 0

        # 2. List values to verify
        result = runner.invoke(app, ["values", "list", "--env", "prod"])
        assert result.exit_code == 0
        assert "port" in result.output
        assert "8080" in result.output
        assert "api-key" in result.output
        assert "SECRET" in result.output
        assert "features" in result.output
        assert "replicas" in result.output

        # 3. Validate configuration
        result = runner.invoke(app, ["validate", "--env", "prod"])
        assert result.exit_code == 0
        assert "Validation passed" in result.output

        # 4. Generate values.yaml
        result = runner.invoke(app, ["generate", "--env", "prod"])
        assert result.exit_code == 0

        # Parse and verify generated YAML
        generated_yaml = yaml.safe_load(result.stdout)

        expected_structure = {
            "app": {
                "name": "myapp",  # From default
                "port": 8080,  # Set by user
                "apiKey": "super-secret-key",  # Resolved from env var
                "features": ["auth", "logging"],  # Set by user
            },
            "deployment": {
                "replicas": 3  # Override default
            },
        }

        assert generated_yaml == expected_structure


def test_multi_environment_workflow(tmp_path, monkeypatch):
    """Test managing multiple environments with the same schema."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Set up environment variables
        monkeypatch.setenv("DEV_DB_PASSWORD", "dev-password")
        monkeypatch.setenv("PROD_DB_PASSWORD", "prod-password")

        # Create schema
        schema_data = {
            "version": "1.0",
            "values": [
                {
                    "key": "environment",
                    "path": "global.environment",
                    "description": "Environment name",
                    "type": "string",
                    "required": True,
                },
                {
                    "key": "database-host",
                    "path": "database.host",
                    "description": "Database hostname",
                    "type": "string",
                    "required": True,
                },
                {
                    "key": "database-password",
                    "path": "database.password",
                    "description": "Database password",
                    "type": "string",
                    "required": True,
                    "sensitive": True,
                },
                {
                    "key": "replicas",
                    "path": "deployment.replicas",
                    "description": "Number of replicas",
                    "type": "number",
                    "required": False,
                    "default": 1,
                },
            ],
        }

        with open("schema.json", "w") as f:
            json.dump(schema_data, f, indent=2)

        # Configure development environment
        result = runner.invoke(app, ["values", "set", "environment", "development", "--env", "dev"])
        assert result.exit_code == 0

        result = runner.invoke(
            app, ["values", "set", "database-host", "dev-db.local", "--env", "dev"]
        )
        assert result.exit_code == 0

        result = runner.invoke(
            app,
            ["values", "set-secret", "database-password", "--env", "dev"],
            input="1\nDEV_DB_PASSWORD\n",
        )
        assert result.exit_code == 0

        # Configure production environment
        result = runner.invoke(app, ["values", "set", "environment", "production", "--env", "prod"])
        assert result.exit_code == 0

        result = runner.invoke(
            app, ["values", "set", "database-host", "prod-db.example.com", "--env", "prod"]
        )
        assert result.exit_code == 0

        result = runner.invoke(
            app,
            ["values", "set-secret", "database-password", "--env", "prod"],
            input="1\nPROD_DB_PASSWORD\n",
        )
        assert result.exit_code == 0

        result = runner.invoke(app, ["values", "set", "replicas", "5", "--env", "prod"])
        assert result.exit_code == 0

        # Validate both environments
        result = runner.invoke(app, ["validate", "--env", "dev"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["validate", "--env", "prod"])
        assert result.exit_code == 0

        # Generate and verify dev configuration
        result = runner.invoke(app, ["generate", "--env", "dev"])
        assert result.exit_code == 0

        dev_yaml = yaml.safe_load(result.stdout)
        assert dev_yaml["global"]["environment"] == "development"
        assert dev_yaml["database"]["host"] == "dev-db.local"
        assert dev_yaml["database"]["password"] == "dev-password"
        assert dev_yaml["deployment"]["replicas"] == 1  # Default

        # Generate and verify prod configuration
        result = runner.invoke(app, ["generate", "--env", "prod"])
        assert result.exit_code == 0

        prod_yaml = yaml.safe_load(result.stdout)
        assert prod_yaml["global"]["environment"] == "production"
        assert prod_yaml["database"]["host"] == "prod-db.example.com"
        assert prod_yaml["database"]["password"] == "prod-password"
        assert prod_yaml["deployment"]["replicas"] == 5  # Override


def test_error_recovery_workflow(tmp_path):
    """Test error scenarios and recovery."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # 1. Try to use commands without schema
        result = runner.invoke(app, ["values", "set", "key", "value", "--env", "test"])
        assert result.exit_code == 1
        assert "No schema.json found" in result.output

        result = runner.invoke(app, ["validate", "--env", "test"])
        assert result.exit_code == 1
        assert "Schema file not found" in result.output

        result = runner.invoke(app, ["generate", "--env", "test"])
        assert result.exit_code == 1
        assert "Schema file not found" in result.output

        # 2. Create schema
        result = runner.invoke(app, ["init", "--force"])
        assert result.exit_code == 0

        # 3. Try to add duplicate key
        result = runner.invoke(
            app, ["schema", "add"], input="test-key\ntest.path\nTest description\nstring\ny\nn\nn\n"
        )
        assert result.exit_code == 0

        result = runner.invoke(
            app, ["schema", "add"], input="test-key\ntest.path2\nDuplicate key\nstring\ny\nn\nn\n"
        )
        assert result.exit_code == 1
        assert "already exists" in result.output

        # 4. Try to set non-existent key
        result = runner.invoke(app, ["values", "set", "non-existent", "value", "--env", "test"])
        assert result.exit_code == 1
        assert "not found in schema" in result.output

        # 5. Try to validate with missing required values
        result = runner.invoke(app, ["validate", "--env", "test"])
        assert result.exit_code == 1
        assert "Missing required value" in result.output

        # 6. Try to generate with validation errors
        result = runner.invoke(app, ["generate", "--env", "test"])
        assert result.exit_code == 1
        assert "Validation failed" in result.output


def test_schema_evolution_workflow(tmp_path):
    """Test schema evolution and backwards compatibility."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # 1. Create initial schema with one value
        result = runner.invoke(app, ["init", "--force"])
        assert result.exit_code == 0

        result = runner.invoke(
            app,
            ["schema", "add"],
            input="app-name\napp.name\nApplication name\nstring\ny\ny\nmyapp\nn\n",
        )
        assert result.exit_code == 0

        # 2. Set initial values
        result = runner.invoke(app, ["values", "set", "app-name", "test-app", "--env", "test"])
        assert result.exit_code == 0

        # 3. Evolve schema - add new optional field
        result = runner.invoke(
            app,
            ["schema", "add"],
            input="version\napp.version\nApplication version\nstring\nn\ny\n1.0.0\nn\n",
        )
        assert result.exit_code == 0

        # 4. Validate existing environment still works (backwards compatibility)
        result = runner.invoke(app, ["validate", "--env", "test"])
        assert result.exit_code == 0

        # 5. Generate with new optional field using default
        result = runner.invoke(app, ["generate", "--env", "test"])
        assert result.exit_code == 0

        generated = yaml.safe_load(result.stdout)
        assert generated["app"]["name"] == "test-app"
        assert generated["app"]["version"] == "1.0.0"  # From default

        # 6. Add new required field
        result = runner.invoke(
            app, ["schema", "add"], input="port\napp.port\nApplication port\nnumber\ny\nn\nn\n"
        )
        assert result.exit_code == 0

        # 7. Validation should now fail
        result = runner.invoke(app, ["validate", "--env", "test"])
        assert result.exit_code == 1
        assert "Missing required value: port" in result.output

        # 8. Set the new required value
        result = runner.invoke(app, ["values", "set", "port", "8080", "--env", "test"])
        assert result.exit_code == 0

        # 9. Validation should pass again
        result = runner.invoke(app, ["validate", "--env", "test"])
        assert result.exit_code == 0


def test_complex_data_types_workflow(tmp_path):
    """Test workflow with complex data types (arrays and objects)."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create schema with complex types
        schema_data = {
            "version": "1.0",
            "values": [
                {
                    "key": "hosts",
                    "path": "ingress.hosts",
                    "description": "Ingress hostnames",
                    "type": "array",
                    "required": True,
                },
                {
                    "key": "resources",
                    "path": "resources",
                    "description": "Resource limits",
                    "type": "object",
                    "required": False,
                    "default": {
                        "requests": {"cpu": "100m", "memory": "128Mi"},
                        "limits": {"cpu": "500m", "memory": "512Mi"},
                    },
                },
                {
                    "key": "annotations",
                    "path": "ingress.annotations",
                    "description": "Ingress annotations",
                    "type": "object",
                    "required": False,
                },
            ],
        }

        with open("schema.json", "w") as f:
            json.dump(schema_data, f, indent=2)

        # Set array value
        result = runner.invoke(
            app,
            ["values", "set", "hosts", '["api.example.com", "www.example.com"]', "--env", "prod"],
        )
        assert result.exit_code == 0

        # Set object value (override default)
        result = runner.invoke(
            app,
            [
                "values",
                "set",
                "resources",
                '{"requests": {"cpu": "200m", "memory": "256Mi"}}',
                "--env",
                "prod",
            ],
        )
        assert result.exit_code == 0

        # Set nested object
        result = runner.invoke(
            app,
            [
                "values",
                "set",
                "annotations",
                '{"nginx.ingress.kubernetes.io/rewrite-target": "/"}',
                "--env",
                "prod",
            ],
        )
        assert result.exit_code == 0

        # Validate and generate
        result = runner.invoke(app, ["validate", "--env", "prod"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["generate", "--env", "prod"])
        assert result.exit_code == 0

        generated = yaml.safe_load(result.stdout)

        # Verify complex structures
        assert generated["ingress"]["hosts"] == ["api.example.com", "www.example.com"]
        assert generated["resources"]["requests"]["cpu"] == "200m"
        assert generated["resources"]["requests"]["memory"] == "256Mi"
        assert (
            generated["ingress"]["annotations"]["nginx.ingress.kubernetes.io/rewrite-target"] == "/"
        )
