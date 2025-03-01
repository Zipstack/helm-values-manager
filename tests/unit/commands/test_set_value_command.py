"""Tests for the set-value command."""

import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from helm_values_manager.commands.set_value_command import SetValueCommand
from helm_values_manager.models.constants import NO_AUTH, NO_BACKEND
from helm_values_manager.models.helm_values_config import Deployment, HelmValuesConfig


@pytest.fixture
def mock_config_file():
    """Create a mock configuration file with a path already added."""
    config = HelmValuesConfig()
    config.version = "1.0"
    config.release = "test-release"
    config.add_config_path(path="app.replicas", description="Number of app replicas", required=True)

    # Add deployment directly to the deployments dictionary
    deployment = Deployment(
        name="dev",
        backend=NO_BACKEND,
        auth={"type": NO_AUTH},
        backend_config={},
    )
    config.deployments["dev"] = deployment

    return json.dumps(config.to_dict())


@pytest.fixture
def command():
    """Create an instance of the SetValueCommand."""
    return SetValueCommand()


def test_set_value_success(command, mock_config_file):
    """Test successful setting of a value."""
    path = "app.replicas"
    deployment = "dev"
    value = "3"

    # Mock file operations
    with (
        patch("builtins.open", mock_open(read_data=mock_config_file)),
        patch("os.path.exists", return_value=True),
        patch("fcntl.flock"),
        patch("os.open"),
        patch("os.close"),
    ):
        result = command.execute(path=path, environment=deployment, value=value)

    assert f"Successfully set value for path '{path}' in deployment '{deployment}'" in result


def test_set_value_path_not_found(command, mock_config_file):
    """Test setting a value for a path that doesn't exist."""
    path = "nonexistent.path"
    deployment = "dev"
    value = "3"

    # Mock file operations
    with (
        patch("builtins.open", mock_open(read_data=mock_config_file)),
        patch("os.path.exists", return_value=True),
        patch("fcntl.flock"),
        patch("os.open"),
        patch("os.close"),
    ):
        with pytest.raises(KeyError, match=f"Path {path} not found"):
            command.execute(path=path, environment=deployment, value=value)


def test_set_value_deployment_not_found(command, mock_config_file):
    """Test setting a value for a deployment that doesn't exist."""
    path = "app.replicas"
    deployment = "nonexistent"
    value = "3"

    # Mock file operations
    with (
        patch("builtins.open", mock_open(read_data=mock_config_file)),
        patch("os.path.exists", return_value=True),
        patch("fcntl.flock"),
        patch("os.open"),
        patch("os.close"),
    ):
        with pytest.raises(KeyError, match=f"Deployment '{deployment}' not found"):
            command.execute(path=path, environment=deployment, value=value)


def test_set_value_empty_path(command, mock_config_file):
    """Test setting a value with an empty path."""
    path = ""
    deployment = "dev"
    value = "3"

    # Mock file operations
    with (
        patch("builtins.open", mock_open(read_data=mock_config_file)),
        patch("os.path.exists", return_value=True),
        patch("fcntl.flock"),
        patch("os.open"),
        patch("os.close"),
    ):
        with pytest.raises(ValueError, match="Path cannot be empty"):
            command.execute(path=path, environment=deployment, value=value)


def test_set_value_empty_deployment(command, mock_config_file):
    """Test setting a value with an empty deployment."""
    path = "app.replicas"
    deployment = ""
    value = "3"

    # Mock file operations
    with (
        patch("builtins.open", mock_open(read_data=mock_config_file)),
        patch("os.path.exists", return_value=True),
        patch("fcntl.flock"),
        patch("os.open"),
        patch("os.close"),
    ):
        with pytest.raises(ValueError, match="Deployment cannot be empty"):
            command.execute(path=path, environment=deployment, value=value)


def test_set_value_none_config(command):
    """Test setting a value when config is None."""
    # Mock the load_config method to return None
    with patch.object(command, "load_config", return_value=None):
        with pytest.raises(ValueError, match="Configuration not loaded"):
            command.execute(path="app.replicas", environment="dev", value="3")


def test_set_value_general_error():
    """Test that general errors are properly handled."""
    command = SetValueCommand()
    config = MagicMock()
    config.deployments = {"dev": MagicMock()}  # Mock deployment exists
    config.set_value.side_effect = Exception("Unexpected error")

    with pytest.raises(Exception) as exc_info:
        command.run(config, path="app.replicas", environment="dev", value="3")

    assert str(exc_info.value) == "Unexpected error"
