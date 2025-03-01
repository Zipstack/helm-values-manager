"""Integration tests for the helm-values-manager CLI."""

import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml


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
    # The sensitive flag is now hidden, so it shouldn't appear in help
    # assert "--sensitive" in stdout


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
    assert second_config["sensitive"] is False
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


def test_add_deployment_help_command(plugin_install):
    """Test that the add-deployment help command works and shows expected output."""
    stdout, stderr, returncode = run_helm_command(["values-manager", "add-deployment", "--help"])
    assert returncode == 0
    assert "Add a new deployment configuration" in stdout


def test_add_deployment_command(plugin_install, tmp_path):
    """Test that the add-deployment command works correctly."""
    # Create a working directory
    work_dir = tmp_path / "test_add_deployment"
    work_dir.mkdir()
    os.chdir(work_dir)

    # Initialize the config
    init_stdout, init_stderr, init_returncode = run_helm_command(
        ["values-manager", "init", "--release", "test-release"]
    )
    assert init_returncode == 0
    assert Path("helm-values.json").exists()

    # Add a deployment
    stdout, stderr, returncode = run_helm_command(["values-manager", "add-deployment", "dev"])
    assert returncode == 0
    assert "Successfully added deployment 'dev'" in stdout

    # Verify the deployment was added
    with open("helm-values.json", "r") as f:
        config = json.load(f)
    assert "dev" in config["deployments"]


def test_add_deployment_duplicate(plugin_install, tmp_path):
    """Test that adding a duplicate deployment fails with the correct error message."""
    # Create a working directory
    work_dir = tmp_path / "test_add_deployment_duplicate"
    work_dir.mkdir()
    os.chdir(work_dir)

    # Initialize the config
    init_stdout, init_stderr, init_returncode = run_helm_command(
        ["values-manager", "init", "--release", "test-release"]
    )
    assert init_returncode == 0
    assert Path("helm-values.json").exists()

    # Add a deployment
    stdout, stderr, returncode = run_helm_command(["values-manager", "add-deployment", "dev"])
    assert returncode == 0

    # Try to add the same deployment again
    stdout, stderr, returncode = run_helm_command(["values-manager", "add-deployment", "dev"])
    assert returncode == 1
    assert "Deployment 'dev' already exists" in stderr


def test_add_deployment_no_config(plugin_install, tmp_path):
    """Test that adding a deployment without initializing fails with the correct error message."""
    # Create a working directory
    work_dir = tmp_path / "test_add_deployment_no_config"
    work_dir.mkdir()
    os.chdir(work_dir)

    # Try to add a deployment without initializing
    stdout, stderr, returncode = run_helm_command(["values-manager", "add-deployment", "dev"])
    assert returncode == 1
    assert "Configuration file helm-values.json not found" in stderr


def test_set_value_command(plugin_install, tmp_path):
    """Test that the set-value command works correctly."""
    # Create a working directory
    work_dir = tmp_path / "test_set_value"
    work_dir.mkdir()
    os.chdir(work_dir)

    # Initialize the config
    init_stdout, init_stderr, init_returncode = run_helm_command(
        ["values-manager", "init", "--release", "test-release"]
    )
    assert init_returncode == 0
    assert Path("helm-values.json").exists()

    # Add a deployment
    add_deployment_stdout, add_deployment_stderr, add_deployment_returncode = run_helm_command(
        ["values-manager", "add-deployment", "dev"]
    )
    assert add_deployment_returncode == 0

    # Add a value config
    add_value_config_stdout, add_value_config_stderr, add_value_config_returncode = run_helm_command(
        [
            "values-manager",
            "add-value-config",
            "--path",
            "app.replicas",
            "--description",
            "Number of replicas",
            "--required",
        ]
    )
    assert add_value_config_returncode == 0

    # Set a value
    stdout, stderr, returncode = run_helm_command(
        ["values-manager", "set-value", "--path", "app.replicas", "--deployment", "dev", "--value", "3"]
    )
    assert returncode == 0
    assert "Successfully set value for path 'app.replicas' in deployment 'dev'" in stdout

    # Verify the value was set
    with open("helm-values.json", "r") as f:
        config = json.load(f)

    # The value itself is stored in the backend, not directly in the config file
    # But we can verify that the path exists in the config
    assert any(path["path"] == "app.replicas" for path in config["config"])


