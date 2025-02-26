"""Integration tests for the helm-values-manager CLI."""

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
