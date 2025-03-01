"""Tests for the generate command."""

import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from helm_values_manager.commands.generate_command import GenerateCommand
from helm_values_manager.models.constants import NO_AUTH, NO_BACKEND
from helm_values_manager.models.helm_values_config import Deployment, HelmValuesConfig


@pytest.fixture
def mock_config_file():
    """Create a mock configuration file with paths and values."""
    config = HelmValuesConfig()
    config.version = "1.0"
    config.release = "test-release"

    # Add config paths
    config.add_config_path(path="app.replicas", description="Number of app replicas", required=True)
    config.add_config_path(path="app.image.repository", description="Container image repository", required=True)
    config.add_config_path(path="app.image.tag", description="Container image tag", required=True)
    config.add_config_path(path="app.resources.limits.cpu", description="CPU limit", required=False)
    config.add_config_path(path="app.resources.limits.memory", description="Memory limit", required=False)

    # Add deployments
    dev_deployment = Deployment(
        name="dev",
        backend=NO_BACKEND,
        auth={"type": NO_AUTH},
        backend_config={},
    )
    config.deployments["dev"] = dev_deployment

    prod_deployment = Deployment(
        name="prod",
        backend=NO_BACKEND,
        auth={"type": NO_AUTH},
        backend_config={},
    )
    config.deployments["prod"] = prod_deployment

    # Set values for dev environment
    config.set_value(path="app.replicas", environment="dev", value="1")
    config.set_value(path="app.image.repository", environment="dev", value="myapp")
    config.set_value(path="app.image.tag", environment="dev", value="latest")
    config.set_value(path="app.resources.limits.cpu", environment="dev", value="100m")
    config.set_value(path="app.resources.limits.memory", environment="dev", value="128Mi")

    # Set values for prod environment
    config.set_value(path="app.replicas", environment="prod", value="3")
    config.set_value(path="app.image.repository", environment="prod", value="myapp")
    config.set_value(path="app.image.tag", environment="prod", value="stable")
    config.set_value(path="app.resources.limits.cpu", environment="prod", value="500m")
    config.set_value(path="app.resources.limits.memory", environment="prod", value="512Mi")

    return json.dumps(config.to_dict())


@pytest.fixture
def command():
    """Create an instance of the GenerateCommand."""
    return GenerateCommand()


def test_generate_success(command, mock_config_file, tmp_path):
    """Test successful generation of values file."""
    deployment = "dev"
    expected_filename = f"{deployment}.test-release.values.yaml"

    # Create a mock for open that tracks file writes
    mock_open_instance = mock_open(read_data=mock_config_file)

    # Mock file operations
    with (
        patch("builtins.open", mock_open_instance),
        patch("os.path.exists", return_value=True),
        patch("fcntl.flock"),
        patch("os.open"),
        patch("os.close"),
    ):
        # Use a real file for the output
        with patch("yaml.dump") as mock_yaml_dump:
            # Execute the command
            result = command.execute(deployment=deployment, output_path=str(tmp_path))

            # Verify the result message
            assert f"Successfully generated values file for deployment '{deployment}'" in result
            assert expected_filename in result

            # Verify yaml.dump was called with the correct data and file
            mock_yaml_dump.assert_called_once()
            dumped_data = mock_yaml_dump.call_args[0][0]

            # Check that the data structure is correct
            assert "app" in dumped_data
            assert dumped_data["app"]["replicas"] == "1"
            assert dumped_data["app"]["image"]["repository"] == "myapp"
            assert dumped_data["app"]["image"]["tag"] == "latest"
            assert dumped_data["app"]["resources"]["limits"]["cpu"] == "100m"
            assert dumped_data["app"]["resources"]["limits"]["memory"] == "128Mi"

            # Verify the file path in the open call
            # Find calls to open with write mode
            write_calls = [call for call in mock_open_instance.call_args_list if len(call[0]) > 1 and "w" in call[0][1]]
            assert len(write_calls) > 0, "No calls to open() with write mode"

            # Verify the filename in the open call
            filename_arg = write_calls[-1][0][0]
            assert (
                expected_filename in filename_arg
            ), f"Expected filename containing {expected_filename}, got {filename_arg}"
            assert str(tmp_path) in filename_arg, f"Expected path containing {tmp_path}, got {filename_arg}"


