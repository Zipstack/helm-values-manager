"""Test suite for HelmValuesConfig class."""

import jsonschema
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
    assert config.get_value(path, "dev") is None


def test_get_value_nonexistent_value():
    """Test getting a value that doesn't exist."""
    config = HelmValuesConfig()
    path = "app.config.key1"
    config.add_config_path(path, description="Test config")
    assert config.get_value(path, "dev") is None


def test_get_value_returns_none():
    """Test getting a value when value_obj.get() returns None."""
    config = HelmValuesConfig()
    path = "app.config.key1"
    environment = "dev"

    # Add path and set None value
    config.add_config_path(path, description="Test config")
    config.set_value(path, environment, None)

    # Verify that get_value returns None
    assert config.get_value(path, environment) is None


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
    config.release = "test-release"  # Set release name
    path = "app.config.key1"
    config.add_config_path(path, description="Test config", required=True, sensitive=False)

    # Should not raise error since path_data.validate() handles validation
    config.validate()


def test_validate_with_schema():
    """Test validation including schema validation."""
    # Create config with invalid version
    config = HelmValuesConfig()
    config.release = "test-release"  # Set release name
    config.version = "invalid"  # Version must match pattern in schema

    # Should raise ValidationError due to schema validation
    with pytest.raises(jsonschema.exceptions.ValidationError, match=r"'invalid' is not one of"):
        config.validate()

    # Fix version and test valid case
    config.version = "1.0"
    config.validate()  # Should not raise error


def test_validate_without_release():
    """Test validation fails when release name is not set."""
    config = HelmValuesConfig()
    with pytest.raises(ValueError, match="Release name is required"):
        config.validate()


def test_release_name_validation():
    """
    Test that release names are properly validated.

    Release names must match the following pattern: ^[a-z0-9-]{1,53}$.
    """
    # Valid cases
    valid_names = [
        "my-release",
        "release123",
        "a-b-c-123",
        "a" * 53,  # max length
    ]
    for name in valid_names:
        config = {"version": "1.0", "release": name, "deployments": {}, "config": []}
        HelmValuesConfig._validate_schema(config)  # Should not raise

    # Invalid cases
    invalid_names = [
        "UPPERCASE",  # uppercase not allowed
        "my_release",  # underscore not allowed
        "my.release",  # dot not allowed
        "-starts-with-hyphen",  # cannot start with hyphen
        "ends-with-hyphen-",  # cannot end with hyphen
        "a" * 54,  # too long
        "",  # empty string
    ]
    for name in invalid_names:
        config = {"version": "1.0", "release": name, "deployments": {}, "config": []}
        with pytest.raises(jsonschema.exceptions.ValidationError):
            HelmValuesConfig._validate_schema(config)


def test_deployment_name_validation():
    """
    Test that deployment names are properly validated.

    Deployment names must match the following pattern: ^[a-z0-9-]{1,53}$.
    """
    # Valid cases
    valid_config = {
        "version": "1.0",
        "release": "test-release",
        "deployments": {
            "my-deployment": {"backend": "no-backend", "auth": {"type": "no-auth"}},
            "deployment123": {"backend": "no-backend", "auth": {"type": "no-auth"}},
            "a-b-c-123": {"backend": "no-backend", "auth": {"type": "no-auth"}},
        },
        "config": [],
    }
    HelmValuesConfig._validate_schema(valid_config)  # Should not raise

    # Invalid cases - test one by one to ensure proper validation
    base_config = {"version": "1.0", "release": "test-release", "deployments": {}, "config": []}

    invalid_names = [
        "UPPERCASE",  # uppercase not allowed
        "my_deployment",  # underscore not allowed
        "my.deployment",  # dot not allowed
        "-starts-with-hyphen",  # cannot start with hyphen
        "ends-with-hyphen-",  # cannot end with hyphen
        "",  # empty string
    ]

    for name in invalid_names:
        config = dict(base_config)
        config["deployments"] = {name: {"backend": "no-backend", "auth": {"type": "no-auth"}}}
        with pytest.raises(jsonschema.exceptions.ValidationError):
            HelmValuesConfig._validate_schema(config)
