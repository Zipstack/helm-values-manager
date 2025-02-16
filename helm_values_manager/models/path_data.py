"""
Module for managing path data and associated metadata.

This module contains the PathData class which is responsible for managing
metadata and values associated with a specific configuration path.
"""

from typing import Any, Callable, Dict, Iterator, Optional

from helm_values_manager.models.value import Value
from helm_values_manager.utils.logger import logger


class PathData:
    """Manages metadata and values for a configuration path."""

    def __init__(self, path: str, metadata: Dict[str, Any]):
        """
        Initialize PathData with a path and metadata.

        Args:
            path: The configuration path
            metadata: Dictionary containing metadata fields
        """
        self.path = path
        self.metadata = metadata
        self._values: Dict[str, Value] = {}

    def validate(self) -> None:
        """
        Validate the PathData instance.

        Ensures that:
        1. All Value instances use the same path as this PathData
        2. If path is marked as required, each environment has a non-empty value

        Raises:
            ValueError: If validation fails
        """
        logger.debug("Validating PathData for path: %s", self.path)

        # Validate path consistency and required values
        for env, value in self._values.items():
            # Check path consistency
            if value.path != self.path:
                logger.error("Path mismatch for environment %s: %s != %s", env, value.path, self.path)
                raise ValueError(f"Value for environment {env} has inconsistent path: {value.path} != {self.path}")

            # Check required values
            if self.metadata.get("required", False):
                val = value.get()
                if val is None or val == "":
                    logger.error("Missing required value for path %s in environment %s", self.path, env)
                    raise ValueError(f"Missing required value for path {self.path} in environment {env}")

    def set_value(self, environment: str, value: Value) -> None:
        """
        Set a Value object for a specific environment.

        Args:
            environment (str): The environment to set the value for
            value (Value): The Value object to set

        Raises:
            ValueError: If the Value object's path doesn't match this PathData's path
        """
        logger.debug("Setting value for path %s in environment %s", self.path, environment)

        if value.path != self.path:
            logger.error("Value path %s doesn't match PathData path %s", value.path, self.path)
            raise ValueError(f"Value path {value.path} doesn't match PathData path {self.path}")

        self._values[environment] = value

    def get_value(self, environment: str, resolve: bool = False) -> Optional[str]:
        """
        Get the value for a specific environment.

        Args:
            environment: The environment to get the value for
            resolve: Whether to resolve the value (for sensitive values)

        Returns:
            Optional[str]: The value if found, None otherwise
        """
        logger.debug("Getting value for path %s in environment %s", self.path, environment)
        value = self._values.get(environment)
        if value is None:
            logger.debug("No value found for path %s in environment %s", self.path, environment)
            return None

        return value.get(resolve=resolve)

    def get_environments(self) -> Iterator:
        """
        Get all environment names that have values.

        Returns:
            Iterator: Iterator of environment names
        """
        return iter(self._values.keys())

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert PathData to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of PathData
        """
        return {
            "path": self.path,
            "metadata": self.metadata,
            "values": {env: value.to_dict() for env, value in self._values.items()},
        }

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], create_value_fn: Callable[[str, str, Dict[str, Any]], Value]
    ) -> "PathData":
        """
        Create a PathData instance from a dictionary.

        Args:
            data (Dict[str, Any]): Dictionary containing PathData data
            create_value_fn: Function to create Value instances. Takes (path, env, value_data) and returns Value

        Returns:
            PathData: New PathData instance
        """
        path_data = cls(path=data["path"], metadata=data["metadata"])

        # Create Value instances for each environment
        for env, value_data in data.get("values", {}).items():
            value = create_value_fn(data["path"], env, value_data)
            path_data.set_value(env, value)

        return path_data