def test_generate_with_output_path(command, mock_config_file, tmp_path):
    """Test generating values file with a custom output path."""
    deployment = "prod"
    output_path = str(tmp_path / "custom-dir")
    expected_filename = f"{deployment}.test-release.values.yaml"

    # Create a mock for open that tracks file writes
    mock_open_instance = mock_open(read_data=mock_config_file)

    # Mock file operations
    with (
        patch("builtins.open", mock_open_instance),
        patch("os.path.exists", side_effect=lambda path: path != output_path),  # Directory doesn't exist
        patch("os.makedirs") as mock_makedirs,
        patch("fcntl.flock"),
        patch("os.open"),
        patch("os.close"),
    ):
        # Mock the yaml.dump to capture the output
        with patch("yaml.dump") as mock_yaml_dump:
            # Execute the command
            result = command.execute(deployment=deployment, output_path=output_path)

            # Verify the result
            assert f"Successfully generated values file for deployment '{deployment}'" in result
            assert output_path in result

            # Verify directory creation
            mock_makedirs.assert_called_once_with(output_path)

            # Verify yaml.dump was called with the correct data
            mock_yaml_dump.assert_called_once()
            dumped_data = mock_yaml_dump.call_args[0][0]

            # Check that the data structure is correct
            assert "app" in dumped_data
            assert dumped_data["app"]["replicas"] == "3"
            assert dumped_data["app"]["image"]["tag"] == "stable"

            # Verify the file path in the open call
            # Find calls to open with write mode
            write_calls = [call for call in mock_open_instance.call_args_list if len(call[0]) > 1 and "w" in call[0][1]]
            assert len(write_calls) > 0, "No calls to open() with write mode"

            # Verify the filename in the open call
            filename_arg = write_calls[-1][0][0]
            assert (
                expected_filename in filename_arg
            ), f"Expected filename containing {expected_filename}, got {filename_arg}"
            assert output_path in filename_arg, f"Expected path containing {output_path}, got {filename_arg}"


def test_generate_missing_deployment(command, mock_config_file):
    """Test generating values file with a non-existent deployment."""
    deployment = "staging"

    # Mock file operations
    with (
        patch("builtins.open", mock_open(read_data=mock_config_file)),
        patch("os.path.exists", return_value=True),
        patch("fcntl.flock"),
        patch("os.open"),
        patch("os.close"),
    ):
        # Execute the command and expect an error
        with pytest.raises(KeyError, match=f"Deployment '{deployment}' not found"):
            command.execute(deployment=deployment)


def test_generate_empty_deployment(command, mock_config_file):
    """Test generating values file with an empty deployment."""
    deployment = ""

    # Mock file operations
    with (
        patch("builtins.open", mock_open(read_data=mock_config_file)),
        patch("os.path.exists", return_value=True),
        patch("fcntl.flock"),
        patch("os.open"),
        patch("os.close"),
    ):
        # Execute the command and expect an error
        with pytest.raises(ValueError, match="Deployment cannot be empty"):
            command.execute(deployment=deployment)


def test_generate_no_config(command):
    """Test generating values file when config is None."""
    deployment = "dev"

    # Mock file operations to make load_config return None
    with (
        patch.object(command, "load_config", side_effect=FileNotFoundError("Config file not found")),
        patch("fcntl.flock"),
        patch("os.open"),
        patch("os.close"),
    ):
        # Execute the command and expect an error
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            command.execute(deployment=deployment)


