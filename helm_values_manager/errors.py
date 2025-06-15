"""Centralized error handling utilities for consistent error formatting."""

from typing import Optional

import typer
from rich.console import Console


# Create error console that outputs to stderr
error_console = Console(stderr=True)


class ErrorHandler:
    """Centralized error handler for consistent error formatting."""

    @staticmethod
    def format_error(context: str, message: str) -> str:
        """Format error message in consistent format: Error: [context] - message"""
        return f"Error: [{context}] - {message}"

    @staticmethod
    def print_error(context: str, message: str, exit_code: int = 1) -> None:
        """Print error message and exit with code."""
        formatted = ErrorHandler.format_error(context, message)
        error_console.print(f"[red]{formatted}[/red]")
        raise typer.Exit(exit_code)

    @staticmethod
    def print_warning(message: str) -> None:
        """Print warning message."""
        error_console.print(f"[yellow]Warning:[/yellow] {message}")

    @staticmethod
    def print_errors(errors: list[str], context: Optional[str] = None) -> None:
        """Print multiple errors at once."""
        if not errors:
            return

        if context:
            error_console.print(f"\n[red]Error: [{context}] - Validation failed:[/red]")
        else:
            error_console.print("\n[red]Error: Validation failed:[/red]")

        for error in errors:
            # Escape brackets for Rich formatting
            safe_error = error.replace("[", "\\[").replace("]", "\\]")
            error_console.print(f"  • {safe_error}")

        error_console.print()  # Empty line for readability
        raise typer.Exit(1)

    @staticmethod
    def suggest_solution(error_message: str) -> Optional[str]:
        """Return suggested solution for common errors."""
        suggestions = {
            "No schema.json found": "Run 'helm values-manager init' to create a schema file",
            "not found in schema": "Add the key to schema using 'helm values-manager schema add'",
            "Environment variable": "Set the environment variable or use a different secret type",
            "Missing required value": "Set the value using 'helm values-manager values set'",
            "already exists": "Use --force flag to overwrite, or choose a different key",
            "Type mismatch": "Check the expected type in schema using 'helm values-manager schema get'",
        }

        for pattern, suggestion in suggestions.items():
            if pattern in error_message:
                return suggestion

        return None

    @staticmethod
    def handle_exception(e: Exception, context: str) -> None:
        """Handle exceptions with consistent formatting."""
        message = str(e)

        # Add suggestion if available
        suggestion = ErrorHandler.suggest_solution(message)
        if suggestion:
            message = f"{message}\n  Suggestion: {suggestion}"

        ErrorHandler.print_error(context, message)


class HelmValuesError(Exception):
    """Base exception for helm-values-manager."""

    pass


class SchemaError(HelmValuesError):
    """Exception for schema-related errors."""

    pass


class ValuesError(HelmValuesError):
    """Exception for values-related errors."""

    pass


class GeneratorError(HelmValuesError):
    """Exception for generation-related errors."""

    pass


class ValidationError(HelmValuesError):
    """Exception for validation-related errors."""

    pass
