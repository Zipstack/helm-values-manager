# Helm Values Manager - Design Document

## Background
Helm Values Manager simplifies **configuration and secret management** across multiple Kubernetes deployments. It ensures **secure storage**, **validation**, and **automation** in Helm-based workflows.

## Architecture Overview

The Helm plugin consists of:
- **CLI Command Interface (Python Typer-based)**: Handles command execution.
- **Validation Engine**: Ensures required values have values for each deployment.
- **Configuration Manager**: Manages path/environment organization and key generation.
- **Value Storage Backend**: Provides key-value storage through AWS Secrets Manager, Azure Key Vault, HashiCorp Vault, and Git-Secrets.
- **values.yaml Generator**: Produces the final Helm-compatible values file.
- **Helm Plugin System**: Integrates seamlessly with Helm commands.
- **JSON Schema Validation**: Ensures configuration files follow the correct structure.

## Configuration Structure

```json
{
  "release": "my-release",
  "deployments": {
    "dev": {
      "secrets_backend": "aws_secrets_manager"
    },
    "prod": {
      "secrets_backend": "azure_key_vault"
    }
  },
  "config": [
    {
      "path": "global.database.url",
      "required": true,
      "sensitive": true,
      "values": {
        "dev": "mydb://dev-connection",
        "prod": "mydb://prod-connection"
      }
    },
    {
      "path": "global.logging.level",
      "required": false,
      "sensitive": false,
      "values": {
        "dev": "DEBUG",
        "prod": "WARN"
      }
    }
  ]
}
```

## Value Backend Extensibility
Implemented using **Abstract Base Class (ABC)**:

```python
from abc import ABC, abstractmethod

class ValueBackend(ABC):
    @abstractmethod
    def get_value(self, key: str) -> str:
        """Get a value from the secrets backend."""
        pass

    @abstractmethod
    def set_value(self, key: str, value: str) -> None:
        """Set a value in the secrets backend."""
        pass
```

## CLI Workflow

### Example Commands
```sh
helm values-manager init my-release
helm values-manager add-value --path=global.database.url --required --sensitive
helm values-manager set-value global.database.url=mydb://connection --deployment=dev
helm values-manager validate
helm values-manager generate --deployment=dev
```

## Testing Strategy
- **Unit Tests:** CLI commands, validation logic, storage handling.
- **Integration Tests:** Backend interactions and value management.
- **E2E Tests:** Full workflow validation.

## Implementation Details

### JSON Schema Validation
- Uses Python's `jsonschema` library for configuration validation
- Schema version control for backward compatibility
- Strict validation of required fields and value types

### Value Storage
- Values stored in JSON format for consistency
- Supports both plain text and encrypted storage
- Environment-specific value management

### Security Considerations
- Sensitive values stored in secure backends
- Support for various authentication methods
- No sensitive data in version control

## Conclusion
Helm Values Manager is a **secure, scalable, and extensible solution** for Helm-based deployments, using JSON for consistent configuration management and robust schema validation.
