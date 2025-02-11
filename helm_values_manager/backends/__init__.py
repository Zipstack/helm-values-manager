"""Value storage backends for helm-values-manager.

This module provides the base interface and implementations for value storage backends.
Each backend is responsible for securely storing and retrieving values using
different storage systems like AWS Secrets Manager or Azure Key Vault.
"""

from .base import ValueBackend

__all__ = ["ValueBackend"]
