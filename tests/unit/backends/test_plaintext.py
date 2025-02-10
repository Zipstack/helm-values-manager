"""Tests for the PlainTextBackend implementation."""

import pytest

from helm_values_manager.backends.plaintext import PlainTextBackend


@pytest.fixture
def backend():
    """Create a PlainTextBackend instance for testing."""
    return PlainTextBackend()


def test_plaintext_backend_initialization():
    """Test PlainTextBackend initialization."""
    # Test with no auth config
    backend = PlainTextBackend()
    assert isinstance(backend, PlainTextBackend)

    # Test with auth config
    backend = PlainTextBackend(auth_config={"type": "anything"})
    assert isinstance(backend, PlainTextBackend)


def test_get_value(backend):
    """Test getting values from the backend."""
    # Set some test values
    backend.set_value("test/path:dev", "dev_value")
    backend.set_value("test/path:prod", "prod_value")
    backend.set_value("another/path:dev", "another_dev_value")

    # Test getting existing values
    assert backend.get_value("test/path:dev") == "dev_value"
    assert backend.get_value("test/path:prod") == "prod_value"
    assert backend.get_value("another/path:dev") == "another_dev_value"

    # Test getting non-existent key
    with pytest.raises(ValueError, match="Key not found"):
        backend.get_value("non/existent:dev")


def test_set_value(backend):
    """Test setting values in the backend."""
    # Test setting new value
    backend.set_value("test/path:staging", "staging_value")
    assert backend.get_value("test/path:staging") == "staging_value"

    # Test overwriting existing value
    backend.set_value("test/path:staging", "new_value")
    assert backend.get_value("test/path:staging") == "new_value"
