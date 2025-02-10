"""Value storage backends for helm-values-manager."""

from .base import ValueBackend
from .plain import PlainTextBackend

__all__ = ["ValueBackend", "PlainTextBackend"]
