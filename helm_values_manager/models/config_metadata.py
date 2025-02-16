"""Simple dataclass for configuration metadata."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass
class ConfigMetadata:
    """
    Represents metadata for a configuration path.

    Attributes:
        description (Optional[str]): Description of the configuration path.
        required (bool): Whether the configuration path is required. Defaults to False.
        sensitive (bool): Whether the configuration path is sensitive. Defaults to False.
    """

    description: Optional[str] = None
    required: bool = False
    sensitive: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigMetadata":
        """Create a ConfigMetadata instance from a dictionary."""
        return cls(
            description=data.get("description"),
            required=data.get("required", False),
            sensitive=data.get("sensitive", False),
        )
