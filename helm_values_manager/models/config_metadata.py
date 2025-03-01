"""Simple dataclass for configuration metadata."""

from dataclasses import asdict, dataclass
from typing import Any, ClassVar, Dict


@dataclass
class ConfigMetadata:
    """
    Represents metadata for a configuration path.

    Attributes:
        description (str): Description of the configuration path. Defaults to empty string.
        required (bool): Whether the configuration path is required. Defaults to False.
        sensitive (bool): Whether the configuration path is sensitive. Defaults to False.
    """

    # Default values as class variables for reference elsewhere
    DEFAULT_DESCRIPTION: ClassVar[str] = ""
    DEFAULT_REQUIRED: ClassVar[bool] = False
    DEFAULT_SENSITIVE: ClassVar[bool] = False

    description: str = DEFAULT_DESCRIPTION
    required: bool = DEFAULT_REQUIRED
    sensitive: bool = DEFAULT_SENSITIVE

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigMetadata":
        """Create a ConfigMetadata instance from a dictionary."""
        return cls(
            description=data.get("description", cls.DEFAULT_DESCRIPTION),
            required=data.get("required", cls.DEFAULT_REQUIRED),
            sensitive=data.get("sensitive", cls.DEFAULT_SENSITIVE),
        )
