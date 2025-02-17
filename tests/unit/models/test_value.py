"""Tests for the Value class."""

from unittest.mock import Mock

import pytest

from helm_values_manager.backends.base import ValueBackend
from helm_values_manager.models.value import Value


@pytest.fixture
def mock_backend():
    """Create a mock backend for testing."""
    backend = Mock(spec=ValueBackend)
    # Return different values based on resolve parameter
    backend.get_value.side_effect = lambda path, env, resolve: (
        "secret://gcp-secrets/my-app/dev/value" if not resolve else "resolved_value"
    )
    backend.backend_type = "mock"
    return backend


def test_value_init(mock_backend):
    """Test Value initialization."""
    value = Value(path="app.replicas", environment="dev", _backend=mock_backend)
    assert value.path == "app.replicas"
    assert value.environment == "dev"
    assert value._backend == mock_backend


def test_get_value_without_resolve(mock_backend):
    """Test getting a value without resolving."""
    value = Value(path="app.replicas", environment="dev", _backend=mock_backend)
    assert value.get(resolve=False) == "secret://gcp-secrets/my-app/dev/value"
    mock_backend.get_value.assert_called_once_with("app.replicas", "dev", False)


def test_get_value_with_resolve(mock_backend):
    """Test getting a value with resolving."""
    value = Value(path="app.replicas", environment="dev", _backend=mock_backend)
    assert value.get(resolve=True) == "resolved_value"
    mock_backend.get_value.assert_called_once_with("app.replicas", "dev", True)


def test_set_value(mock_backend):
    """Test setting a value."""
    value = Value(path="app.replicas", environment="dev", _backend=mock_backend)
    value.set("3")
    mock_backend.set_value.assert_called_once_with("app.replicas", "dev", "3")


def test_set_valid_types(mock_backend):
    """Test setting various valid value types."""
    value = Value(path="app.replicas", environment="dev", _backend=mock_backend)

    # Test string
    value.set("test-value")
    mock_backend.set_value.assert_called_with("app.replicas", "dev", "test-value")

    # Test integer
    value.set(42)
    mock_backend.set_value.assert_called_with("app.replicas", "dev", 42)

    # Test float
    value.set(3.14)
    mock_backend.set_value.assert_called_with("app.replicas", "dev", 3.14)

    # Test boolean
    value.set(True)
    mock_backend.set_value.assert_called_with("app.replicas", "dev", True)

    # Test None
    value.set(None)
    mock_backend.set_value.assert_called_with("app.replicas", "dev", None)


def test_set_invalid_type(mock_backend):
    """Test setting an invalid value type."""
    value = Value(path="app.replicas", environment="dev", _backend=mock_backend)
    with pytest.raises(ValueError, match="Value must be a string, number, boolean, or None"):
        value.set({"key": "value"})  # Dictionary is not a valid type


def test_to_dict(mock_backend):
    """Test serializing a value."""
    value = Value(path="app.replicas", environment="dev", _backend=mock_backend)
    data = value.to_dict()
    assert data == {"path": "app.replicas", "environment": "dev", "backend_type": "mock"}


def test_from_dict(mock_backend):
    """Test deserializing a value."""
    data = {"path": "app.replicas", "environment": "dev"}
    value = Value.from_dict(data, mock_backend)
    assert value.path == "app.replicas"
    assert value.environment == "dev"
    assert value._backend == mock_backend


def test_from_dict_invalid():
    """Test deserializing with invalid data."""
    with pytest.raises(ValueError, match="Data must be a dictionary"):
        Value.from_dict("not a dict", Mock(spec=ValueBackend))


def test_from_dict_missing_path(mock_backend):
    """Test deserializing with missing path."""
    data = {"environment": "dev"}
    with pytest.raises(ValueError, match="Missing required field: path"):
        Value.from_dict(data, mock_backend)


def test_from_dict_missing_environment(mock_backend):
    """Test deserializing with missing environment."""
    data = {"path": "app.replicas"}
    with pytest.raises(ValueError, match="Missing required field: environment"):
        Value.from_dict(data, mock_backend)
