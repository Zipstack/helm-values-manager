"""Unit tests for the add-deployment command."""

import json
import os

import pytest

from helm_values_manager.commands.add_deployment_command import AddDeploymentCommand
from helm_values_manager.models.constants import NO_AUTH, NO_BACKEND


@pytest.fixture
def mock_config_file(tmp_path):
    """Create a mock config file for testing."""
    config_path = tmp_path / "helm-values.json"
    config_data = {"version": "1.0", "release": "test-release", "deployments": {}, "config": []}
    config_path.write_text(json.dumps(config_data))
    return str(config_path)


@pytest.fixture
def command(mock_config_file):
    """Create a command instance with a mock config file."""
    cmd = AddDeploymentCommand()
    cmd.config_file = mock_config_file
    cmd.lock_file = str(os.path.dirname(mock_config_file)) + "/.helm-values.lock"
    return cmd


def test_add_deployment_basic(command):
    """Test adding a basic deployment configuration."""
    # Arrange
    kwargs = {
        "name": "dev",
    }

    # Act
    result = command.execute(**kwargs)

    # Assert
    assert "Successfully added deployment 'dev'" in result

    # Verify the config file was updated correctly
    with open(command.config_file, "r") as f:
        config_data = json.load(f)

    assert "dev" in config_data["deployments"]
    assert config_data["deployments"]["dev"]["backend"] == NO_BACKEND
    assert config_data["deployments"]["dev"]["auth"]["type"] == NO_AUTH
    assert config_data["deployments"]["dev"]["backend_config"] == {}


def test_add_deployment_missing_name(command):
    """Test that an error is raised when name is missing."""
    # Arrange
    kwargs = {}

    # Act & Assert
    with pytest.raises(ValueError, match="Deployment name cannot be empty"):
        command.execute(**kwargs)


def test_add_deployment_duplicate(command):
    """Test that an error is raised when adding a duplicate deployment."""
    # Arrange
    kwargs = {
        "name": "dev",
    }

    # Add the deployment first
    command.execute(**kwargs)

    # Act & Assert - Try to add it again
    with pytest.raises(ValueError, match="Deployment 'dev' already exists"):
        command.execute(**kwargs)


def test_add_deployment_no_config():
    """Test that an error is raised when config is None."""
    # Arrange
    command = AddDeploymentCommand()
    command.config = None

    # Act & Assert
    with pytest.raises(ValueError, match="Configuration not loaded"):
        command.run(name="dev")
