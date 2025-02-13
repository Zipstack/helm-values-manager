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

    def get_value(self, path: str, environment: str) -> str:
        """Get a value from the store.

        Args:
            path: The configuration path
            environment: The environment name

        Returns:
            The stored value

        Raises:
            ValueError: If value not found
        """
        key = f"{path}:{environment}"
        if key not in self.store:
            raise ValueError(f"No value found for {path} in {environment}")
        return self.store[key]

    def set_value(self, path: str, environment: str, value: str) -> None:
        """Set a value in the store.

        Args:
            path: The configuration path
            environment: The environment name
            value: The value to store
        """
        key = f"{path}:{environment}"
        self.store[key] = value

    def remove_value(self, path: str, environment: str) -> None:
        """Remove a value from the store.

        Args:
            path: The configuration path
            environment: The environment name

        Raises:
            ValueError: If value not found
        """
        key = f"{path}:{environment}"
        if key not in self.store:
            raise ValueError(f"No value found for {path} in {environment}")
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
    backend.set_value("app.replicas", "dev", "3")

    # Test getting existing value
    assert backend.get_value("app.replicas", "dev") == "3"

    # Test getting non-existent value
    with pytest.raises(ValueError, match="No value found"):
        backend.get_value("app.replicas", "prod")


def test_set_value(backend):
    """Test setting values in the backend."""
    # Test setting new value
    backend.set_value("app.replicas", "dev", "3")
    assert backend.get_value("app.replicas", "dev") == "3"

    # Test overwriting existing value
    backend.set_value("app.replicas", "dev", "5")
    assert backend.get_value("app.replicas", "dev") == "5"


def test_remove_value(backend):
    """Test removing values from the backend."""
    # Set test value
    backend.set_value("app.replicas", "dev", "3")
    assert backend.get_value("app.replicas", "dev") == "3"

    # Test removing existing value
    backend.remove_value("app.replicas", "dev")
    with pytest.raises(ValueError, match="No value found"):
        backend.get_value("app.replicas", "dev")

    # Test removing non-existent value
    with pytest.raises(ValueError, match="No value found"):
        backend.remove_value("app.replicas", "prod")
