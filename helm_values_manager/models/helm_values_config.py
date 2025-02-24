"""HelmValuesConfig class for managing Helm values and secrets."""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import jsonschema
from jsonschema.exceptions import ValidationError

from helm_values_manager.backends.simple import SimpleValueBackend
from helm_values_manager.models.path_data import PathData
from helm_values_manager.models.value import Value
from helm_values_manager.utils.logger import HelmLogger


@dataclass
class Deployment:
    """Deployment configuration."""

    name: str
    auth: Dict[str, Any]
    backend: str
    backend_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert deployment to dictionary."""
        return {"backend": self.backend, "auth": self.auth, "backend_config": self.backend_config}


class HelmValuesConfig:
    """Configuration manager for Helm values and secrets."""

    def __init__(self):
        """Initialize configuration."""
        self.version: str = "1.0"
        self.release: str = ""
        self.deployments: Dict[str, Deployment] = {}
        self._path_map: Dict[str, PathData] = {}
        self._backend = SimpleValueBackend()  # For non-sensitive values

    @classmethod
    def _load_schema(cls) -> Dict[str, Any]:
        """Load the JSON schema for configuration validation."""
        schema_path = os.path.join(os.path.dirname(__file__), "..", "schemas", "v1.json")
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def _validate_schema(cls, data: dict) -> None:
        """
        Validate data against JSON schema.

        Args:
            data: Dictionary to validate against schema

        Raises:
            ValidationError: If the data does not match the schema
        """
        schema = cls._load_schema()
        try:
            jsonschema.validate(instance=data, schema=schema)
        except ValidationError as e:
            HelmLogger.error("JSON schema validation failed: %s", e)
            raise

    def add_config_path(
        self, path: str, description: Optional[str] = None, required: bool = False, sensitive: bool = False
    ) -> None:
        """
        Add a new configuration path.

        Args:
            path: The configuration path
            description: Description of what this configuration does
            required: Whether this configuration is required
            sensitive: Whether this configuration contains sensitive data
        """
        if path in self._path_map:
            raise ValueError(f"Path {path} already exists")

        metadata = {
            "description": description,
            "required": required,
            "sensitive": sensitive,
        }
        path_data = PathData(path, metadata)
        self._path_map[path] = path_data

    def get_value(self, path: str, environment: str, resolve: bool = False) -> Optional[str]:
        """
        Get a value for the given path and environment.

        Args:
            path: The configuration path
            environment: The environment name
            resolve: If True, resolve any secret references to their actual values.
                    If False, return the raw value which may be a secret reference.

        Returns:
            Optional[str]: The value (resolved or raw depending on resolve parameter), or None if value doesn't exist.

        Raises:
            KeyError: If path doesn't exist
        """
        if path not in self._path_map:
            HelmLogger.debug("Path %s not found in path map", path)
            raise KeyError(f"Path {path} not found")

        path_data = self._path_map[path]
        value_obj = path_data.get_value(environment)
        if value_obj is None:
            HelmLogger.debug("No value object found for path %s in environment %s", path, environment)
            return None

        value = value_obj.get(resolve=resolve)
        if value is None:
            HelmLogger.debug("No value found for path %s in environment %s", path, environment)
            return None

        HelmLogger.debug("Found value for path %s in environment %s", path, environment)
        return value

    def set_value(self, path: str, environment: str, value: str) -> None:
        """Set a value for the given path and environment."""
        if path not in self._path_map:
            raise KeyError(f"Path {path} not found")

        value_obj = Value(path=path, environment=environment, _backend=self._backend)
        value_obj.set(value)
        self._path_map[path].set_value(environment, value_obj)

    def validate(self) -> None:
        """
        Validate the configuration.

        Raises:
            ValueError: If validation fails.
        """
        if not self.release:
            raise ValueError("Release name is required")

        # Validate schema
        self._validate_schema(self.to_dict())

        # Then validate each path_data
        for path_data in self._path_map.values():
            path_data.validate()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return {
            "version": self.version,
            "release": self.release,
            "deployments": {name: depl.to_dict() for name, depl in self.deployments.items()},
            "config": [path_data.to_dict() for path_data in self._path_map.values()],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HelmValuesConfig":
        """
        Create a configuration from a dictionary.

        Args:
            data: Dictionary containing configuration data

        Returns:
            HelmValuesConfig: New configuration instance

        Raises:
            ValidationError: If the configuration data is invalid
        """
        # Validate against schema
        data = data.copy()  # Don't modify the input
        cls._validate_schema(data)

        config = cls()
        config.version = data["version"]
        config.release = data["release"]

        # Load deployments
        for name, depl_data in data.get("deployments", {}).items():
            config.deployments[name] = Deployment(
                name=name,
                backend=depl_data["backend"],
                auth=depl_data["auth"],
                backend_config=depl_data.get("backend_config", {}),
            )

        # Load config paths
        for config_item in data.get("config", []):
            path = config_item["path"]
            metadata = {
                "description": config_item.get("description"),
                "required": config_item.get("required", False),
                "sensitive": config_item.get("sensitive", False),
            }
            path_data = PathData(path, metadata)
            config._path_map[path] = path_data

            # Load values
            for env, value in config_item.get("values", {}).items():
                value_obj = Value(path=path, environment=env, _backend=config._backend)
                value_obj.set(value)
                path_data.set_value(env, value_obj)

        return config
