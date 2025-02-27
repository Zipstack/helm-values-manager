# Backends and Authentication Types

This document provides a comprehensive overview of the supported backends, authentication types, and backend configurations in the Helm Values Manager.

## Supported Backends

The Helm Values Manager supports the following backend types for storing values:

| Backend Type | Description | Use Case | Status |
|--------------|-------------|----------|--------|
| `git-secret` | Uses git-secret for encrypting sensitive values | Local development, small teams | Planned |
| `aws` | Uses AWS Secrets Manager for storing sensitive values | AWS-based deployments | Planned |
| `azure` | Uses Azure Key Vault for storing sensitive values | Azure-based deployments | Planned |
| `gcp` | Uses Google Secret Manager for storing sensitive values | GCP-based deployments | Planned |

### Backend Selection Criteria

When selecting a backend, consider:

1. **Security Requirements**: Different backends offer varying levels of security, audit capabilities, and compliance features.
2. **Cloud Provider**: Select the backend that aligns with your cloud infrastructure.
3. **Team Size**: For small teams, simpler backends like `git-secret` may be sufficient.
4. **Operational Complexity**: Some backends require more setup and maintenance than others.

## Authentication Types

Each backend supports multiple authentication methods:

| Auth Type | Description | Required Parameters | Supported Backends |
|-----------|-------------|---------------------|-------------------|
| `direct` | Direct credential input | `credentials` object | All |
| `env` | Environment variable-based authentication | `env_prefix` | All |
| `file` | File-based authentication | `path` to auth file | All |
| `managed_identity` | Cloud provider managed identity | None | `aws`, `azure`, `gcp` |

### Authentication Type Details

#### Direct Authentication (`direct`)

Credentials are provided directly in the configuration file. This is suitable for testing but not recommended for production use.

**Required Parameters:**
- `credentials`: An object containing backend-specific credentials

**Example:**
```json
"auth": {
  "type": "direct",
  "credentials": {
    "token": "your-token-here"
  }
}
```

#### Environment Variable Authentication (`env`)

Credentials are read from environment variables. This is suitable for CI/CD pipelines and containerized deployments.

**Required Parameters:**
- `env_prefix`: Prefix for environment variables

**Example:**
```json
"auth": {
  "type": "env",
  "env_prefix": "AWS_"
}
```

#### File Authentication (`file`)

Credentials are read from a file. This is suitable for local development and when credentials are managed by external systems.

**Required Parameters:**
- `path`: Path to the authentication file

**Example:**
```json
"auth": {
  "type": "file",
  "path": "~/.aws/credentials"
}
```

#### Managed Identity Authentication (`managed_identity`)

Uses cloud provider's managed identity service. This is the recommended approach for production deployments in cloud environments.

**Required Parameters:**
- None

**Example:**
```json
"auth": {
  "type": "managed_identity"
}
```

## Backend Configurations

Each backend may require additional configuration parameters:

### Git Secret Backend (`git-secret`)

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| None | No additional configuration required | - | - |

### AWS Secrets Manager Backend (`aws`)

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `region` | AWS region | Yes | - |
| `prefix` | Prefix for secret names | No | Empty string |
| `endpoint` | Custom endpoint URL | No | AWS default endpoint |

**Example:**
```json
"backend_config": {
  "region": "us-west-2",
  "prefix": "myapp/"
}
```

### Azure Key Vault Backend (`azure`)

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `vault_url` | Key Vault URL | Yes | - |
| `prefix` | Prefix for secret names | No | Empty string |

**Example:**
```json
"backend_config": {
  "vault_url": "https://myvault.vault.azure.net/",
  "prefix": "myapp-"
}
```

### Google Secret Manager Backend (`gcp`)

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `project_id` | GCP Project ID | Yes | - |
| `prefix` | Prefix for secret names | No | Empty string |

**Example:**
```json
"backend_config": {
  "project_id": "my-gcp-project",
  "prefix": "myapp_"
}
```

## Implementation Status

For the MVP release, the following components are implemented:

1. **Command Interface**:
   - `add-deployment`: Command interface implemented
   - Backend validation: Interface defined, implementation pending

2. **Backends**:
   - All backends: Interface defined, implementation pending

3. **Authentication Types**:
   - All auth types: Interface defined, implementation pending

4. **Backend Configurations**:
   - Basic validation implemented
   - Backend-specific validation defined in the command interface

## Future Enhancements

1. **Additional Backends**:
   - HashiCorp Vault
   - Kubernetes Secrets
   - Custom backends via plugins

2. **Enhanced Authentication**:
   - OIDC support
   - Role-based access for cloud providers
   - Multi-factor authentication integration

3. **Configuration Extensions**:
   - Rotation policies
   - Versioning support
   - Audit logging
