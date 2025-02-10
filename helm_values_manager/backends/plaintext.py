"""PlainText backend for value storage.

This module provides a simple in-memory key-value store implementation.
It is suitable for development and testing environments.
"""

from typing import Dict

from .base import ValueBackend


class PlainTextBackend(ValueBackend):
    """A backend that stores values in memory.

    This backend is suitable for development and testing environments.
    Values are stored in memory and will be lost when the process exits.
    """

    def __init__(self, auth_config: dict = None):
        """Initialize the backend.

        Args:
            auth_config: Optional authentication configuration (not used)
        """
        self._values: Dict[str, str] = {}
        super().__init__(auth_config)

    def _validate_auth_config(self, auth_config: dict) -> None:
        """Validate the authentication configuration.

        For PlainTextBackend, no authentication is required.
        Any auth config will pass validation.

        Args:
            auth_config: The authentication configuration to validate
        """
        pass  # No validation needed for plain text backend

    def get_value(self, key: str) -> str:
        """Get a value from memory.

        Args:
            key: The key to retrieve the value for

        Returns:
            The stored value

        Raises:
            ValueError: If the key doesn't exist
        """
        if key not in self._values:
            raise ValueError(f"Key not found: {key}")

        return self._values[key]

    def set_value(self, key: str, value: str) -> None:
        """Set a value in memory.

        Args:
            key: The key to store the value under
            value: The value to store
        """
        self._values[key] = value
