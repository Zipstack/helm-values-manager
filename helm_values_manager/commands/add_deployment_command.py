"""Command to add a new deployment configuration."""

from typing import Optional

from helm_values_manager.commands.base_command import BaseCommand
from helm_values_manager.models.constants import NO_AUTH, NO_BACKEND
from helm_values_manager.models.helm_values_config import Deployment, HelmValuesConfig
from helm_values_manager.utils.logger import HelmLogger


class AddDeploymentCommand(BaseCommand):
    """Command to add a new deployment configuration."""

    def run(self, config: Optional[HelmValuesConfig] = None, **kwargs) -> str:
        """
        Add a new deployment configuration.

        Args:
            config: The loaded configuration
            **kwargs: Command arguments
                - name (str): The deployment name (e.g., 'dev', 'prod')

        Returns:
            str: Success message

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        if config is None:
            raise ValueError("Configuration not loaded")

        # Extract required parameters
        name = kwargs.get("name")
        if not name:
            raise ValueError("Deployment name cannot be empty")

        # Check if deployment already exists
        if name in config.deployments:
            raise ValueError(f"Deployment '{name}' already exists")

        # Create and add the deployment with minimal configuration
        # Backend and auth will be added later with separate commands
        deployment = Deployment(
            name=name,
            backend=NO_BACKEND,  # Default to NO_BACKEND, will be updated by add-backend command
            auth={"type": NO_AUTH},  # Default to NO_AUTH, will be updated by add-auth command
            backend_config={},  # Empty dict instead of None
        )

        # Add deployment to config
        config.deployments[name] = deployment

        # Save the updated configuration
        self.save_config(config)

        HelmLogger.debug("Added deployment '%s'", name)
        return f"Successfully added deployment '{name}'"
