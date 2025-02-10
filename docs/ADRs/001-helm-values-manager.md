# ADR-001: Decision to Implement Helm Values Manager as a Helm Plugin

## Status
Accepted

## Context
Managing configurations and secrets across multiple Kubernetes deployments is a complex task. Helm provides a standardized way to manage Kubernetes applications, but it lacks a structured approach for managing per-environment configurations and securely storing secrets.

Key challenges include:
- Ensuring configurations remain consistent across different environments (e.g., dev, staging, production).
- Managing sensitive values securely using external secret management systems.
- Automating the generation of `values.json` while integrating with GitOps tools like ArgoCD.
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
7. **ArgoCD Compatibility:** Generates `values.json` dynamically for GitOps workflows.
8. **JSON for Configuration:** Using JSON for configuration files provides better schema validation and consistent parsing across different platforms.

## Configuration Structure

The configuration follows this structure:

```json
{
  "version": "1.0",
  "release": "my-release",
  "deployments": {
    "dev": {
      "secrets_backend": "aws_secrets_manager",
      "secrets_config": {
        "region": "us-west-2",
        "secret_prefix": "/dev/myapp/",
        "auth": {
          "type": "env"
        }
      }
    },
    "staging": {
      "secrets_backend": "google_secret_manager",
      "secrets_config": {
        "project_id": "my-gcp-project",
        "secret_prefix": "myapp-staging-",
        "auth": {
          "type": "file",
          "path": "/path/to/gcp-service-account.json"
        }
      }
    },
    "prod": {
      "secrets_backend": "azure_key_vault",
      "secrets_config": {
        "vault_url": "https://my-prod-vault.vault.azure.net",
        "auth": {
          "type": "managed_identity"
        }
      }
    },
    "local": {
      "secrets_backend": "git_secret",
      "secrets_config": {
        "gpg_key": "${GPG_KEY}",
        "secret_files_path": "./.gitsecret",
        "auth": {
          "type": "file",
          "path": "~/.gnupg/secring.gpg"
        }
      }
    }
  },
  "config": [
    {
      "path": "global.database.url",
      "description": "Database connection string for the application",
      "required": true,
      "sensitive": true,
      "values": {
        "dev": "mydb://dev-connection",
        "staging": "mydb://staging-connection",
        "prod": "mydb://prod-connection",
        "local": "mydb://localhost"
      }
    },
    {
      "path": "global.logging.level",
      "description": "Application logging verbosity level",
      "required": false,
      "sensitive": false,
      "values": {
        "dev": "DEBUG",
        "staging": "INFO",
        "prod": "WARN",
        "local": "DEBUG"
      }
    }
  ]
}
```

Alternative authentication configurations:
- AWS:
  ```json
  {
    "type": "file",
    "path": "~/.aws/credentials"
  }
  ```
  or
  ```json
  {
    "type": "direct",
    "access_key_id": "AKIA...",
    "secret_access_key": "xyz..."
  }
  ```

- Google Cloud:
  ```json
  {
    "type": "env",
    "credential_env": "GOOGLE_APPLICATION_CREDENTIALS"
  }
  ```
  or
  ```json
  {
    "type": "direct",
    "credentials_json": "{...}"
  }
  ```

- Azure:
  ```json
  {
    "type": "service_principal",
    "tenant_id": "${AZURE_TENANT_ID}",
    "client_id": "${AZURE_CLIENT_ID}",
    "client_secret": "${AZURE_CLIENT_SECRET}"
  }
  ```

- Git Secret:
  ```json
  {
    "type": "env",
    "passphrase_env": "GIT_SECRET_PASSPHRASE"
  }
  ```
  or
  ```json
  {
    "type": "direct",
    "passphrase": "your-passphrase"
  }
  ```

## Consequences
- The project will be built as a Helm plugin with Python as the core language.
- Secret backends must be configured separately for security compliance.
- Future extensions can include a UI for easier configuration management.

## Decision Outcome
✅ **Accepted** - Implementation will proceed as a Helm plugin using Python, with structured configuration management, secret integration, and ArgoCD compatibility.
