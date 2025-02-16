"""Tests for the path_data module."""

from unittest.mock import Mock

import pytest

from helm_values_manager.models.path_data import PathData
from helm_values_manager.models.value import Value


@pytest.fixture
def path_data():
    """Create a PathData instance for testing."""
    return PathData(
        "test.path",
        {
            "description": "Test description",
            "required": True,
            "sensitive": False,
        },
    )


@pytest.fixture
def mock_value():
    """Create a mock Value instance."""
    value = Mock(spec=Value)
    value.path = "test.path"
    return value


def test_path_data_init(path_data):
    """Test PathData initialization."""
    assert path_data.path == "test.path"
    assert path_data.metadata["description"] == "Test description"
    assert path_data.metadata["required"] is True
    assert path_data.metadata["sensitive"] is False


def test_set_value(path_data, mock_value):
    """Test setting a value."""
    path_data.set_value("test", mock_value)
    assert path_data._values["test"] == mock_value


def test_get_value_nonexistent_environment(path_data):
    """Test getting a value for a non-existent environment."""
    assert path_data.get_value("test") is None


def test_get_value(path_data, mock_value):
    """Test getting a value."""
    mock_value.get.return_value = "test_value"
    path_data.set_value("test", mock_value)
    assert path_data.get_value("test") == "test_value"


def test_get_environments(path_data, mock_value):
    """Test getting environment names."""
    path_data.set_value("test1", mock_value)
    path_data.set_value("test2", mock_value)
    environments = list(path_data.get_environments())
    assert len(environments) == 2
    assert "test1" in environments
    assert "test2" in environments
