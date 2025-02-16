"""
Value class implementation for Helm Values Manager.

This module provides the Value class which encapsulates the storage and resolution
of configuration values using the appropriate backend.
"""

from dataclasses import dataclass
from typing import Any, Dict

from ..backends.base import ValueBackend
from ..utils.logger import logger


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

    def __post_init__(self):
        """Post-initialization validation and logging."""
        logger.debug("Created Value instance for path %s in environment %s", self.path, self.environment)

    def get(self, resolve: bool = False) -> str:
        """
        Get the value.

        Args:
            resolve (bool): If True, resolve any secret references to their actual values.
                          If False, return the raw value which may be a secret reference.

        Returns:
            str: The value (resolved or raw depending on resolve parameter)

        Raises:
            ValueError: If value doesn't exist
            RuntimeError: If backend operation fails
        """
        logger.debug("Getting value for path %s in environment %s", self.path, self.environment)
        try:
            value = self._backend.get_value(self.path, self.environment, resolve)
            logger.debug("Successfully retrieved value for path %s", self.path)
            return value
        except Exception as e:
            logger.error("Failed to get value for path %s in environment %s: %s", self.path, self.environment, str(e))
            raise

    def set(self, value: str) -> None:
        """
        Set the value using the backend.

        Args:
            value: The value to store, can be a raw value or a secret reference

        Raises:
            ValueError: If value is not a string
            RuntimeError: If backend operation fails
        """
        if not isinstance(value, str):
            raise ValueError("Value must be a string")

        logger.debug("Setting value for path %s in environment %s", self.path, self.environment)
        try:
            self._backend.set_value(self.path, self.environment, value)
            logger.debug("Successfully set value for path %s", self.path)
        except Exception as e:
            logger.error("Failed to set value for path %s in environment %s: %s", self.path, self.environment, str(e))
            raise

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Value instance to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the Value instance
        """
        logger.debug("Converting Value to dict for path %s", self.path)
        return {"path": self.path, "environment": self.environment, "backend_type": self._backend.backend_type}

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
