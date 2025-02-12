"""Tests for the command line interface."""

from typer.testing import CliRunner

from helm_values_manager.cli import app

runner = CliRunner()


def test_main_no_command():
    """Test main function without any subcommand."""
    result = runner.invoke(app)
    assert result.exit_code == 0
    assert "Usage: helm values-manager" in result.stdout


def test_init_command():
    """Test init command."""
    result = runner.invoke(app, ["init", "--release", "test-release"])
    assert result.exit_code == 0
    assert "Initializing values manager" in result.stdout
    assert "test-release" in result.stdout
