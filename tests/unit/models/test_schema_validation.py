"""Test suite for schema validation and data loading in HelmValuesConfig."""

import pytest
from jsonschema.exceptions import ValidationError

from helm_values_manager.models.helm_values_config import HelmValuesConfig


def test_valid_minimal_config():
    """Test loading a minimal valid configuration."""
    config_data = {"version": "1.0", "release": "test-release", "deployments": {}, "config": []}
    config = HelmValuesConfig.from_dict(config_data)
    assert isinstance(config, HelmValuesConfig)
    # Verify loaded data
    assert config.release == "test-release"
    assert config.version == "1.0"
    assert len(config.deployments) == 0
    assert len(config._path_map) == 0


def test_valid_full_config():
    """Test loading a valid configuration with all fields."""
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
    config = HelmValuesConfig.from_dict(config_data)
    # Verify loaded data
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
    assert config.get_value("app.config.key1", "default") == "test-value"


def test_default_values():
    """Test that default values are properly set when fields are omitted."""
    config_data = {
        "version": "1.0",
        "release": "test-release",
        "deployments": {},
        "config": [{"path": "app.config.key1", "values": {}}],
    }
    config = HelmValuesConfig.from_dict(config_data)
    path_data = config._path_map["app.config.key1"]
    assert path_data.metadata.description is None
    assert path_data.metadata.required is False
    assert path_data.metadata.sensitive is False


def test_type_coercion():
    """Test that values are properly coerced to their expected types."""
    config_data = {
        "version": "1.0",
        "release": "test-release",
        "deployments": {},
        "config": [
            {
                "path": "app.config.key1",
                "required": True,  # Proper boolean
                "sensitive": False,  # Proper boolean
                "values": {},
            }
        ],
    }
    config = HelmValuesConfig.from_dict(config_data)
    path_data = config._path_map["app.config.key1"]
    assert path_data.metadata.required is True
    assert path_data.metadata.sensitive is False


def test_missing_required_fields():
    """Test that missing required fields raise validation error."""
    config_data = {"version": "1.0", "release": "test-release", "config": []}  # Missing required 'deployments' field
    with pytest.raises(ValidationError, match=r".*'deployments'.*required property.*"):
        HelmValuesConfig.from_dict(config_data)


def test_invalid_version():
    """Test that invalid version raises validation error."""
    config_data = {"version": "2.0", "release": "test-release", "deployments": {}, "config": []}  # Invalid version
    with pytest.raises(ValidationError, match=r".*'2\.0'.*not one of.*"):
        HelmValuesConfig.from_dict(config_data)


def test_invalid_backend_type():
    """Test that invalid backend type raises validation error."""
    config_data = {
        "version": "1.0",
        "release": "test-release",
        "deployments": {
            "prod": {"backend": "invalid", "auth": {"type": "env", "env_prefix": "AWS_"}}  # Invalid backend type
        },
        "config": [],
    }
    with pytest.raises(ValidationError, match=r".*'invalid'.*not one of.*"):
        HelmValuesConfig.from_dict(config_data)


def test_invalid_auth_config():
    """Test that invalid auth configuration raises validation error."""
    config_data = {
        "version": "1.0",
        "release": "test-release",
        "deployments": {"prod": {"backend": "aws", "auth": {"invalid": "config"}}},  # Invalid auth config
        "config": [],
    }
    with pytest.raises(ValidationError, match=r".*'env_prefix' is a required property.*"):
        HelmValuesConfig.from_dict(config_data)


def test_invalid_path_format():
    """Test that invalid path format raises validation error."""
    config_data = {
        "version": "1.0",
        "release": "test-release",
        "deployments": {},
        "config": [{"path": "invalid/path", "required": True, "sensitive": False, "values": {}}],  # Invalid path format
    }
    with pytest.raises(ValidationError, match=r".*'invalid/path'.*does not match.*"):
        HelmValuesConfig.from_dict(config_data)
