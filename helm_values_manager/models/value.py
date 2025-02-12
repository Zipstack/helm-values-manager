"""
Value class implementation for Helm Values Manager.

This module provides the Value class which encapsulates the storage and resolution
of configuration values, supporting both local and remote storage backends.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..backends.base import ValueBackend


@dataclass
class Value:
    """
    Represents a configuration value with its storage strategy.

    Attributes:
        path: The configuration path (e.g., "app.replicas")
        environment: The environment name (e.g., "dev", "prod")
        storage_type: Type of storage ("local" or "remote")
        _backend: Optional backend for remote storage
        _value: The actual value for local storage
    """

    path: str
    environment: str
    storage_type: str = "local"
    _backend: Optional[ValueBackend] = None
    _value: Optional[str] = None

    def __post_init__(self):
        """Validate the value configuration after initialization."""
        if self.storage_type not in ["local", "remote"]:
            raise ValueError(f"Invalid storage type: {self.storage_type}")

        if self.storage_type == "remote" and self._backend is None:
            raise ValueError("Remote storage type requires a backend")

    def get(self) -> str:
        """
        Get the resolved value.

        Returns:
            str: The resolved value

        Raises:
            ValueError: If value is not set for local storage
            RuntimeError: If backend operation fails
        """
        if self.storage_type == "local":
            if self._value is None:
                raise ValueError(f"No value set for {self.path} in {self.environment}")
            return self._value

        if not self._backend:
            raise RuntimeError("Backend not configured for remote storage")

        return self._backend.get_value(self._generate_key())

    def set(self, value: str) -> None:
        """
        Set the value in appropriate storage.

        Args:
            value: The value to store

        Raises:
            ValueError: If value is not a string
            RuntimeError: If backend operation fails
        """
        if not isinstance(value, str):
            raise ValueError("Value must be a string")

        if self.storage_type == "local":
            self._value = value
        else:
            if not self._backend:
                raise RuntimeError("Backend not configured for remote storage")
            self._backend.set_value(self._generate_key(), value)

    def _generate_key(self) -> str:
        """
        Generate a unique key for remote storage.

        Returns:
            str: A unique key combining path and environment
        """
        return f"{self.path}:{self.environment}"

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the value configuration to a dictionary.

        Returns:
            dict: Serialized representation of the value containing:
                - path: The configuration path
                - environment: The environment name
                - storage_type: Type of storage (local/remote)
                - value: The actual value for local storage
        """
        return {
            "path": self.path,
            "environment": self.environment,
            "storage_type": self.storage_type,
            "value": self._value if self.storage_type == "local" else None,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any], backend: Optional[ValueBackend] = None) -> "Value":
        """
        Create a Value instance from a dictionary representation.

        Args:
            data: Dictionary containing value configuration including:
                - path: The configuration path
                - environment: The environment name
                - storage_type: Type of storage (local/remote)
                - value: The actual value for local storage
            backend: Optional backend for remote storage

        Returns:
            Value: New Value instance

        Raises:
            ValueError: If required data is missing or invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        if "path" not in data:
            raise ValueError("Missing required field: path")
        if "environment" not in data:
            raise ValueError("Missing required field: environment")

        storage_type = data.get("storage_type", "local")
        value = data.get("value")

        return Value(
            path=data["path"],
            environment=data["environment"],
            storage_type=storage_type,
            _backend=backend,
            _value=value if storage_type == "local" else None,
        )
