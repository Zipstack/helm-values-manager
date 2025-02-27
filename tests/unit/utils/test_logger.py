"""Tests for the HelmLogger utility."""

import os
from io import StringIO
from unittest import mock

import pytest

from helm_values_manager.utils.logger import HelmLogger


@pytest.fixture
def logger():
    """Create a HelmLogger instance."""
    return HelmLogger()


def test_debug_with_helm_debug_enabled(logger):
    """Test debug output when HELM_DEBUG is set."""
    stderr = StringIO()
    with (
        mock.patch.dict(os.environ, {"HELM_DEBUG": "1"}),
        mock.patch("helm_values_manager.utils.logger.sys.stderr", stderr),
    ):
        logger.debug("Test message")
        assert stderr.getvalue() == "[debug] Test message\n"


def test_debug_with_helm_debug_disabled(logger):
    """Test debug output when HELM_DEBUG is not set."""
    stderr = StringIO()
    with mock.patch.dict(os.environ, {}), mock.patch("helm_values_manager.utils.logger.sys.stderr", stderr):
        logger.debug("Test message")
        assert stderr.getvalue() == ""


def test_debug_with_formatting(logger):
    """Test debug output with string formatting."""
    stderr = StringIO()
    with (
        mock.patch.dict(os.environ, {"HELM_DEBUG": "1"}),
        mock.patch("helm_values_manager.utils.logger.sys.stderr", stderr),
    ):
        logger.debug("Test %s: %d", "value", 42)
        assert stderr.getvalue() == "[debug] Test value: 42\n"


def test_error_output(logger):
    """Test error output."""
    stderr = StringIO()
    with mock.patch("helm_values_manager.utils.logger.sys.stderr", stderr):
        logger.error("Error message")
        assert stderr.getvalue() == "Error: Error message\n"


def test_error_with_formatting(logger):
    """Test error output with string formatting."""
    stderr = StringIO()
    with mock.patch("helm_values_manager.utils.logger.sys.stderr", stderr):
        logger.error("Error in %s: %s", "function", "details")
        assert stderr.getvalue() == "Error: Error in function: details\n"


def test_multiple_messages(logger):
    """Test multiple messages in sequence."""
    stderr = StringIO()
    with (
        mock.patch.dict(os.environ, {"HELM_DEBUG": "1"}),
        mock.patch("helm_values_manager.utils.logger.sys.stderr", stderr),
    ):
        logger.debug("Debug 1")
        logger.error("Error 1")
        logger.debug("Debug 2")
        expected = "[debug] Debug 1\nError: Error 1\n[debug] Debug 2\n"
        assert stderr.getvalue() == expected