def test_set_value_nonexistent_path(plugin_install, tmp_path):
    """Test that setting a value for a nonexistent path fails with the correct error message."""
    # Create a working directory
    work_dir = tmp_path / "test_set_value_nonexistent_path"
    work_dir.mkdir()
    os.chdir(work_dir)

    # Initialize the config
    init_stdout, init_stderr, init_returncode = run_helm_command(
        ["values-manager", "init", "--release", "test-release"]
    )
    assert init_returncode == 0
    assert Path(work_dir, "helm-values.json").exists()

    # Add a deployment
    add_deployment_stdout, add_deployment_stderr, add_deployment_returncode = run_helm_command(
        ["values-manager", "add-deployment", "dev"]
    )
    assert add_deployment_returncode == 0

    # Try to set a value for a nonexistent path
    stdout, stderr, returncode = run_helm_command(
        ["values-manager", "set-value", "--path", "nonexistent.path", "--deployment", "dev", "--value", "3"]
    )
    assert returncode == 1
    assert "Path nonexistent.path not found" in stderr


def test_set_value_nonexistent_deployment(plugin_install, tmp_path):
    """Test that setting a value for a nonexistent deployment fails with the correct error message."""
    # Create a working directory
    work_dir = tmp_path / "test_set_value_nonexistent_deployment"
    work_dir.mkdir()
    os.chdir(work_dir)

    # Initialize the config
    init_stdout, init_stderr, init_returncode = run_helm_command(
        ["values-manager", "init", "--release", "test-release"]
    )
    assert init_returncode == 0
    assert Path("helm-values.json").exists()

    # Add a value config
    add_value_config_stdout, add_value_config_stderr, add_value_config_returncode = run_helm_command(
        [
            "values-manager",
            "add-value-config",
            "--path",
            "app.replicas",
            "--description",
            "Number of replicas",
            "--required",
        ]
    )
    assert add_value_config_returncode == 0

    # Try to set a value for a nonexistent deployment
    stdout, stderr, returncode = run_helm_command(
        ["values-manager", "set-value", "--path", "app.replicas", "--deployment", "nonexistent", "--value", "3"]
    )
    assert returncode == 1
    assert "Deployment 'nonexistent' not found" in stderr


def test_generate_help_command(plugin_install):
    """Test that the generate help command works and shows expected output."""
    stdout, stderr, returncode = run_helm_command(["values-manager", "generate", "--help"])
    assert returncode == 0, f"Failed to run help command: {stderr}"
    assert "Generate a values file for a specific deployment" in stdout, "Help text should include command description"
    assert "--deployment" in stdout, "Help text should include deployment option"
    assert "--output" in stdout, "Help text should include output option"


def test_generate_command(plugin_install, tmp_path):
    """Test that the generate command works correctly."""
    # Create a test directory
    test_dir = tmp_path / "test_generate_command"
    test_dir.mkdir()
    os.chdir(test_dir)

    # Initialize the plugin
    stdout, stderr, returncode = run_helm_command(["values-manager", "init", "--release", "test-release"])
    assert returncode == 0, f"Failed to initialize plugin: {stderr}"

    # Add a deployment
    stdout, stderr, returncode = run_helm_command(["values-manager", "add-deployment", "dev"])
    assert returncode == 0, f"Failed to add deployment: {stderr}"

    # Add value configs
    stdout, stderr, returncode = run_helm_command(
        ["values-manager", "add-value-config", "--path", "app.replicas", "--description", "Number of replicas"]
    )
    assert returncode == 0, f"Failed to add value config: {stderr}"

    stdout, stderr, returncode = run_helm_command(
        ["values-manager", "add-value-config", "--path", "app.image.repository", "--description", "Image repository"]
    )
    assert returncode == 0, f"Failed to add value config: {stderr}"

    stdout, stderr, returncode = run_helm_command(
        ["values-manager", "add-value-config", "--path", "app.image.tag", "--description", "Image tag"]
    )
    assert returncode == 0, f"Failed to add value config: {stderr}"

    # Set values
    stdout, stderr, returncode = run_helm_command(
        ["values-manager", "set-value", "--path", "app.replicas", "--deployment", "dev", "--value", "3"]
    )
    assert returncode == 0, f"Failed to set value: {stderr}"

    stdout, stderr, returncode = run_helm_command(
        ["values-manager", "set-value", "--path", "app.image.repository", "--deployment", "dev", "--value", "myapp"]
    )
    assert returncode == 0, f"Failed to set value: {stderr}"

    stdout, stderr, returncode = run_helm_command(
        ["values-manager", "set-value", "--path", "app.image.tag", "--deployment", "dev", "--value", "latest"]
    )
    assert returncode == 0, f"Failed to set value: {stderr}"

    # Generate values file
    stdout, stderr, returncode = run_helm_command(["values-manager", "generate", "--deployment", "dev"])
    assert returncode == 0, f"Failed to generate values file: {stderr}"
    assert "Successfully generated values file for deployment 'dev'" in stdout, f"Unexpected output: {stdout}"

    # Verify the values file exists
    values_file = test_dir / "dev.test-release.values.yaml"
    assert values_file.exists(), "Values file should exist"

    # Verify the content of the values file
    with open(values_file, "r") as f:
        values = yaml.safe_load(f)
        assert values["app"]["replicas"] == "3", "Values file should contain correct replicas value"
        assert values["app"]["image"]["repository"] == "myapp", "Values file should contain correct repository value"
        assert values["app"]["image"]["tag"] == "latest", "Values file should contain correct tag value"


