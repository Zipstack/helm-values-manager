"""Tests for the SimpleValueBackend."""

import pytest

from helm_values_manager.backends.simple import SimpleValueBackend


@pytest.fixture
def backend():
    """Create a SimpleValueBackend instance for testing."""
    return SimpleValueBackend()


def test_get_value_not_found(backend):
    """Test getting a non-existent value."""
    with pytest.raises(ValueError, match="No value found for app.replicas in dev"):
        backend.get_value("app.replicas", "dev")


def test_set_and_get_value(backend):
    """Test setting and getting a value."""
    backend.set_value("app.replicas", "dev", "3")
    assert backend.get_value("app.replicas", "dev") == "3"


def test_set_invalid_value_type(backend):
    """Test setting an invalid value type."""
    with pytest.raises(ValueError, match="Value must be a string, number, boolean, or None"):
        backend.set_value("app.replicas", "dev", {"key": "value"})  # Dictionary is not a valid type


def test_remove_value(backend):
    """Test removing a value."""
    # Set and verify value
    backend.set_value("app.replicas", "dev", "3")
    assert backend.get_value("app.replicas", "dev") == "3"

    # Remove and verify it's gone
    backend.remove_value("app.replicas", "dev")
    with pytest.raises(ValueError, match="No value found for app.replicas in dev"):
        backend.get_value("app.replicas", "dev")


def test_remove_non_existent_value(backend):
    """Test removing a non-existent value."""
    with pytest.raises(ValueError, match="No value found for app.replicas in dev"):
        backend.remove_value("app.replicas", "dev")


def test_environment_isolation(backend):
    """Test that values are isolated between environments."""
    # Set value in dev
    backend.set_value("app.replicas", "dev", "3")
    assert backend.get_value("app.replicas", "dev") == "3"

    # Verify it doesn't exist in prod
    with pytest.raises(ValueError, match="No value found for app.replicas in prod"):
        backend.get_value("app.replicas", "prod")

    # Set different value in prod
    backend.set_value("app.replicas", "prod", "5")
    assert backend.get_value("app.replicas", "prod") == "5"
    assert backend.get_value("app.replicas", "dev") == "3"


def test_path_isolation(backend):
    """Test that values are isolated between paths."""
    # Set value for app.replicas
    backend.set_value("app.replicas", "dev", "3")
    assert backend.get_value("app.replicas", "dev") == "3"

    # Set value for app.image
    backend.set_value("app.image", "dev", "nginx:latest")
    assert backend.get_value("app.image", "dev") == "nginx:latest"
    assert backend.get_value("app.replicas", "dev") == "3"
