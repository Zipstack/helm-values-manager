"""Test the command line interface."""

import json
import os
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from helm_values_manager.cli import app

runner = CliRunner()


def test_main_no_command():
    """Test main without command."""
    result = runner.invoke(app)
    assert result.exit_code == 0
    assert "Usage: " in result.stdout


def test_init_command(tmp_path):
    """Test init command."""
    # Change to temp directory
    os.chdir(tmp_path)

    result = runner.invoke(app, ["init", "--release", "test-release"], catch_exceptions=False)
    print("Command output:", result.stdout)  # Debug output
    assert result.exit_code == 0
    assert "Successfully initialized helm-values configuration" in result.stdout

    # Verify config file was created
    config_file = Path("helm-values.json")
    assert config_file.exists()
    assert config_file.is_file()

    # Verify lock file was created
    lock_file = Path(".helm-values.lock")
    assert lock_file.exists()
    assert lock_file.is_file()

    # Verify the contents of the config file
    with config_file.open() as file:
        config_data = json.load(file)
        assert config_data == {"version": "1.0", "release": "test-release", "deployments": {}, "config": []}


def test_init_command_empty_release():
    """Test init command with empty release name."""
    result = runner.invoke(app, ["init", "--release", ""])
    assert result.exit_code == 1
    assert "Failed to initialize: Release name cannot be empty" in result.stdout


def test_init_command_already_initialized(tmp_path):
    """Test init command when config already exists."""
    # Change to temp directory
    os.chdir(tmp_path)

    # First initialization
    result = runner.invoke(app, ["init", "--release", "test-release"])
    assert result.exit_code == 0

    # Try to initialize again
    result = runner.invoke(app, ["init", "--release", "another-release"])
    assert result.exit_code == 1
    assert "Failed to initialize: Configuration file" in result.stdout
    assert "already exists" in result.stdout


def test_add_value_config_command(tmp_path):
    """Test add-value-config command."""
    # Change to temp directory
    os.chdir(tmp_path)

    # First initialize a configuration
    init_result = runner.invoke(app, ["init", "--release", "test-release"], catch_exceptions=False)
    assert init_result.exit_code == 0

    # Add a value configuration
    path = "app.replicas"
    description = "Number of application replicas"
    result = runner.invoke(
        app, ["add-value-config", "--path", path, "--description", description, "--required"], catch_exceptions=False
    )

    assert result.exit_code == 0
    assert f"Successfully added value config '{path}'" in result.stdout

    # Verify the configuration file was updated correctly
    config_file = Path("helm-values.json")
    with config_file.open() as file:
        config_data = json.load(file)

    assert "config" in config_data
    assert len(config_data["config"]) == 1
    assert config_data["config"][0]["path"] == path
    assert config_data["config"][0]["description"] == description
    assert config_data["config"][0]["required"] is True
    assert config_data["config"][0]["sensitive"] is False
    assert config_data["config"][0]["values"] == {}


def test_add_value_config_duplicate_path(tmp_path):
    """Test add-value-config command with duplicate path."""
    # Change to temp directory
    os.chdir(tmp_path)

    # First initialize a configuration
    init_result = runner.invoke(app, ["init", "--release", "test-release"], catch_exceptions=False)
    assert init_result.exit_code == 0

    # Add a value configuration
    path = "app.replicas"
    description = "Number of application replicas"
    first_result = runner.invoke(
        app, ["add-value-config", "--path", path, "--description", description], catch_exceptions=False
    )

    assert first_result.exit_code == 0

    # Try to add the same path again
    second_result = runner.invoke(app, ["add-value-config", "--path", path, "--description", "Another description"])

    assert second_result.exit_code == 1
    assert f"Failed to add value config: Path {path} already exists" in second_result.stdout


def test_add_value_config_empty_path(tmp_path):
    """Test add-value-config command with empty path."""
    # Change to temp directory
    os.chdir(tmp_path)

    # First initialize a configuration
    init_result = runner.invoke(app, ["init", "--release", "test-release"], catch_exceptions=False)
    assert init_result.exit_code == 0

    # Try to add a value configuration with empty path
    result = runner.invoke(app, ["add-value-config", "--path", "", "--description", "Some description"])

    assert result.exit_code == 1
    assert "Failed to add value config: Path cannot be empty" in result.stdout


