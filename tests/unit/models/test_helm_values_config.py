"""Test suite for HelmValuesConfig class."""

import pytest

from helm_values_manager.models.helm_values_config import HelmValuesConfig
from helm_values_manager.models.path_data import PathData


def test_helm_values_config_initialization():
    """Test initialization of HelmValuesConfig."""
    config = HelmValuesConfig()
    assert config.deployments == {}
    assert config._path_map == {}


def test_add_config_path():
    """Test adding a new configuration path."""
    config = HelmValuesConfig()
    path = "app.config.key1"
    description = "Test config"

    config.add_config_path(path, description=description, required=True, sensitive=False)

    assert path in config._path_map
    path_data = config._path_map[path]
    assert isinstance(path_data, PathData)
    assert path_data.path == path
    assert path_data.metadata.description == description
    assert path_data.metadata.required is True
    assert path_data.metadata.sensitive is False


def test_add_duplicate_path():
    """Test adding a duplicate path."""
    config = HelmValuesConfig()
    path = "app.config.key1"

    config.add_config_path(path, description="Test config")
    with pytest.raises(ValueError, match=f"Path {path} already exists"):
        config.add_config_path(path, description="Another config")


def test_set_and_get_value():
    """Test setting and getting a value."""
    config = HelmValuesConfig()
    path = "app.config.key1"
    value = "test-value"
    environment = "dev"

    config.add_config_path(path, description="Test config")
    config.set_value(path, environment, value)

    assert config.get_value(path, environment) == value


def test_get_value_nonexistent_path():
    """Test getting a value for a non-existent path."""
    config = HelmValuesConfig()
    with pytest.raises(KeyError, match=r"Path app\.config\.key1 not found"):
        config.get_value("app.config.key1", "dev")


def test_get_value_nonexistent_environment():
    """Test getting a value for a non-existent environment."""
    config = HelmValuesConfig()
    path = "app.config.key1"
    config.add_config_path(path, description="Test config", required=True, sensitive=False)
    with pytest.raises(ValueError, match=f"No value found for path {path} in environment dev"):
        config.get_value(path, "dev")


def test_get_value_nonexistent_value():
    """Test getting a value that doesn't exist."""
    config = HelmValuesConfig()
    path = "app.config.key1"
    config.add_config_path(path, description="Test config")
    with pytest.raises(ValueError, match=f"No value found for path {path} in environment dev"):
        config.get_value(path, "dev")


def test_set_value_without_path():
    """Test setting a value without first adding its path."""
    config = HelmValuesConfig()
    with pytest.raises(KeyError, match=r"Path app\.config\.key1 not found"):
        config.set_value("app.config.key1", "dev", "test-value")


def test_to_dict_from_dict():
    """Test serialization and deserialization."""
    config_data = {
        "version": "1.0",
        "release": "test-release",
        "deployments": {
            "prod": {
                "backend": "aws",
                "auth": {"type": "env", "env_prefix": "AWS_"},
                "backend_config": {"region": "us-west-2"},
            }
        },
        "config": [
            {
                "path": "app.config.key1",
                "description": "Test config",
                "required": True,
                "sensitive": True,
                "values": {"default": "test-value"},
            }
        ],
    }

    # Test from_dict
    config = HelmValuesConfig.from_dict(config_data)
    assert config.release == "test-release"
    assert config.version == "1.0"
    assert len(config.deployments) == 1
    assert len(config._path_map) == 1

    # Verify deployment data
    deployment = config.deployments["prod"]
    assert deployment.backend == "aws"
    assert deployment.auth == {"type": "env", "env_prefix": "AWS_"}
    assert deployment.backend_config == {"region": "us-west-2"}

    # Verify config data
    path_data = config._path_map["app.config.key1"]
    assert path_data.path == "app.config.key1"
    assert path_data.metadata.description == "Test config"
    assert path_data.metadata.required is True
    assert path_data.metadata.sensitive is True

    # Test to_dict
    config_dict = config.to_dict()
    assert config_dict["version"] == "1.0"
    assert config_dict["release"] == "test-release"
    assert config_dict["deployments"] == {
        "prod": {
            "backend": "aws",
            "auth": {"type": "env", "env_prefix": "AWS_"},
            "backend_config": {"region": "us-west-2"},
        }
    }
    assert len(config_dict["config"]) == 1

    config_item = config_dict["config"][0]
    assert config_item["path"] == "app.config.key1"
    assert config_item["description"] == "Test config"
    assert config_item["required"] is True
    assert config_item["sensitive"] is True
    assert config_item["values"] == {"default": "test-value"}


def test_validate():
    """Test validation of required paths."""
    config = HelmValuesConfig()
    path = "app.config.key1"
    config.add_config_path(path, description="Test config", required=True, sensitive=False)

    # Should not raise error since path_data.validate() handles validation
    config.validate()
