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


def test_value_init_local():
    """Test Value initialization with local storage."""
    value = Value(path="app.replicas", environment="dev")
    assert value.path == "app.replicas"
    assert value.environment == "dev"
    assert value.storage_type == "local"
    assert value._backend is None
    assert value._value is None


def test_value_init_remote(mock_backend):
    """Test Value initialization with remote storage."""
    value = Value(path="app.replicas", environment="dev", storage_type="remote", _backend=mock_backend)
    assert value.storage_type == "remote"
    assert value._backend == mock_backend


def test_value_init_invalid_storage():
    """Test Value initialization with invalid storage type."""
    with pytest.raises(ValueError, match="Invalid storage type"):
        Value(path="app.replicas", environment="dev", storage_type="invalid")


def test_value_init_remote_no_backend():
    """Test Value initialization with remote storage but no backend."""
    with pytest.raises(ValueError, match="Remote storage type requires a backend"):
        Value(path="app.replicas", environment="dev", storage_type="remote")


def test_get_local():
    """Test getting a local value."""
    value = Value(path="app.replicas", environment="dev", _value="3")
    assert value.get() == "3"


def test_get_local_not_set():
    """Test getting an unset local value."""
    value = Value(path="app.replicas", environment="dev")
    with pytest.raises(ValueError, match="No value set"):
        value.get()


def test_get_remote(mock_backend):
    """Test getting a remote value."""
    value = Value(path="app.replicas", environment="dev", storage_type="remote", _backend=mock_backend)
    assert value.get() == "mock_value"
    mock_backend.get_value.assert_called_once_with("app.replicas:dev")


def test_set_local():
    """Test setting a local value."""
    value = Value(path="app.replicas", environment="dev")
    value.set("3")
    assert value._value == "3"


def test_set_remote(mock_backend):
    """Test setting a remote value."""
    value = Value(path="app.replicas", environment="dev", storage_type="remote", _backend=mock_backend)
    value.set("3")
    mock_backend.set_value.assert_called_once_with("app.replicas:dev", "3")


def test_set_invalid_type():
    """Test setting a non-string value."""
    value = Value(path="app.replicas", environment="dev")
    with pytest.raises(ValueError, match="Value must be a string"):
        value.set(3)


def test_to_dict_local():
    """Test serializing a local value."""
    value = Value(path="app.replicas", environment="dev", _value="3")
    data = value.to_dict()
    assert data == {"path": "app.replicas", "environment": "dev", "storage_type": "local", "value": "3"}


def test_to_dict_remote(mock_backend):
    """Test serializing a remote value."""
    value = Value(path="app.replicas", environment="dev", storage_type="remote", _backend=mock_backend)
    data = value.to_dict()
    assert data == {"path": "app.replicas", "environment": "dev", "storage_type": "remote", "value": None}


def test_from_dict_local():
    """Test deserializing a local value."""
    data = {"path": "app.replicas", "environment": "dev", "storage_type": "local", "value": "3"}
    value = Value.from_dict(data)
    assert value.path == "app.replicas"
    assert value.environment == "dev"
    assert value.storage_type == "local"
    assert value._value == "3"


def test_from_dict_remote(mock_backend):
    """Test deserializing a remote value."""
    data = {"path": "app.replicas", "environment": "dev", "storage_type": "remote", "value": None}
    value = Value.from_dict(data, mock_backend)
    assert value.path == "app.replicas"
    assert value.environment == "dev"
    assert value.storage_type == "remote"
    assert value._backend == mock_backend
    assert value._value is None


def test_from_dict_invalid():
    """Test deserializing with invalid data."""
    with pytest.raises(ValueError, match="Data must be a dictionary"):
        Value.from_dict("not a dict")


def test_from_dict_missing_path():
    """Test deserializing with missing path."""
    data = {"environment": "dev", "storage_type": "local", "value": "3"}
    with pytest.raises(ValueError, match="Missing required field: path"):
        Value.from_dict(data)


def test_from_dict_missing_environment():
    """Test deserializing with missing environment."""
    data = {"path": "app.replicas", "storage_type": "local", "value": "3"}
    with pytest.raises(ValueError, match="Missing required field: environment"):
        Value.from_dict(data)