def test_add_value_config_with_sensitive_flag(tmp_path):
    """Test add-value-config command with sensitive flag."""
    # Change to temp directory
    os.chdir(tmp_path)

    # Initialize the config first
    runner.invoke(app, ["init", "--release", "test-release"], catch_exceptions=False)

    # Add a value config with sensitive flag
    result = runner.invoke(
        app,
        ["add-value-config", "--path", "test.path", "--description", "Test description", "--required", "--sensitive"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "Successfully added value config" in result.stdout
    assert "Sensitive value support will be available in version 0.2.0" in result.stdout

    # Verify the config file was updated correctly
    config_file = Path("helm-values.json")
    with config_file.open() as file:
        config_data = json.load(file)
        assert len(config_data["config"]) == 1
        assert config_data["config"][0]["path"] == "test.path"
        assert config_data["config"][0]["description"] == "Test description"
        assert config_data["config"][0]["required"] is True
        assert config_data["config"][0]["sensitive"] is False  # Should be False since the flag is ignored


def test_add_deployment_command(tmp_path):
    """Test add-deployment command."""
    # Change to temp directory
    os.chdir(tmp_path)

    # First initialize the config
    init_result = runner.invoke(app, ["init", "--release", "test-release"], catch_exceptions=False)
    assert init_result.exit_code == 0

    # Now add a deployment
    result = runner.invoke(app, ["add-deployment", "dev"], catch_exceptions=False)
    print("Command output:", result.stdout)  # Debug output
    assert result.exit_code == 0
    assert "Successfully added deployment 'dev'" in result.stdout

    # Verify the deployment was added to the config file
    config_file = Path("helm-values.json")
    with config_file.open() as file:
        config_data = json.load(file)
        assert "dev" in config_data["deployments"]
        assert config_data["deployments"]["dev"]["backend"] == "no-backend"
        assert config_data["deployments"]["dev"]["auth"]["type"] == "no-auth"
        assert config_data["deployments"]["dev"]["backend_config"] == {}


def test_add_deployment_duplicate(tmp_path):
    """Test add-deployment command with duplicate deployment."""
    # Change to temp directory
    os.chdir(tmp_path)

    # First initialize the config
    init_result = runner.invoke(app, ["init", "--release", "test-release"], catch_exceptions=False)
    assert init_result.exit_code == 0

    # Add a deployment
    first_result = runner.invoke(app, ["add-deployment", "dev"], catch_exceptions=False)
    assert first_result.exit_code == 0

    # Try to add the same deployment again
    second_result = runner.invoke(app, ["add-deployment", "dev"], catch_exceptions=False)
    assert second_result.exit_code == 1
    assert "Failed to add deployment: Deployment 'dev' already exists" in second_result.stdout


def test_add_deployment_no_config(tmp_path):
    """Test add-deployment command without initializing config first."""
    # Change to temp directory
    os.chdir(tmp_path)

    # Try to add a deployment without initializing
    result = runner.invoke(app, ["add-deployment", "dev"], catch_exceptions=False)
    assert result.exit_code == 1
    assert "Configuration file helm-values.json not found" in result.stdout


def test_set_value_command(tmp_path):
    """Test set-value command."""
    # Change to temp directory
    os.chdir(tmp_path)

    # Initialize the config
    init_result = runner.invoke(app, ["init", "--release", "test-release"])
    assert init_result.exit_code == 0

    # Add a deployment
    add_deployment_result = runner.invoke(app, ["add-deployment", "dev"])
    assert add_deployment_result.exit_code == 0

    # Add a value config
    add_value_config_result = runner.invoke(
        app, ["add-value-config", "--path", "app.replicas", "--description", "Number of replicas", "--required"]
    )
    assert add_value_config_result.exit_code == 0

    # Set a value
    result = runner.invoke(app, ["set-value", "--path", "app.replicas", "--deployment", "dev", "--value", "3"])
    assert result.exit_code == 0
    assert "Successfully set value for path 'app.replicas' in deployment 'dev'" in result.stdout

    # Verify the value was set by checking the config file
    with open("helm-values.json", "r") as f:
        config = json.load(f)

    # The value itself is stored in the backend, not directly in the config file
    # But we can verify that the path exists in the config
    assert "app.replicas" in [path["path"] for path in config["config"]]


def test_set_value_nonexistent_path(tmp_path):
    """Test set-value command with nonexistent path."""
    # Change to temp directory
    os.chdir(tmp_path)

    # Initialize the config
    init_result = runner.invoke(app, ["init", "--release", "test-release"])
    assert init_result.exit_code == 0

    # Add a deployment
    add_deployment_result = runner.invoke(app, ["add-deployment", "dev"])
    assert add_deployment_result.exit_code == 0

    # Set a value for a nonexistent path
    result = runner.invoke(app, ["set-value", "--path", "nonexistent.path", "--deployment", "dev", "--value", "3"])
    assert result.exit_code == 1
    assert "Path nonexistent.path not found" in result.stdout


def test_set_value_nonexistent_deployment(tmp_path):
    """Test set-value command with nonexistent deployment."""
    # Change to temp directory
    os.chdir(tmp_path)

    # Initialize the config
    init_result = runner.invoke(app, ["init", "--release", "test-release"])
    assert init_result.exit_code == 0

    # Add a value config
    add_value_config_result = runner.invoke(
        app, ["add-value-config", "--path", "app.replicas", "--description", "Number of replicas", "--required"]
    )
    assert add_value_config_result.exit_code == 0

    # Set a value for a nonexistent deployment
    result = runner.invoke(app, ["set-value", "--path", "app.replicas", "--deployment", "nonexistent", "--value", "3"])
    assert result.exit_code == 1
    assert "Deployment 'nonexistent' not found" in result.stdout


def test_set_value_no_config(tmp_path):
    """Test set-value command without initializing config first."""
    # Change to temp directory
    os.chdir(tmp_path)

    result = runner.invoke(app, ["set-value", "--path", "app.replicas", "--deployment", "dev", "--value", "3"])
    assert result.exit_code == 1
    assert "Configuration file helm-values.json not found" in result.stdout


def test_generate_command(tmp_path):
    """Test generate command."""
    # Change to temp directory
    os.chdir(tmp_path)

    # Initialize the config
    runner.invoke(app, ["init", "--release", "test-release"], catch_exceptions=False)

    # Add a deployment
    runner.invoke(app, ["add-deployment", "dev"], catch_exceptions=False)

    # Add value configs
    runner.invoke(
        app,
        ["add-value-config", "--path", "app.replicas", "--description", "Number of replicas"],
        catch_exceptions=False,
    )
    runner.invoke(
        app,
        ["add-value-config", "--path", "app.image.repository", "--description", "Image repository"],
        catch_exceptions=False,
    )

    # Set values
    runner.invoke(
        app, ["set-value", "--path", "app.replicas", "--deployment", "dev", "--value", "3"], catch_exceptions=False
    )
    runner.invoke(
        app,
        ["set-value", "--path", "app.image.repository", "--deployment", "dev", "--value", "myapp"],
        catch_exceptions=False,
    )

    # Generate values file
    result = runner.invoke(app, ["generate", "--deployment", "dev"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Successfully generated values file for deployment 'dev'" in result.stdout

    # Verify the values file exists
    values_file = Path("dev.test-release.values.yaml")
    assert values_file.exists(), "Values file should exist"


def test_generate_with_output_path(tmp_path):
    """Test generate command with custom output path."""
    # Change to temp directory
    os.chdir(tmp_path)

    # Create a custom output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Initialize the config
    runner.invoke(app, ["init", "--release", "test-release"], catch_exceptions=False)

    # Add a deployment
    runner.invoke(app, ["add-deployment", "prod"], catch_exceptions=False)

    # Add value configs and set values
    runner.invoke(
        app,
        ["add-value-config", "--path", "app.replicas", "--description", "Number of replicas"],
        catch_exceptions=False,
    )
    runner.invoke(
        app, ["set-value", "--path", "app.replicas", "--deployment", "prod", "--value", "5"], catch_exceptions=False
    )

    # Generate values file with custom output path
    result = runner.invoke(
        app, ["generate", "--deployment", "prod", "--output", str(output_dir)], catch_exceptions=False
    )
    assert result.exit_code == 0
    assert "Successfully generated values file for deployment 'prod'" in result.stdout

    # Verify the values file exists in the custom output directory
    values_file = output_dir / "prod.test-release.values.yaml"
    assert values_file.exists(), "Values file should exist in the custom output directory"


def test_generate_nonexistent_deployment(tmp_path):
    """Test generate command with a nonexistent deployment."""
    # Change to temp directory
    os.chdir(tmp_path)

    # Initialize the config
    runner.invoke(app, ["init", "--release", "test-release"], catch_exceptions=False)

    # Try to generate values for a nonexistent deployment
    result = runner.invoke(app, ["generate", "--deployment", "nonexistent"])
    assert result.exit_code == 1
    assert "Failed to generate values file" in result.stdout
    assert "Deployment 'nonexistent' not found" in result.stdout


def test_generate_no_config(tmp_path):
    """Test generate command without initializing config first."""
    # Change to temp directory
    os.chdir(tmp_path)

    # Try to generate values without initializing
    result = runner.invoke(app, ["generate", "--deployment", "dev"])
    assert result.exit_code == 1
    assert "Failed to generate values file" in result.stdout
    assert "Configuration file" in result.stdout


def test_generate_command_with_missing_required_value(tmp_path):
    """Test generate command with missing required values."""
    # Change to temp directory
    os.chdir(tmp_path)

    # Initialize the config
    runner.invoke(app, ["init", "--release", "test-release"], catch_exceptions=False)

    # Add a deployment
    runner.invoke(app, ["add-deployment", "dev"], catch_exceptions=False)

    # Add a required value config but don't set a value for it
    runner.invoke(
        app,
        ["add-value-config", "--path", "app.required", "--description", "Required value", "--required"],
        catch_exceptions=False,
    )

    # Try to generate values without setting the required value
    result = runner.invoke(app, ["generate", "--deployment", "dev"])
    assert result.exit_code == 1
    assert "Failed to generate values file" in result.stdout
    assert "Missing required values" in result.stdout
    assert "app.required" in result.stdout


def test_generate_command_error_handling(tmp_path):
    """Test generate command error handling."""
    # Change to temp directory
    os.chdir(tmp_path)

    # Initialize the config
    runner.invoke(app, ["init", "--release", "test-release"], catch_exceptions=False)

    # Add a deployment
    runner.invoke(app, ["add-deployment", "dev"], catch_exceptions=False)

    # Mock the GenerateCommand to raise an exception
    with patch("helm_values_manager.cli.GenerateCommand") as mock_command:
        mock_instance = mock_command.return_value
        mock_instance.execute.side_effect = ValueError("Test error")

        # Try to generate values
        result = runner.invoke(app, ["generate", "--deployment", "dev"])
        assert result.exit_code == 1
        assert "Failed to generate values file: Test error" in result.stdout