def test_generate_with_none_config(command):
    """Test generating values file when config is None in the run method."""
    deployment = "dev"

    # Mock load_config to return None instead of raising an exception
    with (
        patch.object(command, "load_config", return_value=None),
        patch("fcntl.flock"),
        patch("os.open"),
        patch("os.close"),
    ):
        # Execute the command and expect a ValueError
        with pytest.raises(ValueError, match="Configuration not loaded"):
            command.execute(deployment=deployment)


def test_generate_with_none_value(command, mock_config_file):
    """Test generating values file when a value is None."""
    deployment = "dev"
    expected_filename = f"{deployment}.test-release.values.yaml"
    expected_filepath = f"./{expected_filename}"  # Account for ./ prefix

    # Create a mock config with a None value
    config = HelmValuesConfig()
    config.version = "1.0"
    config.release = "test-release"

    # Add config paths
    config.add_config_path(path="app.replicas", description="Number of app replicas", required=True)
    config.add_config_path(path="app.image.repository", description="Container image repository", required=True)
    config.add_config_path(
        path="app.image.tag", description="Container image tag", required=False
    )  # Changed to not required

    # Add deployment
    dev_deployment = Deployment(
        name="dev",
        backend=NO_BACKEND,
        auth={"type": NO_AUTH},
        backend_config={},
    )
    config.deployments["dev"] = dev_deployment

    # Set some values, but leave one as None
    config.set_value(path="app.replicas", environment="dev", value="1")
    config.set_value(path="app.image.repository", environment="dev", value="myapp")
    # app.image.tag is intentionally not set, so it will be None

    # Mock file operations
    with (
        patch.object(command, "load_config", return_value=config),
        patch("os.path.exists", return_value=True),
        patch("fcntl.flock"),
        patch("os.open"),
        patch("os.close"),
    ):
        # Use a mock for the output file
        with patch("builtins.open", mock_open()) as mock_file, patch("yaml.dump") as mock_yaml_dump:
            # Execute the command
            result = command.execute(deployment=deployment)

            # Verify the result message
            assert f"Successfully generated values file for deployment '{deployment}'" in result
            assert expected_filename in result

            # Verify file operations
            mock_file.assert_called_once_with(expected_filepath, "w", encoding="utf-8")

            # Verify yaml.dump was called with the correct data
            mock_yaml_dump.assert_called_once()

            # Verify the data structure is correct and the None value was skipped
            dumped_data = mock_yaml_dump.call_args[0][0]

            # Check that the data structure is correct and the None value was skipped
            assert "app" in dumped_data
            assert dumped_data["app"]["replicas"] == "1"
            assert dumped_data["app"]["image"]["repository"] == "myapp"
            assert "tag" not in dumped_data["app"]["image"], "None value should be skipped"


def test_generate_with_missing_required_value():
    """Test generate command with a missing required value."""
    # Create a mock config
    config = MagicMock(spec=HelmValuesConfig)

    # Setup the deployment
    deployment = "dev"
    config.deployments = {deployment: MagicMock()}
    config.release = "test-release"

    # Setup paths with one required and one optional
    path_data_required = MagicMock()
    path_data_required._metadata = MagicMock()
    path_data_required._metadata.required = True

    path_data_optional = MagicMock()
    path_data_optional._metadata = MagicMock()
    path_data_optional._metadata.required = False

    # Setup the path map
    config._path_map = {"app.required": path_data_required, "app.optional": path_data_optional}

    # Setup get_value to return None for required path and a value for optional path
    def mock_get_value(path, env, resolve=False):
        if path == "app.required":
            return None
        return "optional-value"

    config.get_value.side_effect = mock_get_value

    # Create command and mock the load_config method to return our mock config
    command = GenerateCommand()
    command.load_config = MagicMock(return_value=config)

    # Execute command and expect ValueError
    with pytest.raises(ValueError) as excinfo:
        command.execute(deployment=deployment, output_path=".")

    # Verify the error message
    assert "Missing required values" in str(excinfo.value)
    assert "app.required" in str(excinfo.value)
    assert "app.optional" not in str(excinfo.value)
