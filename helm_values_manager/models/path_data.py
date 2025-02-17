"""
Module for managing path data and associated metadata.

This module contains the PathData class which is responsible for managing
metadata and values associated with a specific configuration path.
"""

from typing import Any, Callable, Dict, Iterator, Optional

from helm_values_manager.models.config_metadata import ConfigMetadata
from helm_values_manager.models.value import Value
from helm_values_manager.utils.logger import HelmLogger


class PathData:
    """Manages metadata and values for a configuration path."""

    def __init__(self, path: str, metadata: Dict[str, Any]):
        """
        Initialize PathData with a path and metadata.

        Args:
            path: The configuration path (e.g., "app.replicas")
            metadata: Dictionary containing metadata for the path
        """
        self.path = path
        self._metadata = ConfigMetadata(
            description=metadata.get("description"),
            required=metadata.get("required", False),
            sensitive=metadata.get("sensitive", False),
        )
        self._values: Dict[str, Value] = {}
        HelmLogger.debug("Created PathData instance for path %s", path)

    def validate(self) -> None:
        """
        Validate the PathData instance.

        Ensures that:
        1. All Value instances use the same path as this PathData
        2. If path is marked as required, each environment has a non-empty value

        Raises:
            ValueError: If validation fails
        """
        HelmLogger.debug("Validating PathData for path: %s", self.path)

        # Validate path consistency and required values
        for env, value in self._values.items():
            # Check path consistency
            if value.path != self.path:
                HelmLogger.error("Path mismatch for environment %s: %s != %s", env, value.path, self.path)
                raise ValueError(f"Value for environment {env} has inconsistent path: {value.path} != {self.path}")

            # Check required values
            if self._metadata.required:
                val = value.get()
                if val is None or val == "":
                    HelmLogger.error("Missing required value for path %s in environment %s", self.path, env)
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
        HelmLogger.debug("Setting value for path %s in environment %s", self.path, environment)

        if value.path != self.path:
            HelmLogger.error("Value path %s does not match PathData path %s", value.path, self.path)
            raise ValueError(f"Value path {value.path} does not match PathData path {self.path}")

        self._values[environment] = value

    def get_value(self, environment: str) -> Optional[Value]:
        """
        Get the Value object for a specific environment.

        Args:
            environment (str): The environment to get the value for

        Returns:
            Optional[Value]: The Value object if it exists, None otherwise
        """
        HelmLogger.debug("Getting value for path %s in environment %s", self.path, environment)
        value = self._values.get(environment)
        if value is None:
            HelmLogger.debug("No value found for path %s in environment %s", self.path, environment)
        else:
            HelmLogger.debug("Found value for path %s in environment %s", self.path, environment)
        return value

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
            "description": self._metadata.description,
            "required": self._metadata.required,
            "sensitive": self._metadata.sensitive,
            "values": {env: value.get() for env, value in self._values.items()},
        }

    @property
    def metadata(self) -> ConfigMetadata:
        """
        Get metadata for this path.

        Returns:
            ConfigMetadata: Metadata instance for this path
        """
        return self._metadata

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

        Raises:
            ValueError: If the dictionary structure is invalid
        """
        if not isinstance(data, dict):
            HelmLogger.error("Invalid data type provided: %s", type(data))
            raise ValueError("Data must be a dictionary")

        HelmLogger.debug("Creating PathData from dict with path: %s", data.get("path"))

        required_keys = {"path", "values"}
        if not all(key in data for key in required_keys):
            missing = required_keys - set(data.keys())
            HelmLogger.error("Missing required keys in data: %s", missing)
            raise ValueError(f"Missing required keys: {missing}")

        metadata = {
            "description": data.get("description"),
            "required": data.get("required", False),
            "sensitive": data.get("sensitive", False),
        }
        path_data = cls(path=data["path"], metadata=metadata)

        # Create Value instances for each environment
        for env, value in data.get("values", {}).items():
            HelmLogger.debug("Creating value for environment %s", env)
            value_obj = create_value_fn(data["path"], env, {"value": value})
            path_data.set_value(env, value_obj)

        return path_data
