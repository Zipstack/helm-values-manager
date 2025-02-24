"""Command registry for managing helm-values commands."""

from typing import Dict, Type

from helm_values_manager.commands.base_command import BaseCommand


class CommandRegistry:
    """Registry for managing helm-values commands.

    This class provides a central registry for all available commands in the
    helm-values plugin. It handles command registration and lookup.
    """

    _instance = None
    _commands: Dict[str, Type[BaseCommand]] = {}

    def __new__(cls):
        """Create a new singleton instance of CommandRegistry."""
        if cls._instance is None:
            cls._instance = super(CommandRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, name: str, command_class: Type[BaseCommand]) -> None:
        """Register a new command.

        Args:
            name: The name of the command
            command_class: The command class to register

        Raises:
            ValueError: If a command with the same name already exists
        """
        if name in cls._commands:
            raise ValueError(f"Command {name} already registered")
        cls._commands[name] = command_class

    @classmethod
    def get_command(cls, name: str) -> Type[BaseCommand]:
        """Get a command by name.

        Args:
            name: The name of the command to get

        Returns:
            The command class

        Raises:
            KeyError: If the command is not found
        """
        if name not in cls._commands:
            raise KeyError(f"Command {name} not found")
        return cls._commands[name]

    @classmethod
    def list_commands(cls) -> Dict[str, Type[BaseCommand]]:
        """List all registered commands.

        Returns:
            A dictionary mapping command names to command classes
        """
        return cls._commands.copy()

    @classmethod
    def clear(cls) -> None:
        """Clear all registered commands.

        This is primarily used for testing.
        """
        cls._commands.clear()