def test_generate_with_output_path(plugin_install, tmp_path):
    """Test that the generate command works with a custom output path."""
    # Create a test directory
    test_dir = tmp_path / "test_generate_with_output_path"
    test_dir.mkdir()
    os.chdir(test_dir)

    # Create a custom output directory
    output_dir = test_dir / "output"
    output_dir.mkdir()

    # Initialize the plugin
    stdout, stderr, returncode = run_helm_command(["values-manager", "init", "--release", "test-release"])
    assert returncode == 0, f"Failed to initialize plugin: {stderr}"

    # Add a deployment
    stdout, stderr, returncode = run_helm_command(["values-manager", "add-deployment", "prod"])
    assert returncode == 0, f"Failed to add deployment: {stderr}"

    # Add value configs
    stdout, stderr, returncode = run_helm_command(
        ["values-manager", "add-value-config", "--path", "app.replicas", "--description", "Number of replicas"]
    )
    assert returncode == 0, f"Failed to add value config: {stderr}"

    # Set values
    stdout, stderr, returncode = run_helm_command(
        ["values-manager", "set-value", "--path", "app.replicas", "--deployment", "prod", "--value", "5"]
    )
    assert returncode == 0, f"Failed to set value: {stderr}"

    # Generate values file with custom output path
    stdout, stderr, returncode = run_helm_command(
        ["values-manager", "generate", "--deployment", "prod", "--output", str(output_dir)]
    )
    assert returncode == 0, f"Failed to generate values file: {stderr}"
    assert "Successfully generated values file for deployment 'prod'" in stdout, f"Unexpected output: {stdout}"

    # Verify the values file exists in the custom output directory
    values_file = output_dir / "prod.test-release.values.yaml"
    assert values_file.exists(), "Values file should exist in the custom output directory"

    # Verify the content of the values file
    with open(values_file, "r") as f:
        values = yaml.safe_load(f)
        assert values["app"]["replicas"] == "5", "Values file should contain correct replicas value"


def test_generate_nonexistent_deployment(plugin_install, tmp_path):
    """Test that generating values for a nonexistent deployment fails with the correct error message."""
    # Create a test directory
    test_dir = tmp_path / "test_generate_nonexistent_deployment"
    test_dir.mkdir()
    os.chdir(test_dir)

    # Initialize the plugin
    stdout, stderr, returncode = run_helm_command(["values-manager", "init", "--release", "test-release"])
    assert returncode == 0, f"Failed to initialize plugin: {stderr}"

    # Try to generate values for a nonexistent deployment
    stdout, stderr, returncode = run_helm_command(["values-manager", "generate", "--deployment", "nonexistent"])
    assert returncode != 0, "Expected command to fail but it succeeded"
    assert "Deployment 'nonexistent' not found" in stderr, f"Unexpected error message: {stderr}"


def test_generate_no_config(plugin_install, tmp_path):
    """Test that generating values without initializing fails with the correct error message."""
    # Create a test directory
    test_dir = tmp_path / "test_generate_no_config"
    test_dir.mkdir()
    os.chdir(test_dir)

    # Try to generate values without initializing
    stdout, stderr, returncode = run_helm_command(["values-manager", "generate", "--deployment", "dev"])
    assert returncode != 0, "Expected command to fail but it succeeded"
    assert "Configuration file helm-values.json not found" in stderr, f"Unexpected error message: {stderr}"


def test_generate_with_missing_required_value(plugin_install, tmp_path):
    """Test generate command with missing required values."""
    # Change to temp directory
    os.chdir(tmp_path)

    # Initialize the config
    stdout, stderr, returncode = run_helm_command(["values-manager", "init", "--release", "test-release"])
    assert returncode == 0, f"Failed to initialize config: {stderr}"

    # Add a deployment
    stdout, stderr, returncode = run_helm_command(["values-manager", "add-deployment", "dev"])
    assert returncode == 0, f"Failed to add deployment: {stderr}"

    # Add a required value config but don't set a value for it
    stdout, stderr, returncode = run_helm_command(
        [
            "values-manager",
            "add-value-config",
            "--path",
            "app.required",
            "--description",
            "Required value",
            "--required",
        ]
    )
    assert returncode == 0, f"Failed to add value config: {stderr}"

    # Try to generate values without setting the required value
    stdout, stderr, returncode = run_helm_command(["values-manager", "generate", "--deployment", "dev"])

    # Verify the command failed
    assert returncode != 0, "Expected command to fail but it succeeded"
    assert "Missing required values for deployment 'dev'" in stderr
    assert "app.required" in stderr
