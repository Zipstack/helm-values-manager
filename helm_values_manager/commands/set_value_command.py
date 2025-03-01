"""Command to set a value for a specific path and deployment."""

from typing import Optional

from helm_values_manager.commands.base_command import BaseCommand
from helm_values_manager.models.helm_values_config import HelmValuesConfig
from helm_values_manager.utils.logger import HelmLogger


class SetValueCommand(BaseCommand):
    """Command to set a value for a specific path and deployment."""

    def run(self, config: Optional[HelmValuesConfig] = None, **kwargs) -> str:
        """
        Set a value for a specific path and deployment.

        Args:
            config: The loaded configuration
            **kwargs: Command arguments
                - path (str): The configuration path (e.g., 'app.replicas')
                - environment (str): The deployment to set the value for (e.g., 'dev', 'prod')
                - value (str): The value to set

        Returns:
            str: Success message

        Raises:
            ValueError: If path or environment is empty
            KeyError: If path or deployment doesn't exist in the configuration
        """
        if config is None:
            raise ValueError("Configuration not loaded")

        path = kwargs.get("path")
        if not path:
            raise ValueError("Path cannot be empty")

        environment = kwargs.get("environment")
        if not environment:
            raise ValueError("Deployment cannot be empty")

        value = kwargs.get("value")

        # Validate that the deployment exists
        if environment not in config.deployments:
            raise KeyError(f"Deployment '{environment}' not found")

        try:
            # Set the value for the specified path and deployment
            config.set_value(path=path, environment=environment, value=value)

            # Save the updated configuration
            self.save_config(config)

            HelmLogger.debug("Set value for path '%s' in deployment '%s'", path, environment)
            return f"Successfully set value for path '{path}' in deployment '{environment}'"
        except KeyError as e:
            HelmLogger.error("Failed to set value: %s", str(e))
            raise
        except Exception as e:
            HelmLogger.error("Failed to set value: %s", str(e))
            raise
