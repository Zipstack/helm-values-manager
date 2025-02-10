"""Base module for value storage backends.

This module provides the abstract base class for all value storage backends.
Each backend must implement the key-value interface defined here.
"""

from abc import ABC, abstractmethod


class ValueBackend(ABC):
    """Abstract base class for value storage backends.

    This class defines the interface that all value storage backends must implement.
    Implementations can store values in memory, secret managers, or other storage systems.
    The backend operates on a simple key-value model.
    """

    def __init__(self, auth_config: dict):
        """Initialize the backend with authentication configuration.

        Args:
            auth_config: Optional authentication configuration
        """
        self._validate_auth_config(auth_config)

    def _validate_auth_config(self, auth_config: dict) -> None:
        """Validate the authentication configuration.

        This is an internal method called during initialization.
        Subclasses should override this to implement their specific validation.

        Args:
            auth_config: The authentication configuration to validate
        """
        if auth_config is None or not isinstance(auth_config, dict):
            raise ValueError("Auth config must be a dictionary")

        if "type" not in auth_config:
            raise ValueError("Auth config must contain 'type'")

        if auth_config["type"] not in ["env", "file", "direct", "managed_identity"]:
            raise ValueError(f"Invalid auth type: {auth_config['type']}")

    @abstractmethod
    def get_value(self, key: str) -> str:
        """Get a value from the storage backend.

        Args:
            key: The unique key to retrieve the value for

        Returns:
            The value stored in the backend

        Raises:
            ValueError: If the key doesn't exist
        """
        pass

    @abstractmethod
    def set_value(self, key: str, value: str) -> None:
        """Set a value in the storage backend.

        Args:
            key: The unique key to store the value under
            value: The value to store
        """
        pass
