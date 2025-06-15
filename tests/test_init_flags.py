"""Tests for values init command flag behavior."""

import json

from typer.testing import CliRunner

from helm_values_manager.cli import app

runner = CliRunner()


def test_force_mode_fixed_behavior(tmp_path):
    """Test that --force mode prompts for required fields without defaults."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create schema with mix of fields
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
                    # No default - should be prompted even in force mode
                },
                {
                    "key": "debug",
                    "path": "app.debug",
                    "description": "Debug mode",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                },
                {
                    "key": "features",
                    "path": "app.features",
                    "description": "Feature flags",
                    "type": "array",
                    "required": False,
                    # No default - should be skipped in force mode
                },
            ],
        }

        with open("schema.json", "w") as f:
            json.dump(schema_data, f, indent=2)

        # Test force mode with input for required field
        result = runner.invoke(
            app, ["values", "init", "--env", "test", "--force"], input="8080\n"
        )  # Input for port

        assert result.exit_code == 0

        # Check output messages
        assert "Using default value: myapp" in result.output
        assert "Using default value:" in result.output
        assert "False" in result.output
        assert "Required field with no default, prompting" in result.output
        assert "Skipping optional field without default" in result.output

        # Check generated values file
        with open("values-test.json") as f:
            values = json.load(f)

        expected_values = {
            "app-name": "myapp",  # From default
            "port": 8080,  # From user input
            "debug": False,  # From default
            # features should not be present (skipped)
        }

        assert values == expected_values


def test_skip_defaults_mode(tmp_path):
    """Test that --skip-defaults skips fields with defaults."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create schema
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
                    "key": "debug",
                    "path": "app.debug",
                    "description": "Debug mode",
                    "type": "boolean",
                    "required": False,
                    "default": False,
                },
            ],
        }

        with open("schema.json", "w") as f:
            json.dump(schema_data, f, indent=2)

        # Test skip-defaults mode
        result = runner.invoke(
            app, ["values", "init", "--env", "test", "--skip-defaults"], input="y\n8080\n"
        )  # y for port, 8080 as value

        assert result.exit_code == 0

        # Check output messages
        assert "Skipping field with default value" in result.output

        # Check generated values file
        with open("values-test.json") as f:
            values = json.load(f)

        # Should only have port (no defaults used)
        expected_values = {"port": 8080}

        assert values == expected_values


def test_force_and_skip_defaults_combined(tmp_path):
    """Test --force and --skip-defaults together."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Create schema
        schema_data = {
            "version": "1.0",
            "values": [
                {
                    "key": "app-name",
                    "path": "app.name",
                    "description": "Application name",
                    "type": "string",
                    "required": False,
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
                    "key": "optional-port",
                    "path": "app.optionalPort",
                    "description": "Optional port",
                    "type": "number",
                    "required": False,
                },
            ],
        }

        with open("schema.json", "w") as f:
            json.dump(schema_data, f, indent=2)

        # Test both flags together
        result = runner.invoke(
            app, ["values", "init", "--env", "test", "--force", "--skip-defaults"], input="8080\n"
        )  # Input for required port

        assert result.exit_code == 0

        # Check output messages
        assert "Skipping field with default value" in result.output  # app-name skipped
        assert "Required field with no default, prompting" in result.output  # port prompted
        assert "Skipping optional field without default" in result.output  # optional-port skipped

        # Check generated values file
        with open("values-test.json") as f:
            values = json.load(f)

        # Should only have port
        expected_values = {"port": 8080}

        assert values == expected_values


def test_force_mode_help_text():
    """Test that help text is updated correctly."""
    result = runner.invoke(app, ["values", "init", "--help"])
    assert result.exit_code == 0
    # Check that the help text contains key phrases (may be wrapped across lines)
    assert "required fields without defaults" in result.output
    assert "skip-defaults" in result.output
    assert "Skip fields with default values entirely" in result.output
