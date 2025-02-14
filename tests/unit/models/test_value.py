"""Tests for the Value class."""

from unittest.mock import Mock

import pytest

from helm_values_manager.backends.base import ValueBackend
from helm_values_manager.models.value import Value


@pytest.fixture
def mock_backend():
    """Create a mock backend for testing."""
    backend = Mock(spec=ValueBackend)
    backend.get_value.return_value = "mock_value"
    return backend


def test_value_init(mock_backend):
    """Test Value initialization."""
    value = Value(path="app.replicas", environment="dev", _backend=mock_backend)
    assert value.path == "app.replicas"
    assert value.environment == "dev"
    assert value._backend == mock_backend


def test_get_value(mock_backend):
    """Test getting a value."""
    value = Value(path="app.replicas", environment="dev", _backend=mock_backend)
    assert value.get() == "mock_value"
    mock_backend.get_value.assert_called_once_with("app.replicas", "dev")


def test_set_value(mock_backend):
    """Test setting a value."""
    value = Value(path="app.replicas", environment="dev", _backend=mock_backend)
    value.set("3")
    mock_backend.set_value.assert_called_once_with("app.replicas", "dev", "3")


def test_set_invalid_type(mock_backend):
    """Test setting a non-string value."""
    value = Value(path="app.replicas", environment="dev", _backend=mock_backend)
    with pytest.raises(ValueError, match="Value must be a string"):
        value.set(3)


def test_to_dict(mock_backend):
    """Test serializing a value."""
    mock_backend.backend_type = "mock"
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
