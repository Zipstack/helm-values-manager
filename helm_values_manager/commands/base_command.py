"""Base command class for helm-values plugin."""

import fcntl
import json
import os
from typing import Any, Optional

from jsonschema.exceptions import ValidationError

from helm_values_manager.models.helm_values_config import HelmValuesConfig
from helm_values_manager.utils.logger import HelmLogger


class BaseCommand:
    """Base class for all helm-values commands.

    This class provides common functionality for all commands including:
    - Configuration loading and saving
    - Error handling and logging
    - Lock management for concurrent access
    """

    def __init__(self) -> None:
        """Initialize the base command."""
        self.config_file = "helm-values.json"
        self.lock_file = ".helm-values.lock"
        self._lock_fd: Optional[int] = None

    def _load_config_file(self) -> dict:
        """Load and parse the configuration file.

        Returns:
            dict: The parsed configuration data

        Raises:
            FileNotFoundError: If the config file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        if not os.path.exists(self.config_file):
            HelmLogger.error("Configuration file %s not found", self.config_file)
            raise FileNotFoundError(f"Configuration file {self.config_file} not found")

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            HelmLogger.error("Failed to parse configuration file: %s", e)
            raise

    def load_config(self) -> HelmValuesConfig:
        """Load the helm-values configuration from disk.

        Returns:
            HelmValuesConfig: The loaded configuration.

        Raises:
            FileNotFoundError: If the config file doesn't exist.
            json.JSONDecodeError: If the file contains invalid JSON.
            ValidationError: If the configuration format is invalid.
        """
        data = self._load_config_file()
        try:
            return HelmValuesConfig.from_dict(data)
        except ValidationError as e:
            HelmLogger.error("Invalid configuration format: %s", e)
            raise

    def save_config(self, config: HelmValuesConfig) -> None:
        """Save the helm-values configuration to disk.

        Args:
            config: The configuration to save.

        Raises:
            IOError: If unable to write to the file.
            ValueError: If the configuration is invalid.
        """
        # Validate the config before saving
        config.validate()

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, indent=2)
        except IOError as e:
            HelmLogger.error("Failed to save configuration: %s", e)
            raise

    def acquire_lock(self) -> None:
        """Acquire an exclusive lock for file operations.

        This ensures thread-safe operations when multiple commands
        are trying to modify the configuration.

        Raises:
            IOError: If unable to acquire the lock.
        """
        self._lock_fd = os.open(self.lock_file, os.O_CREAT | os.O_RDWR)
        try:
            fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            HelmLogger.debug("Acquired lock on file %s", self.lock_file)
        except IOError:
            os.close(self._lock_fd)
            self._lock_fd = None
            HelmLogger.error("Unable to acquire lock. Another command may be running.")
            raise IOError("Unable to acquire lock. Another command may be running.")

    def release_lock(self) -> None:
        """Release the exclusive lock."""
        if self._lock_fd is not None:
            fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
            os.close(self._lock_fd)
            self._lock_fd = None
            HelmLogger.debug("Released lock on file %s", self.lock_file)

    def execute(self, **kwargs) -> Any:
        """Execute the command.

        This is the main entry point for running a command.
        It handles:
        1. Lock acquisition
        2. Configuration loading (if needed)
        3. Command execution via run()
        4. Lock release

        Args:
            **kwargs: Command-specific keyword arguments

        Returns:
            Any: The result of the command execution.

        Raises:
            Exception: If any error occurs during command execution.
        """
        try:
            self.acquire_lock()
            config = None
            if not getattr(self, "skip_config_load", False):
                config = self.load_config()
            result = self.run(config=config, **kwargs)
            return result
        finally:
            self.release_lock()

    def run(self, config: Optional[HelmValuesConfig] = None, **kwargs) -> Any:
        """Run the command-specific logic.

        This method should be implemented by each specific command subclass
        to perform its unique functionality.

        Args:
            config: The loaded configuration, or None if skip_config_load is True
            **kwargs: Command-specific keyword arguments

        Returns:
            Any: The result of running the command.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement run()")
