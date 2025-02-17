"""
Logger utility for Helm Values Manager.

This module provides a Helm-style logger that respects HELM_DEBUG environment variable
and follows Helm plugin conventions for output.
"""

import os
import sys
from typing import Any


class HelmLogger:
    """
    Logger class that follows Helm plugin conventions.

    This logger:
    1. Writes debug messages only when HELM_DEBUG is set
    2. Writes all messages to stderr (Helm convention)
    3. Uses string formatting for better performance
    4. Provides consistent error and debug message formatting
    """

    @staticmethod
    def debug(msg: str, *args: Any) -> None:
        """
        Print debug message if HELM_DEBUG is set.

        Args:
            msg: Message with optional string format placeholders
            args: Values to substitute in the message
        """
        if os.environ.get("HELM_DEBUG"):
            if args:
                msg = msg % args
            print("[debug] %s" % msg, file=sys.stderr)

    @staticmethod
    def error(msg: str, *args: Any) -> None:
        """
        Print error message to stderr.

        Args:
            msg: Message with optional string format placeholders
            args: Values to substitute in the message
        """
        if args:
            msg = msg % args
        print("Error: %s" % msg, file=sys.stderr)
