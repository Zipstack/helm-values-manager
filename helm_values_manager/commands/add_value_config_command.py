"""Command to add a new value configuration with metadata."""

from typing import Optional

from helm_values_manager.commands.base_command import BaseCommand
from helm_values_manager.models.helm_values_config import HelmValuesConfig
from helm_values_manager.utils.logger import HelmLogger


class AddValueConfigCommand(BaseCommand):
    """Command to add a new value configuration with metadata."""

    def run(self, config: Optional[HelmValuesConfig] = None, **kwargs) -> str:
        """
        Add a new value configuration with metadata.

        Args:
            config: The loaded configuration
            **kwargs: Command arguments
                - path (str): The configuration path (e.g., 'app.replicas')
                - description (str, optional): Description of what this configuration does
                - required (bool, optional): Whether this configuration is required
                - sensitive (bool, optional): Whether this configuration contains sensitive data

        Returns:
            str: Success message

        Raises:
            ValueError: If path is invalid or already exists
        """
        if config is None:
            raise ValueError("Configuration not loaded")

        path = kwargs.get("path")
        if not path:
            raise ValueError("Path cannot be empty")

        description = kwargs.get("description")
        required = kwargs.get("required", False)
        sensitive = kwargs.get("sensitive", False)

        try:
            # Add the new configuration path
            config.add_config_path(path=path, description=description, required=required, sensitive=sensitive)

            # Save the updated configuration
            self.save_config(config)

            HelmLogger.debug("Added value config '%s' (required=%s, sensitive=%s)", path, required, sensitive)
            return f"Successfully added value config '{path}'"
        except ValueError as e:
            HelmLogger.error("Failed to add value config: %s", str(e))
            raise
