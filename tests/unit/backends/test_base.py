"""Tests for the ValueBackend base class."""

import pytest

from helm_values_manager.backends.base import ValueBackend


class DummyBackend(ValueBackend):
    """A dummy backend implementation for testing the base class."""

    def __init__(self, auth_config={"type": "direct"}):
        """Initialize the dummy backend.

        Args:
            auth_config: Optional authentication configuration
        """
        self.store = {}
        super().__init__(auth_config)

    def get_value(self, key: str) -> str:
        """Get a value from the store.

        Args:
            key: The key to retrieve

        Returns:
            The stored value

        Raises:
            ValueError: If key not found
        """
        if key not in self.store:
            raise ValueError(f"Key not found: {key}")
        return self.store[key]

    def set_value(self, key: str, value: str) -> None:
        """Set a value in the store.

        Args:
            key: The key to store under
            value: The value to store
        """
        self.store[key] = value


@pytest.fixture
def backend():
    """Create a DummyBackend instance for testing."""
    return DummyBackend()


def test_backend_initialization():
    """Test backend initialization with different auth configs."""
    # Test with default auth config
    backend = DummyBackend()
    assert isinstance(backend, ValueBackend)

    # Test with direct auth type
    backend = DummyBackend(auth_config={"type": "direct"})
    assert isinstance(backend, ValueBackend)

    # Test with managed identity auth type
    backend = DummyBackend(auth_config={"type": "managed_identity"})
    assert isinstance(backend, ValueBackend)

    # Test with invalid auth config
    with pytest.raises(ValueError, match="Auth config must contain 'type'"):
        backend = DummyBackend(auth_config={})

    with pytest.raises(ValueError, match="Auth config must be a dictionary"):
        backend = DummyBackend(auth_config=None)


def test_get_value(backend):
    """Test getting values from the backend."""
    # Set some test values
    backend.set_value("key1", "value1")
    backend.set_value("key2", "value2")

    # Test getting existing values
    assert backend.get_value("key1") == "value1"
    assert backend.get_value("key2") == "value2"

    # Test getting non-existent key
    with pytest.raises(ValueError, match="Key not found"):
        backend.get_value("non_existent")


def test_set_value(backend):
    """Test setting values in the backend."""
    # Test setting new value
    backend.set_value("key1", "value1")
    assert backend.get_value("key1") == "value1"

    # Test overwriting existing value
    backend.set_value("key1", "new_value")
    assert backend.get_value("key1") == "new_value"
