"""Unit tests for the command registry."""

import pytest

from helm_values_manager.commands.base_command import BaseCommand
from helm_values_manager.commands.registry import CommandRegistry


class DummyCommand(BaseCommand):
    """Dummy command class for testing."""

    def run(self, config):
        """Run the command."""
        return "test"


def test_singleton_instance():
    """Test that CommandRegistry is a singleton."""
    registry1 = CommandRegistry()
    registry2 = CommandRegistry()
    assert registry1 is registry2


def test_register_command():
    """Test registering a command."""
    CommandRegistry.clear()
    CommandRegistry.register("test", DummyCommand)
    assert "test" in CommandRegistry.list_commands()
    assert CommandRegistry.list_commands()["test"] == DummyCommand


def test_register_duplicate_command():
    """Test registering a duplicate command."""
    CommandRegistry.clear()
    CommandRegistry.register("test", DummyCommand)
    with pytest.raises(ValueError, match="Command test already registered"):
        CommandRegistry.register("test", DummyCommand)


def test_get_command():
    """Test getting a command."""
    CommandRegistry.clear()
    CommandRegistry.register("test", DummyCommand)
    assert CommandRegistry.get_command("test") == DummyCommand


def test_get_nonexistent_command():
    """Test getting a nonexistent command."""
    CommandRegistry.clear()
    with pytest.raises(KeyError, match="Command test not found"):
        CommandRegistry.get_command("test")


def test_list_commands():
    """Test listing commands."""
    CommandRegistry.clear()
    CommandRegistry.register("test1", DummyCommand)
    CommandRegistry.register("test2", DummyCommand)
    commands = CommandRegistry.list_commands()
    assert len(commands) == 2
    assert "test1" in commands
    assert "test2" in commands
    assert commands["test1"] == DummyCommand
    assert commands["test2"] == DummyCommand


def test_clear_commands():
    """Test clearing commands."""
    CommandRegistry.register("test", DummyCommand)
    CommandRegistry.clear()
    assert len(CommandRegistry.list_commands()) == 0
