"""Integration tests for the helm-values-manager CLI."""

import json
import os
import subprocess
from pathlib import Path

import pytest


def run_helm_command(command: list[str]) -> tuple[str, str, int]:
    """Run a helm command and return stdout, stderr, and return code."""
    process = subprocess.run(["helm"] + command, capture_output=True, text=True)
    return process.stdout, process.stderr, process.returncode


@pytest.fixture(autouse=True)
def cleanup_plugin():
    """Ensure plugin is cleaned up after each test."""
    yield
    try:
        subprocess.run(
            ["helm", "plugin", "uninstall", "values-manager"],
            capture_output=True,
            text=True,
            check=False,  # Don't raise on error
        )
    except Exception:
        # Ignore any errors during cleanup
        pass


@pytest.fixture
def plugin_install(tmp_path):
    """Install the plugin in a temporary directory."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent

    # First, try to uninstall if it exists
    try:
        subprocess.run(
            ["helm", "plugin", "uninstall", "values-manager"],
            capture_output=True,
            text=True,
            check=False,  # Don't raise on error
        )
    except Exception:
        # Ignore any errors during uninstall
        pass

    # Install the plugin
    subprocess.run(["helm", "plugin", "install", str(project_root)], capture_output=True, text=True, check=True)

    yield


def test_help_command(plugin_install):
    """Test that the help command works and shows expected output."""
    stdout, stderr, returncode = run_helm_command(["values-manager", "--help"])

    assert returncode == 0
    assert "Usage: helm values-manager [OPTIONS] COMMAND [ARGS]..." in stdout
    # Check for description split across lines
    assert "A Helm plugin to manage values and secrets across" in stdout
    assert "environments" in stdout
    assert "init" in stdout  # Check that init command is listed


def test_init_help_command(plugin_install):
    """Test that the init help command works and shows expected output."""
    stdout, stderr, returncode = run_helm_command(["values-manager", "init", "--help"])

    assert returncode == 0
    assert "Initialize a new values manager configuration" in stdout
    assert "--release" in stdout
    assert "-r" in stdout


def test_init_command(plugin_install, tmp_path):
    """Test that the init command works."""
    # Change to temp directory to avoid conflicts
    os.chdir(tmp_path)
    stdout, stderr, returncode = run_helm_command(["values-manager", "init", "-r", "test"])

    assert returncode == 0
    assert "Successfully initialized helm-values configuration" in stdout
    assert Path("helm-values.json").exists()
    assert Path(".helm-values.lock").exists()


def test_add_value_config_help_command(plugin_install):
    """Test that the add-value-config help command works and shows expected output."""
    stdout, stderr, returncode = run_helm_command(["values-manager", "add-value-config", "--help"])

    assert returncode == 0
    assert "Add a new value configuration with metadata" in stdout
    assert "--path" in stdout
    assert "--description" in stdout
    assert "--required" in stdout
    assert "--sensitive" in stdout


def test_add_value_config_command(plugin_install, tmp_path):
    """Test that the add-value-config command works correctly."""
    # Change to temp directory to avoid conflicts
    os.chdir(tmp_path)

    # First initialize a configuration
    init_stdout, init_stderr, init_returncode = run_helm_command(["values-manager", "init", "-r", "test-app"])
    assert init_returncode == 0

    # Add a value configuration
    path = "app.replicas"
    description = "Number of application replicas"
    stdout, stderr, returncode = run_helm_command(
        ["values-manager", "add-value-config", "--path", path, "--description", description, "--required"]
    )

    assert returncode == 0
    assert f"Successfully added value config '{path}'" in stdout

    # Verify the configuration file was updated correctly
    with open("helm-values.json", "r") as f:
        config = json.load(f)

    # Check that the config contains our new value
    assert "config" in config
    assert len(config["config"]) == 1
    assert config["config"][0]["path"] == path
    assert config["config"][0]["description"] == description
    assert config["config"][0]["required"] is True
    assert config["config"][0]["sensitive"] is False
    assert config["config"][0]["values"] == {}

    # Add another value configuration
    second_path = "app.image.tag"
    second_description = "Application image tag"
    stdout, stderr, returncode = run_helm_command(
        [
            "values-manager",
            "add-value-config",
            "--path",
            second_path,
            "--description",
            second_description,
            "--sensitive",
        ]
    )

    assert returncode == 0
    assert f"Successfully added value config '{second_path}'" in stdout

    # Verify the configuration file was updated correctly
    with open("helm-values.json", "r") as f:
        config = json.load(f)

    # Check that the config contains both values
    assert "config" in config
    assert len(config["config"]) == 2

    # Find the second added config
    second_config = next((c for c in config["config"] if c["path"] == second_path), None)
    assert second_config is not None
    assert second_config["description"] == second_description
    assert second_config["required"] is False
    assert second_config["sensitive"] is True
    assert second_config["values"] == {}


def test_add_value_config_duplicate_path(plugin_install, tmp_path):
    """Test that adding a duplicate path fails with the correct error message."""
    # Change to temp directory to avoid conflicts
    os.chdir(tmp_path)

    # First initialize a configuration
    init_stdout, init_stderr, init_returncode = run_helm_command(["values-manager", "init", "-r", "test-app"])
    assert init_returncode == 0

    # Add a value configuration
    path = "app.replicas"
    description = "Number of application replicas"
    stdout, stderr, returncode = run_helm_command(
        ["values-manager", "add-value-config", "--path", path, "--description", description]
    )

    assert returncode == 0

    # Try to add the same path again
    stdout, stderr, returncode = run_helm_command(
        ["values-manager", "add-value-config", "--path", path, "--description", "Another description"]
    )

    assert returncode != 0
    assert f"Path {path} already exists" in stderr
