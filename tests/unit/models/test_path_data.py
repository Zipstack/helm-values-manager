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
    assert path_data.metadata.description == "Test description"
    assert path_data.metadata.required is True
    assert path_data.metadata.sensitive is False


def test_set_value(path_data, mock_value):
    """Test setting a value."""
    path_data.set_value("test", mock_value)
    assert path_data._values["test"] == mock_value


def test_get_value_nonexistent_environment(path_data):
    """Test getting a value for a non-existent environment."""
    assert path_data.get_value("test") is None


def test_get_value(path_data, mock_value):
    """Test getting a value."""
    path_data.set_value("test", mock_value)
    assert path_data.get_value("test") == mock_value


def test_get_environments(path_data, mock_value):
    """Test getting environment names."""
    path_data.set_value("test1", mock_value)
    path_data.set_value("test2", mock_value)
    environments = list(path_data.get_environments())
    assert len(environments) == 2
    assert "test1" in environments
    assert "test2" in environments


def test_validate_path_mismatch():
    """Test validation when a value has a mismatched path."""
    path_data = PathData("test.path", {"required": True})
    mock_value = Mock(spec=Value)
    mock_value.path = "wrong.path"
    path_data._values["test_env"] = mock_value
    with pytest.raises(
        ValueError, match=r"Value for environment test_env has inconsistent path: wrong\.path != test\.path"
    ):
        path_data.validate()


def test_validate_required_missing_value(path_data):
    """Test validation with missing required value."""
    mock_value = Mock(spec=Value)
    mock_value.path = "test.path"
    mock_value.get.return_value = None
    path_data.set_value("test_env", mock_value)

    with pytest.raises(ValueError, match=r"Missing required value for path test\.path in environment test_env"):
        path_data.validate()


def test_validate_required_empty_value(path_data):
    """Test validation with empty required value."""
    mock_value = Mock(spec=Value)
    mock_value.path = "test.path"
    mock_value.get.return_value = ""
    path_data.set_value("test_env", mock_value)

    with pytest.raises(ValueError, match=r"Missing required value for path test\.path in environment test_env"):
        path_data.validate()


def test_validate_success(path_data, mock_value):
    """Test successful validation."""
    mock_value.get.return_value = "test_value"
    path_data.set_value("test_env", mock_value)
    path_data.validate()  # Should not raise any error


def test_validate_not_required(path_data, mock_value):
    """Test validation when path is not required."""
    path_data.metadata.required = False
    mock_value.get.return_value = None
    path_data.set_value("test_env", mock_value)
    path_data.validate()  # Should not raise any error


def test_to_dict(path_data, mock_value):
    """Test converting PathData to dictionary."""
    mock_value.get.return_value = "test_value"
    path_data.set_value("test_env", mock_value)

    result = path_data.to_dict()
    assert result["path"] == "test.path"
    assert result["description"] == "Test description"
    assert result["required"] is True
    assert result["sensitive"] is False
    assert result["values"] == {"test_env": "test_value"}


def test_from_dict():
    """Test creating PathData from dictionary."""
    data = {
        "path": "test.path",
        "description": "Test description",
        "required": True,
        "sensitive": False,
        "values": {"test_env": "test_value"},
    }

    def create_value_fn(path, env, value_data):
        mock_value = Mock(spec=Value)
        mock_value.path = path
        mock_value.environment = env
        return mock_value

    path_data = PathData.from_dict(data, create_value_fn)
    assert path_data.path == "test.path"
    assert path_data.metadata.description == "Test description"
    assert path_data.metadata.required is True
    assert path_data.metadata.sensitive is False
    assert len(path_data._values) == 1
    assert "test_env" in path_data._values


def test_from_dict_invalid_type():
    """Test from_dict with invalid data type."""
    with pytest.raises(ValueError, match="Data must be a dictionary"):
        PathData.from_dict(["not a dict"], lambda p, e, d: None)


def test_from_dict_missing_keys():
    """Test from_dict with missing required keys."""
    data = {"path": "test.path"}  # Missing values field

    def create_value_fn(path, env, value_data):
        mock_value = Mock(spec=Value)
        mock_value.path = path
        return mock_value

    with pytest.raises(ValueError, match=r"Missing required keys: {'values'}"):
        PathData.from_dict(data, create_value_fn)


def test_from_dict_value_path_mismatch():
    """Test from_dict when create_value_fn returns value with wrong path."""
    data = {
        "path": "test.path",
        "metadata": {"required": True},
        "values": {"test_env": {"value": "test"}},
    }

    def create_value_fn(path, env, value_data):
        mock_value = Mock(spec=Value)
        mock_value.path = "wrong.path"  # Mismatched path
        return mock_value

    with pytest.raises(ValueError, match=r"Value path wrong\.path does not match PathData path test\.path"):
        PathData.from_dict(data, create_value_fn)
