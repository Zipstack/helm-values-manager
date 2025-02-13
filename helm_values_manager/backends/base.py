"""Base module for value storage backends.

This module provides the abstract base class for all value storage backends.
Each backend must implement the path-based interface defined here.
"""

from abc import ABC, abstractmethod
from typing import Dict


class ValueBackend(ABC):
    """Abstract base class for value storage backends.

    This class defines the interface that all value storage backends must implement.
    Each backend is responsible for storing and retrieving values securely using
    their respective storage systems (e.g., AWS Secrets Manager, Azure Key Vault).

    The backend operates on a path-based model where:
    - Values are identified by their path and environment
    - Values are strings that may be encrypted depending on the backend
    """

    def __init__(self, auth_config: Dict[str, str]) -> None:
        """Initialize the backend with authentication configuration.

        Args:
            auth_config: Authentication configuration for the backend.
                Must contain a 'type' key with one of the following values:
                - 'env': Use environment variables
                - 'file': Use configuration file
                - 'direct': Use direct credentials
                - 'managed_identity': Use cloud managed identity

        Raises:
            ValueError: If the auth_config is invalid
        """
        self._validate_auth_config(auth_config)

    def _validate_auth_config(self, auth_config: Dict[str, str]) -> None:
        """Validate the authentication configuration.

        This is an internal method called during initialization.
        Subclasses should override this to implement their specific validation.

        Args:
            auth_config: The authentication configuration to validate

        Raises:
            ValueError: If the auth_config is invalid with a descriptive message
        """
        if not isinstance(auth_config, dict):
            raise ValueError("Auth config must be a dictionary")

        if "type" not in auth_config:
            raise ValueError("Auth config must contain 'type' field")

        valid_types = ["env", "file", "direct", "managed_identity"]
        if auth_config["type"] not in valid_types:
            raise ValueError(f"Invalid auth type: {auth_config['type']}. " f"Must be one of: {', '.join(valid_types)}")

    @abstractmethod
    def get_value(self, path: str, environment: str) -> str:
        """Get a value from the storage backend.

        Args:
            path: The configuration path (e.g., "app.replicas")
            environment: The environment name (e.g., "dev", "prod")

        Returns:
            str: The value stored in the backend.

        Raises:
            ValueError: If the value doesn't exist
            ConnectionError: If there's an error connecting to the backend
            PermissionError: If there's an authentication or authorization error
        """
        pass

    @abstractmethod
    def set_value(self, path: str, environment: str, value: str) -> None:
        """Set a value in the storage backend.

        Args:
            path: The configuration path (e.g., "app.replicas")
            environment: The environment name (e.g., "dev", "prod")
            value: The value to store. Must be a string.

        Raises:
            ValueError: If the value is invalid
            ConnectionError: If there's an error connecting to the backend
            PermissionError: If there's an authentication or authorization error
        """
        pass

    @abstractmethod
    def remove_value(self, path: str, environment: str) -> None:
        """Remove a value from the storage backend.

        Args:
            path: The configuration path (e.g., "app.replicas")
            environment: The environment name (e.g., "dev", "prod")

        Raises:
            ValueError: If the value doesn't exist
            ConnectionError: If there's an error connecting to the backend
            PermissionError: If there's an authentication or authorization error
        """
        pass
