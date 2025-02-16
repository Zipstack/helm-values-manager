"""Test suite for HelmValuesConfig class."""

import pytest

from helm_values_manager.models.helm_values_config import HelmValuesConfig
from helm_values_manager.models.path_data import PathData


def test_helm_values_config_initialization():
    """Test initialization of HelmValuesConfig."""
    config = HelmValuesConfig()
    assert config.deployments == {}
    assert config._path_map == {}
    assert config.default_environment == "default"


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
    assert path_data.metadata["description"] == description
    assert path_data.metadata["required"] is True
    assert path_data.metadata["sensitive"] is False


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
    config = HelmValuesConfig()
    path = "app.config.key1"
    description = "Test config"
    value = "test-value"
    environment = "dev"

    config.add_config_path(path, description=description, required=True, sensitive=False)
    config.set_value(path, environment, value)

    config_dict = config.to_dict()
    assert config_dict["version"] == "1.0"
    assert config_dict["deployments"] == {}
    assert len(config_dict["config"]) == 1

    config_item = config_dict["config"][0]
    assert config_item["path"] == path
    assert config_item["description"] == description
    assert config_item["required"] is True
    assert config_item["sensitive"] is False
    assert config_item["values"] == {environment: value}

    # Test deserialization
    new_config = HelmValuesConfig.from_dict(config_dict)
    assert new_config.get_value(path, environment) == value
    assert new_config._path_map[path].metadata["description"] == description
    assert new_config._path_map[path].metadata["required"] is True
    assert new_config._path_map[path].metadata["sensitive"] is False


def test_validate():
    """Test validation of required paths."""
    config = HelmValuesConfig()
    path = "app.config.key1"
    config.add_config_path(path, description="Test config", required=True, sensitive=False)

    # Should not raise error since path_data.validate() handles validation
    config.validate()
