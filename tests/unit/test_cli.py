"""Test the command line interface."""

import json
import os
from pathlib import Path

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
