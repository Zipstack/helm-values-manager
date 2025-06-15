# helm-values-manager: Technical Specification

## Overview

helm-values-manager is a Helm plugin that helps manage Helm value configurations across different deployments (dev, test, prod) with a schema-driven approach. It separates value definitions (schema) from actual values, enabling vendors to distribute schemas while customers manage their deployment-specific values securely.

## Key Features

- **Schema-driven configuration**: Define value metadata (descriptions, paths, requirements) separately from actual values
- **Multi-environment support**: Manage values for different deployments in a single file
- **Secret management**: Support for environment variables (MVP) with pluggable architecture for future providers
- **CD system agnostic**: Generates standard values.yaml files usable with any CD system
- **Type safety**: JSON-based configuration with validation
- **Interactive CLI**: Commands to add/update/remove both schema entries and values

## Architecture

### File Structure

```
project/
├── schema.json                 # Value definitions (from vendor)
├── values-dev.json            # Customer's values for dev environment
├── values-staging.json        # Customer's values for staging
└── values-prod.json           # Customer's values for production
```

### Schema File Format (schema.json)

```json
{
  "version": "1.0",
  "values": [
    {
      "key": "database-host",
      "path": "database.host",
      "description": "PostgreSQL database hostname",
      "type": "string",
      "required": true,
      "default": "localhost"
    },
    {
      "key": "database-password",
      "path": "database.password",
      "description": "PostgreSQL password",
      "type": "string",
      "required": true,
      "sensitive": true
    },
    {
      "key": "replicas",
      "path": "deployment.replicas",
      "type": "number",
      "required": false,
      "default": 3
    },
    {
      "key": "ingress-hosts",
      "path": "ingress.hosts",
      "type": "array",
      "required": false,
      "default": ["example.com"]
    },
    {
      "key": "resources",
      "path": "resources",
      "type": "object",
      "required": false,
      "default": {
        "requests": {"memory": "256Mi", "cpu": "100m"},
        "limits": {"memory": "512Mi", "cpu": "200m"}
      }
    }
  ]
}
```

### Values File Format (values-prod.json)

```json
{
  "dev": {
    "database-host": "dev-db.example.com",
    "database-password": {
      "type": "env",
      "name": "DEV_DB_PASSWORD"
    },
    "replicas": 1
  },
  "staging": {
    "database-host": "staging-db.example.com",
    "database-password": {
      "type": "env",
      "name": "STAGING_DB_PASSWORD"
    },
    "replicas": 2
  },
  "prod": {
    "database-host": "prod-db.example.com",
    "database-password": {
      "type": "env",
      "name": "PROD_DB_PASSWORD"
    },
    "replicas": 3,
    "ingress-hosts": ["app.example.com", "www.example.com"]
  }
}
```

## CLI Commands

### Schema Management

```bash
# Create initial schema.json in current directory
helm values-manager init

# Add new value to schema (interactive)
helm values-manager schema add

# Update existing schema entry
helm values-manager schema update <key>

# Remove entry from schema
helm values-manager schema remove <key>

# List all schema entries
helm values-manager schema list

# Show details of specific schema entry
helm values-manager schema get <key>
```

### Values Management

```bash
# Set or update a value
helm values-manager values set <key> <value> --env <env>

# Configure environment variable secret (interactive)
helm values-manager values set-secret <key> --env <env>

# Get specific value
helm values-manager values get <key> --env <env>

# List all values for an environment
helm values-manager values list --env <env>

# Remove a value
helm values-manager values remove <key> --env <env>
```

### Core Operations

```bash
# Validate schema and all values files
helm values-manager validate

# Generate values.yaml (includes validation)
helm values-manager generate --env <env>

# Show schema changes between versions (future feature)
helm values-manager diff
```

### Global Options

```bash
--schema <path>    # Path to schema.json (default: ./schema.json)
--values <path>    # Path to values file (default: ./values-<env>.json)
```

## Command Behaviors

### `init` Command
- Creates a minimal schema.json with example structure
- Checks if schema.json already exists and prompts for overwrite

### `schema add` Command
Interactive prompts for:
- Key name
- Helm value path
- Description
- Type (string/number/boolean/array/object)
- Required (yes/no)
- Default value (if not required)
- Is sensitive (yes/no)

### `values set-secret` Command
Interactive prompts for:
- Secret type (env only for MVP)
- Environment variable name

### `generate` Command
1. Validates schema.json structure
2. Validates values file for the specified environment
3. Checks all required values are present
4. Verifies environment variables exist for secrets
5. Resolves all values including secrets
6. Generates values.yaml file

### `validate` Command
Reports all errors at once:
- Missing required values
- Type mismatches
- Invalid schema structure
- Missing environment variables for secrets

## Workflow Example

### Vendor Workflow
```bash
# Create schema for chart
helm values-manager init
helm values-manager schema add  # Add each value definition

# Distribute schema.json alongside helm chart
```

### Customer Workflow
```bash
# Initial setup
helm values-manager values set database-host "prod-db.com" --env prod
helm values-manager values set-secret database-password --env prod

# Generate values for deployment
export PROD_DB_PASSWORD="actual-password"
helm values-manager generate --env prod > values-prod.yaml

# Deploy with any CD system
helm upgrade myapp ./chart -f values-prod.yaml
```

## Implementation Details

### Technology Stack
- **Language**: Python 3.9+
- **CLI Framework**: Typer
- **JSON Parsing**: Built-in json module
- **Validation**: JSON Schema validation

### Plugin Structure
```
helm-values-manager/
├── plugin.yaml
├── install.sh
├── requirements.txt
├── main.py
└── src/
    ├── __init__.py
    ├── schema.py
    ├── values.py
    ├── generator.py
    └── validator.py
```

### plugin.yaml
```yaml
name: "values-manager"
version: "0.1.0"
usage: "Manage Helm values across environments"
description: "Schema-driven Helm values management for multi-environment deployments"
command: "$HELM_PLUGIN_DIR/venv/bin/python $HELM_PLUGIN_DIR/main.py"
```

### install.sh
```bash
#!/bin/bash
cd "$HELM_PLUGIN_DIR"
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## Security Considerations

1. **Secret Handling**:
   - Never store actual secrets in values files
   - Resolve secrets only at generation time
   - Generated values.yaml should be treated as sensitive

2. **File Permissions**:
   - Ensure proper permissions on generated values.yaml
   - Consider using stdout instead of file output in CI/CD

3. **Validation**:
   - Fail fast if any required secrets are missing
   - Validate all inputs before generation

## Future Enhancements

1. **Additional Secret Providers**:
   - Kubernetes Secrets
   - HashiCorp Vault
   - AWS Secrets Manager
   - Azure Key Vault

2. **Schema Versioning**:
   - Semantic versioning
   - Migration guides
   - Breaking change detection

3. **Advanced Features**:
   - Schema inheritance
   - Value templates/interpolation
   - Conditional values based on environment
   - Integration with Helm hooks

## Error Handling

All errors should be descriptive and actionable:

```
Error: Validation failed:
- Missing required value: database-host (env: prod)
- Type mismatch: replicas should be number, got string (env: dev)
- Environment variable not found: PROD_DB_PASSWORD
```

## Testing Strategy

1. Unit tests for each component
2. Integration tests for CLI commands
3. End-to-end tests with actual Helm charts
4. Cross-platform testing (Linux, macOS, Windows)

## Documentation Requirements

1. README with quick start guide
2. Detailed command documentation
3. Schema specification reference
4. Migration guide for chart updates
5. Security best practices guide
