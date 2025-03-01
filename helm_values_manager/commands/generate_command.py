"""Command to generate values file for a specific deployment."""

import os
from typing import Any, Dict, Optional

import yaml

from helm_values_manager.commands.base_command import BaseCommand
from helm_values_manager.models.helm_values_config import HelmValuesConfig
from helm_values_manager.utils.logger import HelmLogger


class GenerateCommand(BaseCommand):
    """Command to generate values file for a specific deployment."""

    def run(self, config: Optional[HelmValuesConfig] = None, **kwargs) -> str:
        """
        Generate a values file for a specific deployment.

        Args:
            config: The loaded configuration
            **kwargs: Command arguments
                - deployment (str): The deployment to generate values for (e.g., 'dev', 'prod')
                - output_path (str, optional): Directory to output the values file to

        Returns:
            str: Success message with the path to the generated file

        Raises:
            ValueError: If deployment is empty
            KeyError: If deployment doesn't exist in the configuration
            FileNotFoundError: If the configuration file doesn't exist
        """
        if config is None:
            raise ValueError("Configuration not loaded")

        deployment = kwargs.get("deployment")
        if not deployment:
            raise ValueError("Deployment cannot be empty")

        output_path = kwargs.get("output_path", ".")

        # Validate that the deployment exists
        if deployment not in config.deployments:
            raise KeyError(f"Deployment '{deployment}' not found")

        # Create output directory if it doesn't exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            HelmLogger.debug("Created output directory: %s", output_path)

        # Generate values dictionary from configuration
        values_dict = self._generate_values_dict(config, deployment)

        # Generate filename based on deployment and release
        filename = f"{deployment}.{config.release}.values.yaml"
        file_path = os.path.join(output_path, filename)

        # Write values to file
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(values_dict, f, default_flow_style=False)

        HelmLogger.debug("Generated values file for deployment '%s' at '%s'", deployment, file_path)
        return f"Successfully generated values file for deployment '{deployment}' at '{file_path}'"

    def _generate_values_dict(self, config: HelmValuesConfig, deployment: str) -> Dict[str, Any]:
        """
        Generate a nested dictionary of values from the configuration.

        Args:
            config: The loaded configuration
            deployment: The deployment to generate values for

        Returns:
            Dict[str, Any]: Nested dictionary of values

        Raises:
            ValueError: If a required value is missing for the deployment
        """
        values_dict = {}
        missing_required_paths = []

        # Get all paths from the configuration
        for path in config._path_map.keys():
            path_data = config._path_map[path]

            # Check if this is a required value
            is_required = path_data._metadata.required

            # Get the value for this path and deployment
            value = config.get_value(path, deployment, resolve=True)

            # If the value is None and it's required, add to missing list
            if value is None and is_required:
                missing_required_paths.append(path)
                continue

            # Skip if no value is set
            if value is None:
                continue

            # Convert dot-separated path to nested dictionary
            path_parts = path.split(".")
            current_dict = values_dict

            # Navigate to the correct nested level
            for i, part in enumerate(path_parts):
                # If we're at the last part, set the value
                if i == len(path_parts) - 1:
                    current_dict[part] = value
                else:
                    # Create nested dictionary if it doesn't exist
                    if part not in current_dict:
                        current_dict[part] = {}
                    current_dict = current_dict[part]

        # If there are missing required values, raise an error
        if missing_required_paths:
            paths_str = ", ".join(missing_required_paths)
            raise ValueError(f"Missing required values for deployment '{deployment}': {paths_str}")

        return values_dict
