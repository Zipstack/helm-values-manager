"""A Helm plugin to manage values and secrets across environments."""

__version__ = "0.1.0"
__description__ = "A Helm plugin to manage values and secrets across environments."

from .cli import app


def helm_values_manager():
    """Entry point for the Helm plugin."""
    app()
