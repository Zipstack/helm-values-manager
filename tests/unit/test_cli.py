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
