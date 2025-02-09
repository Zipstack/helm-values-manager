# ADR-001: Decision to Implement Helm Values Manager as a Helm Plugin

## Status
Accepted

## Context
Managing configurations and secrets across multiple Kubernetes deployments is a complex task. Helm provides a standardized way to manage Kubernetes applications, but it lacks a structured approach for managing per-environment configurations and securely storing secrets.

Key challenges include:
- Ensuring configurations remain consistent across different environments (e.g., dev, staging, production).
- Managing sensitive values securely using external secret management systems.
- Automating the generation of `values.yaml` while integrating with GitOps tools like ArgoCD.
- Providing a user-friendly CLI that integrates well with Helm workflows.

## Decision
We have decided to implement the **Helm Values Manager** as a **Helm plugin written in Python**.

### Justification:
1. **Seamless Helm Integration:** A Helm plugin ensures configurations are managed within the Helm ecosystem without requiring additional tools.
2. **Python for Implementation:** Libraries like `Typer` enable robust CLI development with autocomplete capabilities.
3. **Global and Deployment-Specific Configuration Management:** Ensuring consistency across deployments.
4. **Secret Storage Abstraction:** Securely manages sensitive values by integrating with AWS Secrets Manager, Azure Key Vault, and HashiCorp Vault.
5. **CLI-Based Approach:** Interactive commands for managing configurations and secrets.
6. **Autocomplete Support:** Smooth CLI experience.
7. **ArgoCD Compatibility:** Generates `values.yaml` dynamically for GitOps workflows.

## YAML Structure

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

## Consequences
- The project will be built as a Helm plugin with Python as the core language.
- Secret backends must be configured separately for security compliance.
- Future extensions can include a UI for easier configuration management.

## Decision Outcome
✅ **Accepted** - Implementation will proceed as a Helm plugin using Python, with structured configuration management, secret integration, and ArgoCD compatibility.
