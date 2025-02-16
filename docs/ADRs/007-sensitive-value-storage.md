# ADR 0002: Sensitive Value Storage

## Status
Proposed

## Context
The helm-values-manager needs to handle both sensitive and non-sensitive configuration values. While non-sensitive values can be stored directly in the configuration files, sensitive values require special handling to ensure security.

## Decision
We will store sensitive values using the existing configuration structure, with sensitive values using a special reference format.
The existing schema already supports this through its `sensitive` flag and flexible string values.

1. When a value is marked as sensitive (`sensitive: true`):
   - The actual value will be stored in a secure backend (AWS Secrets Manager, Azure Key Vault, etc.)
   - Only a reference to the secret will be stored in our configuration files
   - The reference will use a URI-like format: `secret://<backend-type>/<secret-path>`

2. Example configuration showing both sensitive and non-sensitive values:
```json
{
    "version": "1.0",
    "release": "my-app",
    "deployments": {
        "prod": {
            "backend": "gcp",
            "auth": {
                "type": "managed_identity"
            },
            "backend_config": {
                "region": "us-central1"
            }
        }
    },
    "config": [
        {
            "path": "app.replicas",
            "description": "Number of application replicas",
            "required": true,
            "sensitive": false,
            "values": {
                "dev": "3",
                "prod": "5"
            }
        },
        {
            "path": "app.database.password",
            "description": "Database password",
            "required": true,
            "sensitive": true,
            "values": {
                "dev": "secret://gcp-secrets/my-app/dev/db-password",
                "prod": "secret://gcp-secrets/my-app/prod/db-password"
            }
        }
    ]
}
```

This approach:
1. Leverages the existing schema without modifications:
   - Uses the `sensitive` flag to identify sensitive values
   - Uses the flexible string type in `values` to store references
   - Maintains backward compatibility
2. Provides a clear and consistent format for secret references
3. Supports versioning through the secret path (e.g., `secret://gcp-secrets/my-app/prod/db-password/v1`)

The validation and resolution of secret references will be handled by:
1. The backend implementation (parsing and resolving references)
2. The `Value` class (determining whether to treat a value as a reference based on the `sensitive` flag)

## Implementation Notes
1. Secret references will be parsed and validated by the backend implementation
2. The `Value` class will check the `sensitive` flag to determine how to handle the value:
   - If `sensitive: false`, use the value as-is
   - If `sensitive: true`, parse the value as a secret reference and resolve it
3. Each secure backend will implement its own reference resolution logic
4. Future enhancement: Add commands to manage secrets directly through the tool

## Consequences

### Positive
- Security: Sensitive values never leave the secure backend
- Traceability: Easy to track which secrets are used where
- Versioning: Support for secret rotation via version references
- Flexibility: Different backends can implement their own reference formats
- Auditability: References are human-readable for easier debugging

### Negative
- Additional Setup: Users need to create secrets separately (until we add direct creation support)
- Complexity: Need to manage both direct values and secret references
- Dependencies: Requires access to secure backends

## Related
- ADR 0001 (if it exists, about general value storage)
- Future ADR about secret management commands
