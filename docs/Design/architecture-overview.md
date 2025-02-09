# Helm Values Manager - Design Document

## Background
Helm Values Manager simplifies **configuration and secret management** across multiple Kubernetes deployments. It ensures **secure storage**, **validation**, and **automation** in Helm-based workflows.

## Architecture Overview

The Helm plugin consists of:
- **CLI Command Interface (Python Typer-based)**: Handles command execution.
- **Validation Engine**: Ensures required keys have values for each deployment.
- **Secret Manager Integration**: Supports AWS Secrets Manager, Azure Key Vault, HashiCorp Vault, and Git-Secrets.
- **values.yaml Generator**: Produces the final Helm-compatible values file.
- **Helm Plugin System**: Integrates seamlessly with Helm commands.

## Configuration YAML Structure

```yaml
release: my-release

deployments:
  dev:
    secrets_backend: aws_secrets_manager
  prod:
    secrets_backend: azure_key_vault

config:
  - key: DATABASE_URL
    path: global.database.url
    required: true
    sensitive: true
    values:
      dev: "mydb://dev-connection"
      prod: "mydb://prod-connection"
  - key: LOG_LEVEL
    path: global.logging.level
    required: false
    sensitive: false
    values:
      dev: "debug"
      prod: "warn"
```

## Secret Manager Extensibility
Implemented using **Abstract Base Class (ABC)**:

```python
from abc import ABC, abstractmethod

class SecretManager(ABC):
    @abstractmethod
    def get_secret(self, secret_name: str) -> str:
        pass

    @abstractmethod
    def store_secret(self, secret_name: str, secret_value: str):
        pass
```

## CLI Workflow

### Example Commands
```sh
helm values-manager init my-release
helm values-manager add-key DATABASE_URL --required --sensitive --path=global.database.url
helm values-manager add-secret DATABASE_URL=mydb://connection --deployment=dev
helm values-manager validate
helm values-manager generate --deployment=dev
```

## Testing Strategy
- **Unit Tests:** CLI commands, validation logic, storage handling.
- **Integration Tests:** Secret manager interactions.
- **E2E Tests:** Full workflow validation.

## Conclusion
Helm Values Manager is a **secure, scalable, and extensible solution** for Helm-based deployments.
