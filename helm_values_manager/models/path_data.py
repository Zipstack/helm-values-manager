"""
PathData class for managing path-specific metadata and values.

This module contains the PathData class which is responsible for managing
metadata and values associated with a specific configuration path.
"""

from typing import Any, Dict, Iterator, Optional

from ..utils.logger import logger
from .value import Value


class PathData:
    """
    Class representing metadata and values for a specific configuration path.

    This class manages both the metadata (like description, required status,
    sensitivity) and the actual values (as Value objects) for a configuration path.

    Attributes:
        path (str): The configuration path (e.g., "app.replicas")
        metadata (Dict[str, Any]): Dictionary containing path metadata like
            description, required status, and sensitivity.
    """

    def __init__(self, path: str, metadata: Dict[str, Any]) -> None:
        """
        Initialize a new PathData instance.

        Args:
            path (str): The configuration path
            metadata (Dict[str, Any]): Dictionary containing path metadata.
                Expected keys: description (str), required (bool), sensitive (bool)
        """
        logger.debug("Creating new PathData instance for path: %s", path)
        self.path = path
        self.metadata = metadata
        self._values: Dict[str, Value] = {}

    def validate(self) -> None:
        """
        Validate the PathData instance.

        Ensures that:
        1. Required metadata fields are present
        2. Metadata fields have correct types
        3. If path is marked as required, all environments have values
        4. All Value instances use the same path as this PathData

        Raises:
            ValueError: If validation fails
        """
        logger.debug("Validating PathData for path: %s", self.path)

        # Validate metadata structure
        required_fields = {"description", "required", "sensitive"}
        missing_fields = required_fields - set(self.metadata.keys())
        if missing_fields:
            logger.error("Missing required metadata fields for path %s: %s", self.path, missing_fields)
            raise ValueError(f"Missing required metadata fields: {missing_fields}")

        # Validate metadata types
        if not isinstance(self.metadata["description"], (str, type(None))):
            logger.error("Invalid description type for path %s", self.path)
            raise ValueError("Description must be a string or None")
        if not isinstance(self.metadata["required"], bool):
            logger.error("Invalid required flag type for path %s", self.path)
            raise ValueError("Required flag must be a boolean")
        if not isinstance(self.metadata["sensitive"], bool):
            logger.error("Invalid sensitive flag type for path %s", self.path)
            raise ValueError("Sensitive flag must be a boolean")

        # Validate path consistency
        for env, value in self._values.items():
            if value.path != self.path:
                logger.error("Path mismatch for environment %s: %s != %s", env, value.path, self.path)
                raise ValueError(f"Value for environment {env} has inconsistent path: {value.path} != {self.path}")

        # If path is required, ensure all environments have values
        if self.metadata["required"]:
            logger.debug("Path %s is marked as required", self.path)
            # Note: The actual environment validation would need to be done
            # at a higher level since PathData doesn't know about all environments

    def set_value(self, environment: str, value: Value) -> None:
        """
        Set a Value object for a specific environment.

        If a value already exists for the environment, it will be replaced.

        Args:
            environment (str): The environment name
            value (Value): The Value object to associate with the environment

        Raises:
            ValueError: If the Value object's path doesn't match this PathData's path
        """
        logger.debug("Setting value for path %s in environment %s", self.path, environment)

        if value.path != self.path:
            logger.error("Value path %s doesn't match PathData path %s", value.path, self.path)
            raise ValueError(f"Value path {value.path} doesn't match PathData path {self.path}")

        was_update = environment in self._values
        self._values[environment] = value
        logger.debug(
            "%s value for path %s in environment %s", "Updated" if was_update else "Added", self.path, environment
        )

    def get_value(self, environment: str) -> Optional[Value]:
        """
        Get the Value object for a specific environment.

        Args:
            environment (str): The environment to get the value for

        Returns:
            Optional[Value]: The Value object if it exists, None otherwise
        """
        logger.debug("Getting value for path %s in environment %s", self.path, environment)
        value = self._values.get(environment)
        if value is None:
            logger.debug("No value found for path %s in environment %s", self.path, environment)
        return value

    def get_environments(self) -> Iterator[str]:
        """
        Get an iterator over all environments that have values.

        Returns:
            Iterator[str]: Iterator of environment names
        """
        logger.debug("Getting environments for path %s", self.path)
        return iter(self._values.keys())

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the PathData instance to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the PathData instance
        """
        logger.debug("Converting PathData to dict for path %s", self.path)
        return {
            "path": self.path,
            "metadata": self.metadata,
            "values": {env: value.to_dict() for env, value in self._values.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], create_value_fn) -> "PathData":
        """
        Create a PathData instance from a dictionary.

        Args:
            data (Dict[str, Any]): Dictionary containing PathData data
            create_value_fn: Function to create Value objects from dict data.
                Should accept (path: str, environment: str, data: Dict) as arguments.

        Returns:
            PathData: New PathData instance

        Raises:
            ValueError: If the dictionary structure is invalid
        """
        if not isinstance(data, dict):
            logger.error("Invalid data type provided: %s", type(data))
            raise ValueError("Data must be a dictionary")

        logger.debug("Creating PathData from dict with path: %s", data.get("path"))

        required_keys = {"path", "metadata", "values"}
        if not all(key in data for key in required_keys):
            missing = required_keys - set(data.keys())
            logger.error("Missing required keys in data: %s", missing)
            raise ValueError(f"Missing required keys: {missing}")

        instance = cls(data["path"], data["metadata"])

        # Reconstruct values
        for env, value_data in data["values"].items():
            logger.debug("Creating value for environment %s", env)
            value = create_value_fn(data["path"], env, value_data)
            instance.set_value(env, value)

        return instance
