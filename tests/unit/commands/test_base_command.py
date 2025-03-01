"""Unit tests for the BaseCommand class."""

import json
import os
from unittest.mock import MagicMock, mock_open, patch

import pytest
from jsonschema.exceptions import ValidationError

from helm_values_manager.commands.base_command import BaseCommand
from helm_values_manager.models.helm_values_config import HelmValuesConfig


@pytest.fixture
def temp_lock_file(tmp_path):
    """Fixture for temporary lock file."""
    lock_file = tmp_path / ".helm-values.lock"
    return str(lock_file)


@pytest.fixture
def base_command(temp_lock_file):
    """Fixture for BaseCommand instance with mocked lock file."""
    command = BaseCommand()
    command.lock_file = temp_lock_file
    return command


@pytest.fixture
def mock_config():
    """Fixture for mocked HelmValuesConfig."""
    return MagicMock(spec=HelmValuesConfig)


@pytest.fixture
def valid_config():
    """Fixture for valid configuration data."""
    return {"version": "1.0", "release": "test", "deployments": {}, "config": []}


def test_initialization(base_command, temp_lock_file):
    """Test BaseCommand initialization."""
    assert base_command.config_file == "helm-values.json"
    assert base_command.lock_file == temp_lock_file
    assert base_command._lock_fd is None


def test_load_config_file_not_found(base_command):
    """Test load_config when file doesn't exist."""
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError, match="Configuration file .* not found"):
            base_command._load_config_file()


def test_load_config_file_invalid_json(base_command):
    """Test load_config with invalid JSON."""
    with patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data="invalid json")):
        with pytest.raises(json.JSONDecodeError):
            base_command._load_config_file()


def test_load_config_file_success(base_command, valid_config):
    """Test successful config file loading."""
    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(valid_config))),
    ):
        data = base_command._load_config_file()
        assert data == valid_config


def test_load_config_invalid_format(base_command):
    """Test load_config with invalid configuration format."""
    invalid_config = {"version": "1.0"}  # Missing required fields
    with patch.object(base_command, "_load_config_file", return_value=invalid_config):
        with pytest.raises(ValidationError, match="'release' is a required property"):
            base_command.load_config()


def test_load_config_success(base_command, valid_config):
    """Test successful config loading."""
    with patch.object(base_command, "_load_config_file", return_value=valid_config):
        config = base_command.load_config()
        assert isinstance(config, HelmValuesConfig)
        assert config.version == valid_config["version"]
        assert config.release == valid_config["release"]


def test_run_not_implemented(base_command):
    """Test that run raises NotImplementedError."""
    with pytest.raises(NotImplementedError, match="Subclasses must implement run()"):
        base_command.run(MagicMock())


def test_acquire_and_release_lock(base_command):
    """Test lock acquisition and release."""
    with patch("helm_values_manager.commands.base_command.fcntl") as mock_fcntl:
        base_command.acquire_lock()
        mock_fcntl.flock.assert_called_once()

        base_command.release_lock()
        assert mock_fcntl.flock.call_count == 2


def test_acquire_lock_failure(base_command):
    """Test lock acquisition when another process holds the lock."""
    with (
        patch("helm_values_manager.commands.base_command.fcntl") as mock_fcntl,
        patch("os.open", return_value=123),
        patch("os.close"),
    ):
        mock_fcntl.flock.side_effect = IOError("Resource temporarily unavailable")

        with pytest.raises(IOError, match="Unable to acquire lock. Another command may be running."):
            base_command.acquire_lock()

        # Verify the file descriptor was closed
        os.close.assert_called_once_with(123)
        assert base_command._lock_fd is None


def test_release_lock_without_lock(base_command):
    """Test release_lock when no lock is held."""
    # Release without acquiring - should not raise any error
    base_command.release_lock()
    assert base_command._lock_fd is None


def test_execute_success(base_command, valid_config):
    """Test successful command execution flow."""
    expected_result = "success"
    base_command.run = MagicMock(return_value=expected_result)

    with (
        patch.object(base_command, "_load_config_file", return_value=valid_config),
        patch("helm_values_manager.commands.base_command.fcntl"),
    ):
        result = base_command.execute()
        assert result == expected_result
        # Check that run was called with a config object and empty kwargs
        assert base_command.run.call_count == 1
        call_args = base_command.run.call_args
        assert isinstance(call_args.kwargs["config"], HelmValuesConfig)
        assert len(call_args.args) == 0


def test_execute_ensures_lock_release_on_error(base_command, valid_config):
    """Test that lock is released even if an error occurs."""
    base_command.run = MagicMock(side_effect=ValueError("Test error"))

    with (
        patch.object(base_command, "_load_config_file", return_value=valid_config),
        patch("helm_values_manager.commands.base_command.fcntl") as mock_fcntl,
    ):
        with pytest.raises(ValueError, match="Test error"):
            base_command.execute()

        assert mock_fcntl.flock.call_count == 2  # Lock acquired and released


def test_save_config_success(base_command):
    """Test successful config save."""
    config = HelmValuesConfig()
    config.version = "1.0"
    config.release = "test"

    # Mock the validate method
    config.validate = MagicMock()

    with patch("builtins.open", mock_open()) as mock_file:
        base_command.save_config(config)

        # Verify validate was called
        config.validate.assert_called_once()

        mock_file.assert_called_once_with(base_command.config_file, "w", encoding="utf-8")
        handle = mock_file()

        # Verify the written data
        written_json = "".join(call.args[0] for call in handle.write.call_args_list)
        written_data = json.loads(written_json)
        assert written_data["version"] == "1.0"
        assert written_data["release"] == "test"


def test_save_config_io_error(base_command):
    """Test IO error handling when saving config."""
    config = HelmValuesConfig()
    config.version = "1.0"
    config.release = "test"

    # Mock the validate method
    config.validate = MagicMock()

    # Simulate an IO error
    mock_file = mock_open()
    mock_file.side_effect = IOError("Test IO Error")

    with patch("builtins.open", mock_file):
        with pytest.raises(IOError) as excinfo:
            base_command.save_config(config)

        assert "Test IO Error" in str(excinfo.value)

        # Verify validate was called
        config.validate.assert_called_once()


def test_save_config_validates_schema(base_command):
    """Test that save_config validates the schema before saving."""
    # Create a mock config
    config = MagicMock(spec=HelmValuesConfig)

    # Make validate method raise an error
    config.validate.side_effect = ValueError("Schema validation failed")

    # Try to save the config
    with pytest.raises(ValueError, match="Schema validation failed"):
        base_command.save_config(config)

    # Verify that validate was called
    config.validate.assert_called_once()


def test_save_config_with_empty_description(base_command, tmp_path):
    """Test that save_config handles empty description correctly."""
    # Create a real config
    config = HelmValuesConfig()
    config.release = "test"

    # Add a config path with empty description (default)
    config.add_config_path("test.path")

    # Set a temporary config file
    temp_file = tmp_path / "test_config.json"
    base_command.config_file = str(temp_file)

    # Save the config
    base_command.save_config(config)

    # Read the saved file
    with open(temp_file, "r") as f:
        data = json.load(f)

    # Verify that description is an empty string
    assert data["config"][0]["description"] == ""
    assert isinstance(data["config"][0]["description"], str)
