"""Tests for the config_metadata module."""

from helm_values_manager.models.config_metadata import ConfigMetadata


def test_from_dict():
    """Test creating ConfigMetadata from dictionary."""
    data = {
        "description": "Test description",
        "required": True,
        "sensitive": True,
    }
    metadata = ConfigMetadata.from_dict(data)
    assert metadata.description == "Test description"
    assert metadata.required is True
    assert metadata.sensitive is True


def test_from_dict_defaults():
    """Test default values when creating from dictionary."""
    data = {"description": "Test description"}
    metadata = ConfigMetadata.from_dict(data)
    assert metadata.description == "Test description"
    assert metadata.required is False
    assert metadata.sensitive is False


def test_to_dict():
    """Test converting ConfigMetadata to dictionary."""
    metadata = ConfigMetadata(
        description="Test description",
        required=True,
        sensitive=True,
    )
    data = metadata.to_dict()
    assert data["description"] == "Test description"
    assert data["required"] is True
    assert data["sensitive"] is True
