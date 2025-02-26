"""Unit tests for the init command."""

import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from helm_values_manager.commands.init_command import InitCommand
from helm_values_manager.models.helm_values_config import HelmValuesConfig


@pytest.fixture
def init_command(tmp_path):
    """Fixture for InitCommand instance."""
    command = InitCommand()
    command.config_file = str(tmp_path / "helm-values.json")
    command.lock_file = str(tmp_path / ".helm-values.lock")
    return command


@pytest.fixture
def mock_config():
    """Fixture for mocked HelmValuesConfig."""
    config = MagicMock(spec=HelmValuesConfig)
    config.release = "test-release"
    config.version = "1.0"
    return config


def test_initialization(init_command, tmp_path):
    """Test InitCommand initialization."""
    assert isinstance(init_command, InitCommand)
    assert init_command.config_file == str(tmp_path / "helm-values.json")
    assert init_command.lock_file == str(tmp_path / ".helm-values.lock")


def test_run_creates_config(init_command):
    """Test that run creates a new config with release name."""
    with patch("builtins.open", mock_open()) as mock_file:
        result = init_command.run(release_name="test-release")
        assert result == "Successfully initialized helm-values configuration."

        # Verify config was saved with correct data
        handle = mock_file()
        written_json = "".join(call.args[0] for call in handle.write.call_args_list)
        written_data = json.loads(written_json)
        assert written_data["version"] == "1.0"
        assert written_data["release"] == "test-release"
        assert written_data["deployments"] == {}
        assert written_data["config"] == []


def test_run_with_existing_config(init_command):
    """Test that run fails if config file already exists."""
    with patch("os.path.exists", return_value=True):
        with pytest.raises(FileExistsError, match="Configuration file .* already exists"):
            init_command.run(release_name="test-release")


def test_run_with_invalid_release_name(init_command):
    """Test that run validates release name."""
    with pytest.raises(ValueError, match="Release name cannot be empty"):
        init_command.run(release_name="")

    with pytest.raises(ValueError, match="Release name cannot be empty"):
        init_command.run(release_name=None)
