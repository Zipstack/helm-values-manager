"""Tests for the values init command."""

import json
import os
from pathlib import Path

from typer.testing import CliRunner

from helm_values_manager.cli import app
from helm_values_manager.models import Schema, SchemaValue

runner = CliRunner()


def create_test_schema_for_init():
    """Create a test schema for init command tests."""
    return Schema(
        version="1.0",
        values=[
            SchemaValue(
                key="app-name",
                path="app.name",
                description="Application name",
                type="string",
                required=True,
                default="myapp",
            ),
            SchemaValue(
                key="port",
                path="app.port",
                description="Application port",
                type="number",
                required=True,
            ),
            SchemaValue(
                key="debug",
                path="app.debug",
                description="Enable debug mode",
                type="boolean",
                required=False,
                default=False,
            ),
            SchemaValue(
                key="api-key",
                path="api.key",
                description="API key for external service",
                type="string",
                required=True,
                sensitive=True,
            ),
            SchemaValue(
                key="features",
                path="app.features",
                description="Feature flags",
                type="array",
                required=False,
            ),
        ],
    )


def test_values_init_force_mode_with_defaults(tmp_path):
    """Test init command in force mode uses defaults and prompts for required fields without defaults."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema_for_init()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Force mode now prompts for required fields without defaults
        # Order: api-key first (1 for env, SECRET_KEY for name), then port (8080)
        result = runner.invoke(
            app, ["values", "init", "--env", "dev", "--force"], input="1\nSECRET_KEY\n8080\n"
        )

        assert result.exit_code == 0
        assert "Using default value: myapp" in result.output
        assert "Using default value:" in result.output
        assert "False" in result.output
        assert "Required field with no default, prompting" in result.output  # port and api-key

        # Check saved values (flat structure)
        with open("values-dev.json") as f:
            values = json.load(f)

        assert values["app-name"] == "myapp"
        assert values["debug"] is False
        assert values["port"] == 8080  # Now included because we prompted for it
        assert values["api-key"]["type"] == "env"  # Secret now set up
        assert values["api-key"]["name"] == "SECRET_KEY"


def test_values_init_interactive_set_values(tmp_path):
    """Test interactive mode setting values."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema_for_init()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Simulate user input (order: api-key, app-name, port, debug, features):
        # - api-key: y, 1, API_KEY
        # - app-name: y, use default (empty input)
        # - port: y, 8080
        # - debug: skip (skip all remaining)
        result = runner.invoke(
            app, ["values", "init", "--env", "staging"], input="y\n1\nAPI_KEY\ny\n\ny\n8080\nskip\n"
        )

        assert result.exit_code == 0
        assert "port" in result.output
        assert "api-key" in result.output
        assert "This is a sensitive value" in result.output

        # Check saved values (flat structure)
        with open("values-staging.json") as f:
            values = json.load(f)

        assert values["port"] == 8080
        assert values["api-key"] == {"type": "env", "name": "API_KEY"}
        assert values["app-name"] == "myapp"  # Used default
        assert "debug" not in values  # Skip all was chosen
        assert "features" not in values  # Skip all was chosen


def test_values_init_skip_existing_values(tmp_path):
    """Test that init skips already set values."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema_for_init()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Create existing values file (flat structure)
        existing_values = {"app-name": "existing-app", "port": 443}
        with open("values-prod.json", "w") as f:
            json.dump(existing_values, f)

        # Only api-key and optional fields should be prompted since app-name and port are already set
        result = runner.invoke(
            app, ["values", "init", "--env", "prod"], input="y\n1\nPROD_API_KEY\nskip\n"
        )

        assert result.exit_code == 0
        assert "app-name" not in result.output  # Already set, not prompted
        assert "port" not in result.output  # Already set, not prompted
        assert "api-key" in result.output  # Not set, should be prompted

        # Check saved values - existing should remain (flat structure)
        with open("values-prod.json") as f:
            values = json.load(f)

        assert values["app-name"] == "existing-app"  # Unchanged
        assert values["port"] == 443  # Unchanged
        assert values["api-key"] == {"type": "env", "name": "PROD_API_KEY"}  # Added


def test_values_init_type_validation(tmp_path):
    """Test that init validates input types."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema_for_init()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Simulate invalid input followed by valid input (order: api-key, app-name, port)
        # Skip api-key, skip app-name, then try invalid then valid input for port
        result = runner.invoke(
            app, ["values", "init", "--env", "test"], input="n\nn\ny\ninvalid\n8080\nskip\n"
        )

        assert result.exit_code == 0
        assert "Invalid value:" in result.output  # Should show validation error

        # Check saved values (flat structure)
        with open("values-test.json") as f:
            values = json.load(f)

        assert values["port"] == 8080  # Should have the correct value


def test_values_init_missing_schema(tmp_path):
    """Test init command with missing schema file."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["values", "init", "--env", "dev"])

        assert result.exit_code == 1
        assert "Schema file not found" in result.output


def test_values_init_required_fields_summary(tmp_path):
    """Test that init shows summary of unset required fields."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema_for_init()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Skip all required fields without defaults
        result = runner.invoke(app, ["values", "init", "--env", "incomplete"], input="skip\n")

        assert result.exit_code == 0
        assert "Warning: The following required values were not set:" in result.output
        assert "port" in result.output
        assert "api-key" in result.output


def test_values_init_array_and_default_handling(tmp_path):
    """Test init command with array types and default values."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema_for_init()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Test setting an array value and using defaults (order: api-key, app-name, port, debug, features)
        # Skip api-key, use default for app-name, skip port, skip debug, set features
        result = runner.invoke(
            app,
            ["values", "init", "--env", "feature-test"],
            input='n\ny\n\nn\nn\ny\n["feature1", "feature2"]\n',
        )

        assert result.exit_code == 0

        # Check saved values (flat structure)
        with open("values-feature-test.json") as f:
            values = json.load(f)

        assert values["app-name"] == "myapp"  # Used default
        assert values["features"] == ["feature1", "feature2"]  # User input
        assert "api-key" not in values  # User skipped
        assert "port" not in values  # User skipped
        assert "debug" not in values  # User skipped


def test_values_init_env_var_warning(tmp_path, monkeypatch):
    """Test that init warns when environment variable doesn't exist."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        schema = create_test_schema_for_init()
        with open("schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        # Ensure the env var doesn't exist
        monkeypatch.delenv("NONEXISTENT_VAR", raising=False)

        result = runner.invoke(
            app, ["values", "init", "--env", "warning-test"], input="y\n1\nNONEXISTENT_VAR\nskip\n"
        )

        assert result.exit_code == 0
        assert "Warning: Environment variable 'NONEXISTENT_VAR' is not set" in result.output


def test_values_init_custom_schema_and_values_path(tmp_path):
    """Test init command with custom schema and values paths."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create custom schema in subdirectory
        os.makedirs("config", exist_ok=True)
        schema = create_test_schema_for_init()
        with open("config/custom-schema.json", "w") as f:
            json.dump(schema.model_dump(), f)

        result = runner.invoke(
            app,
            [
                "values",
                "init",
                "--env",
                "custom",
                "--schema",
                "config/custom-schema.json",
                "--values",
                "config/custom-values-custom.json",
                "--force",
            ],
            input="1\nCUSTOM_SECRET\n8080\n",
        )  # Input order: api-key secret, then port

        assert result.exit_code == 0

        # Check values were saved to custom path (flat structure)
        assert Path("config/custom-values-custom.json").exists()
        with open("config/custom-values-custom.json") as f:
            values = json.load(f)

        assert values["app-name"] == "myapp"
        assert values["debug"] is False
