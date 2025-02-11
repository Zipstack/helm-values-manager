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

    def remove_value(self, key: str) -> None:
        """Remove a value from the store.

        Args:
            key: The key to remove

        Raises:
            ValueError: If key not found
        """
        if key not in self.store:
            raise ValueError(f"Key not found: {key}")
        del self.store[key]


@pytest.fixture
def backend():
    """Create a DummyBackend instance for testing."""
    return DummyBackend()


def test_auth_config_validation():
    """Test authentication configuration validation."""
    # Test valid auth types
    valid_types = ["env", "file", "direct", "managed_identity"]
    for auth_type in valid_types:
        backend = DummyBackend({"type": auth_type})
        assert isinstance(backend, DummyBackend)

    # Test invalid auth config type
    with pytest.raises(ValueError, match="Auth config must be a dictionary"):
        DummyBackend(None)

    # Test missing type field
    with pytest.raises(ValueError, match="Auth config must contain 'type' field"):
        DummyBackend({})

    # Test invalid auth type
    with pytest.raises(ValueError, match="Invalid auth type"):
        DummyBackend({"type": "invalid"})


def test_get_value(backend):
    """Test getting values from the backend."""
    # Set test value
    backend.set_value("test/key", "test_value")

    # Test getting existing value
    assert backend.get_value("test/key") == "test_value"

    # Test getting non-existent value
    with pytest.raises(ValueError, match="Key not found"):
        backend.get_value("non/existent")


def test_set_value(backend):
    """Test setting values in the backend."""
    # Test setting new value
    backend.set_value("test/key", "test_value")
    assert backend.get_value("test/key") == "test_value"

    # Test overwriting existing value
    backend.set_value("test/key", "new_value")
    assert backend.get_value("test/key") == "new_value"


def test_remove_value(backend):
    """Test removing values from the backend."""
    # Set test value
    backend.set_value("test/key", "test_value")
    assert backend.get_value("test/key") == "test_value"

    # Test removing existing value
    backend.remove_value("test/key")
    with pytest.raises(ValueError, match="Key not found"):
        backend.get_value("test/key")

    # Test removing non-existent value
    with pytest.raises(ValueError, match="Key not found"):
        backend.remove_value("non/existent")
