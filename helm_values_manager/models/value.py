"""
Value class implementation for Helm Values Manager.

This module provides the Value class which encapsulates the storage and resolution
of configuration values using the appropriate backend.
"""

from dataclasses import dataclass
from typing import Any, Dict

from ..backends.base import ValueBackend


@dataclass
class Value:
    """
    Represents a configuration value with its storage backend.

    Attributes:
        path: The configuration path (e.g., "app.replicas")
        environment: The environment name (e.g., "dev", "prod")
        _backend: The backend used for storing and retrieving values
    """

    path: str
    environment: str
    _backend: ValueBackend

    def get(self) -> str:
        """
        Get the resolved value.

        Returns:
            str: The resolved value

        Raises:
            ValueError: If value doesn't exist
            RuntimeError: If backend operation fails
        """
        return self._backend.get_value(self.path, self.environment)

    def set(self, value: str) -> None:
        """
        Set the value using the backend.

        Args:
            value: The value to store

        Raises:
            ValueError: If value is not a string
            RuntimeError: If backend operation fails
        """
        if not isinstance(value, str):
            raise ValueError("Value must be a string")
        self._backend.set_value(self.path, self.environment, value)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the value configuration to a dictionary.

        Returns:
            dict: Serialized representation of the value containing:
                - path: The configuration path
                - environment: The environment name
        """
        return {
            "path": self.path,
            "environment": self.environment,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any], backend: ValueBackend) -> "Value":
        """
        Create a Value instance from a dictionary representation.

        Args:
            data: Dictionary containing value configuration including:
                - path: The configuration path
                - environment: The environment name
            backend: The backend to use for this value

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

        return Value(
            path=data["path"],
            environment=data["environment"],
            _backend=backend,
        )
