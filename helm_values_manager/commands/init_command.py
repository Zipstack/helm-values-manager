"""Command to initialize a new helm-values configuration."""

import os
from typing import Optional

from helm_values_manager.commands.base_command import BaseCommand
from helm_values_manager.models.helm_values_config import HelmValuesConfig
from helm_values_manager.utils.logger import HelmLogger


class InitCommand(BaseCommand):
    """Command to initialize a new helm-values configuration."""

    def __init__(self) -> None:
        """Initialize the init command."""
        super().__init__()
        self.skip_config_load = True

    def run(self, config: Optional[HelmValuesConfig] = None, **kwargs) -> str:
        """
        Initialize a new helm-values configuration.

        Args:
            config: Not used by this command
            **kwargs: Command arguments
                - release_name (str): Name of the Helm release

        Returns:
            str: Success message

        Raises:
            FileExistsError: If configuration file already exists
            ValueError: If release name is invalid
        """
        release_name = kwargs.get("release_name")
        if not release_name:
            raise ValueError("Release name cannot be empty")

        # Check if config file already exists
        if os.path.exists(self.config_file):
            raise FileExistsError(f"Configuration file {self.config_file} already exists")

        # Create new config
        new_config = HelmValuesConfig()
        new_config.version = "1.0"
        new_config.release = release_name

        # Save config
        self.save_config(new_config)

        HelmLogger.debug("Initialized helm-values configuration for release: %s", release_name)
        return "Successfully initialized helm-values configuration."
