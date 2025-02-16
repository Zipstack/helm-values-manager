"""
Simple value backend implementation for non-sensitive values.

This module provides a simple in-memory backend for storing non-sensitive values.
"""

from typing import Dict

from helm_values_manager.backends.base import ValueBackend


class SimpleValueBackend(ValueBackend):
    """
    A simple in-memory backend for storing non-sensitive values.

    This backend is used by default for any values marked as non-sensitive.
    """

    def __init__(self) -> None:
        """Initialize an empty in-memory storage."""
        super().__init__({"type": "direct"})  # Simple backend doesn't need auth
        self._storage: Dict[str, str] = {}

    def _get_storage_key(self, path: str, environment: str) -> str:
        """Generate a unique storage key."""
        return f"{path}:{environment}"

    def get_value(self, path: str, environment: str, resolve: bool = False) -> str:
        """
        Get a value from the in-memory storage.

        Args:
            path: The configuration path (e.g., "app.replicas")
            environment: The environment name (e.g., "dev", "prod")
            resolve: If True, resolve any secret references to their actual values.
                    If False, return the raw value which may be a secret reference.

        Returns:
            str: The value (resolved or raw depending on resolve parameter)

        Raises:
            ValueError: If the value doesn't exist
        """
        key = self._get_storage_key(path, environment)
        if key not in self._storage:
            raise ValueError(f"No value found for {path} in {environment}")
        return self._storage[key]

    def set_value(self, path: str, environment: str, value: str) -> None:
        """
        Set a value in the in-memory storage.

        Args:
            path: The configuration path (e.g., "app.replicas")
            environment: The environment name (e.g., "dev", "prod")
            value: The value to store

        Raises:
            ValueError: If the value is not a string
        """
        if not isinstance(value, str):
            raise ValueError("Value must be a string")
        key = self._get_storage_key(path, environment)
        self._storage[key] = value

    def remove_value(self, path: str, environment: str) -> None:
        """
        Remove a value from the in-memory storage.

        Args:
            path: The configuration path (e.g., "app.replicas")
            environment: The environment name (e.g., "dev", "prod")

        Raises:
            ValueError: If the value doesn't exist
        """
        key = self._get_storage_key(path, environment)
        if key not in self._storage:
            raise ValueError(f"No value found for {path} in {environment}")
        del self._storage[key]
