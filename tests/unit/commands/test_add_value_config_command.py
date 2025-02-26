"""Tests for the add-value-config command."""

import json
from unittest.mock import mock_open, patch

import pytest

from helm_values_manager.commands.add_value_config_command import AddValueConfigCommand
from helm_values_manager.models.helm_values_config import HelmValuesConfig


@pytest.fixture
def mock_config_file():
    """Create a mock configuration file."""
    config = HelmValuesConfig()
    config.version = "1.0"
    config.release = "test-release"
    return json.dumps(config.to_dict())


@pytest.fixture
def command():
    """Create an instance of the AddValueConfigCommand."""
    return AddValueConfigCommand()


def test_add_value_config_success(command, mock_config_file):
    """Test successful addition of a value configuration."""
    path = "app.replicas"
    description = "Number of application replicas"
    required = True
    sensitive = False

    # Mock file operations
    with (
        patch("builtins.open", mock_open(read_data=mock_config_file)),
        patch("os.path.exists", return_value=True),
        patch("fcntl.flock"),
        patch("os.open"),
        patch("os.close"),
    ):

        result = command.execute(path=path, description=description, required=required, sensitive=sensitive)

    assert "Successfully added value config 'app.replicas'" in result


def test_add_value_config_empty_path(command, mock_config_file):
    """Test adding a value configuration with an empty path."""
    # Mock file operations
    with (
        patch("builtins.open", mock_open(read_data=mock_config_file)),
        patch("os.path.exists", return_value=True),
        patch("fcntl.flock"),
        patch("os.open"),
        patch("os.close"),
    ):

        with pytest.raises(ValueError, match="Path cannot be empty"):
            command.execute(path="")


def test_add_value_config_duplicate_path(command, mock_config_file):
    """Test adding a duplicate value configuration path."""
    path = "app.replicas"

    # Create a config with the path already added
    config = HelmValuesConfig.from_dict(json.loads(mock_config_file))
    config.add_config_path(path, description="Existing config")
    updated_mock_config = json.dumps(config.to_dict())

    # Mock file operations
    with (
        patch("builtins.open", mock_open(read_data=updated_mock_config)),
        patch("os.path.exists", return_value=True),
        patch("fcntl.flock"),
        patch("os.open"),
        patch("os.close"),
    ):

        with pytest.raises(ValueError, match=f"Path {path} already exists"):
            command.execute(path=path, description="New description")


def test_add_value_config_none_config(command):
    """Test adding a value configuration when config is None."""
    # Test the case where config is None
    with pytest.raises(ValueError, match="Configuration not loaded"):
        command.run(config=None, path="app.replicas", description="Test description")
