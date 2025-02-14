"""Tests for the PathData class."""

from unittest.mock import Mock

import pytest

from helm_values_manager.models.path_data import PathData
from helm_values_manager.models.value import Value


@pytest.fixture
def mock_value():
    """Create a mock Value instance."""
    mock_backend = Mock()
    mock_backend.get_value.return_value = "test_value"
    return Value(path="test.path", environment="test", _backend=mock_backend)


@pytest.fixture
def valid_metadata():
    """Create valid metadata for testing."""
    return {"description": "Test description", "required": True, "sensitive": False}


@pytest.fixture
def path_data(valid_metadata):
    """Create a PathData instance with valid metadata."""
    return PathData("test.path", valid_metadata)


def test_init_with_valid_metadata(valid_metadata):
    """Test PathData initialization with valid metadata."""
    path_data = PathData("test.path", valid_metadata)
    assert path_data.path == "test.path"
    assert path_data.metadata == valid_metadata
    assert list(path_data.get_environments()) == []


def test_init_with_none_description():
    """Test PathData initialization with None description."""
    metadata = {"description": None, "required": True, "sensitive": False}
    path_data = PathData("test.path", metadata)
    assert path_data.metadata["description"] is None


def test_validate_missing_metadata():
    """Test validate() with missing metadata fields."""
    metadata = {"description": "Test"}  # Missing required and sensitive
    path_data = PathData("test.path", metadata)
    with pytest.raises(ValueError, match="Missing required metadata fields"):
        path_data.validate()


def test_validate_invalid_metadata_types():
    """Test validate() with invalid metadata types."""
    test_cases = [
        {
            "metadata": {"description": 123, "required": True, "sensitive": False},
            "match": "Description must be a string or None",
        },
        {
            "metadata": {"description": "Test", "required": "True", "sensitive": False},
            "match": "Required flag must be a boolean",
        },
        {
            "metadata": {"description": "Test", "required": True, "sensitive": "False"},
            "match": "Sensitive flag must be a boolean",
        },
    ]

    for case in test_cases:
        path_data = PathData("test.path", case["metadata"])
        with pytest.raises(ValueError, match=case["match"]):
            path_data.validate()


def test_validate_path_consistency(path_data):
    """Test validate() with inconsistent paths."""
    mock_backend = Mock()
    inconsistent_value = Value(path="different.path", environment="test", _backend=mock_backend)
    # Access private attribute for testing
    path_data._values["test"] = inconsistent_value
    with pytest.raises(ValueError, match="Value for environment test has inconsistent path"):
        path_data.validate()


def test_set_value(path_data, mock_value):
    """Test setting a Value object."""
    # Test adding a new value
    path_data.set_value("test", mock_value)
    assert path_data.get_value("test") == mock_value
    assert list(path_data.get_environments()) == ["test"]

    # Test updating an existing value
    new_mock_value = Value(path="test.path", environment="test", _backend=Mock())
    path_data.set_value("test", new_mock_value)
    assert path_data.get_value("test") == new_mock_value


def test_set_value_with_wrong_path(path_data):
    """Test setting a Value object with wrong path."""
    mock_backend = Mock()
    wrong_path_value = Value(path="wrong.path", environment="test", _backend=mock_backend)
    with pytest.raises(ValueError, match="Value path wrong.path doesn't match PathData path test.path"):
        path_data.set_value("test", wrong_path_value)


def test_get_value(path_data, mock_value):
    """Test getting a Value object."""
    path_data.set_value("test", mock_value)
    assert path_data.get_value("test") == mock_value
    assert path_data.get_value("nonexistent") is None


def test_get_environments(path_data, mock_value):
    """Test getting environment names."""
    path_data.set_value("test1", mock_value)
    path_data.set_value("test2", mock_value)
    assert set(path_data.get_environments()) == {"test1", "test2"}


def test_to_dict(path_data, mock_value):
    """Test converting PathData to dictionary."""
    path_data.set_value("test", mock_value)
    result = path_data.to_dict()

    assert result["path"] == "test.path"
    assert result["metadata"] == path_data.metadata
    assert "test" in result["values"]
    assert result["values"]["test"] == mock_value.to_dict()


def test_from_dict_valid_data(valid_metadata, mock_value):
    """Test creating PathData from valid dictionary data."""
    data = {
        "path": "test.path",
        "metadata": valid_metadata,
        "values": {"test": {"path": "test.path", "environment": "test", "backend_type": "mock"}},
    }

    def create_value_fn(path, env, data):
        return mock_value

    path_data = PathData.from_dict(data, create_value_fn)
    assert path_data.path == "test.path"
    assert path_data.metadata == valid_metadata
    assert path_data.get_value("test") == mock_value


def test_from_dict_invalid_data():
    """Test from_dict() with invalid data."""
    test_cases = [
        ("not_a_dict", "Data must be a dictionary"),
        ({"metadata": {}, "values": {}}, "Missing required keys"),  # Missing path
        ({"path": "test.path", "values": {}}, "Missing required keys"),  # Missing metadata
        ({"path": "test.path", "metadata": {}}, "Missing required keys"),  # Missing values
    ]

    for data, error_match in test_cases:
        with pytest.raises(ValueError, match=error_match):
            PathData.from_dict(data, lambda p, e, d: None)
