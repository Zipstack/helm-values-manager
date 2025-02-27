# Low Level Design - Helm Values Manager

## Core Components

### 1. Domain Model

The core domain model consists of several key classes that manage configuration values and their storage:

```mermaid
classDiagram
    class HelmValuesConfig {
        +List~Deployment~ deployments
        +List~ConfigValue~ config
        -Dict~str,PathData~ _path_map
        +from_dict(data: dict) HelmValuesConfig
        +to_dict() dict
        +validate() None
        +get_value(path: str, environment: str) str
        +set_value(path: str, environment: str, value: str) None
        +add_config_path(path: str, description: str, required: bool, sensitive: bool) None
    }

    class PathData {
        +str path
        +Dict metadata
        -Dict~str,Value~ _values
        +validate() None
        +set_value(environment: str, value: Value) None
        +get_value(environment: str) Optional[Value]
        +get_environments() Iterator[str]
        +to_dict() Dict
        +from_dict(data: Dict, create_value_fn) PathData
    }

    class Value {
        +str path
        +str environment
        -ValueBackend _backend
        +get() str
        +set(value: str) None
        +to_dict() dict
        +from_dict(data: dict, backend: ValueBackend) Value
    }

    class ConfigValue {
        +str path
        +Optional~str~ description
        +bool required
        +bool sensitive
        +Dict~str,str~ values
    }

    class Deployment {
        +str name
        +Dict~str,Any~ auth
        +str backend
        +Dict~str,Any~ backend_config
    }

    class BaseCommand {
        <<abstract>>
        +execute() Any
        +load_config() HelmValuesConfig
        +save_config(config: HelmValuesConfig) None
        #run(config: HelmValuesConfig)* Any
    }

    class ValueBackend {
        <<interface>>
        +get_value(path: str, environment: str)* str
        +set_value(path: str, environment: str, value: str)* None
        +validate_auth_config(auth_config: dict)* None
    }

    class SimpleValueBackend {
        -Dict~str,str~ values
        +get_value(path: str, environment: str) str
        +set_value(path: str, environment: str, value: str) None
    }

    class AWSSecretsBackend {
        -SecretsManagerClient client
        +get_value(path: str, environment: str) str
        +set_value(path: str, environment: str, value: str) None
        +validate_auth_config(auth_config: dict) None
    }

    class AzureKeyVaultBackend {
        -KeyVaultClient client
        +get_value(path: str, environment: str) str
        +set_value(path: str, environment: str, value: str) None
        +validate_auth_config(auth_config: dict) None
    }

    class HelmLogger {
        +debug(msg: str, *args: Any) None
        +error(msg: str, *args: Any) None
    }

    HelmValuesConfig "1" *-- "*" ConfigValue
    HelmValuesConfig "1" *-- "*" Deployment
    HelmValuesConfig "1" *-- "*" PathData
    PathData "1" *-- "*" Value
    Value "1" o-- "1" ValueBackend
    ValueBackend <|.. SimpleValueBackend
    ValueBackend <|.. AWSSecretsBackend
    ValueBackend <|.. AzureKeyVaultBackend
    BaseCommand <|-- SetValueCommand
    BaseCommand <|-- GetValueCommand
```

### 2. Value Management

The system manages configuration values through a hierarchy of classes:

1. **HelmValuesConfig**
   - Top-level configuration manager
   - Maintains mapping of paths to PathData instances
   - Handles backend selection based on value sensitivity
   - Manages deployments and their configurations

2. **PathData**
   - Represents a single configuration path and its properties
   - Owns the configuration path and ensures consistency
   - Stores metadata (description, required status, sensitivity)
   - Manages environment-specific values through Value instances
   - Validates path consistency between itself and its Values
   - Delegates actual value storage to Value instances

3. **Value**
   - Handles actual value storage and retrieval
   - Uses appropriate backend for storage operations
   - Maintains reference to its path and environment

This hierarchy ensures:
- Clear separation of concerns
- Consistent path handling across the system
- Proper validation at each level
- Flexible backend selection based on value sensitivity

### 3. Command Pattern

All CLI commands inherit from `BaseCommand` to ensure consistent behavior:

```python
class BaseCommand:
    def execute(self) -> Any:
        try:
            config = self.load_config()
            result = self.run(config)
            self.save_config(config)
            return result
        except Exception as e:
            # Handle errors, cleanup if needed
            raise

    def load_config(self) -> HelmValuesConfig:
        # Implement file loading with locking
        pass

    def save_config(self, config: HelmValuesConfig) -> None:
        # Implement file saving with backup
        pass

    @abstractmethod
    def run(self, config: HelmValuesConfig) -> Any:
        # Subclasses implement command-specific logic
        pass
```

Benefits:
- Consistent file operations
- Built-in error handling
- Automatic file locking
- Configuration backup support

#### Command Structure for Deployments and Backends

The command structure for managing deployments and backends follows a nested subcommand pattern (see [ADR-011](../ADRs/011-command-structure-for-deployments.md)):

```
helm values add-deployment [name]

helm values add-backend [backend] --deployment=[name] [backend_options]
  - helm values add-backend aws --deployment=prod --region=us-west-2
  - helm values add-backend azure --deployment=prod --vault-url=https://myvault.vault.azure.net
  - helm values add-backend gcp --deployment=prod --project-id=my-project
  - helm values add-backend git-secret --deployment=prod

helm values add-auth [auth_type] --deployment=[name] [auth_options]
  - helm values add-auth direct --deployment=prod --credentials='{...}'
  - helm values add-auth env --deployment=prod --env-prefix=AWS_
  - helm values add-auth file --deployment=prod --auth-path=~/.aws/credentials
  - helm values add-auth managed-identity --deployment=prod
```

This structure:
- Separates the concerns of creating a deployment, configuring a backend, and setting up authentication
- Uses subcommands to provide context-specific options and help text
- Follows a natural workflow of first creating a deployment, then adding backend and auth configuration

### 4. Storage Backends

The `ValueBackend` interface defines the contract for value storage:

```python
class ValueBackend(ABC):
    @abstractmethod
    def get_value(self, path: str, environment: str) -> str:
        """Get a value from storage."""
        pass

    @abstractmethod
    def set_value(self, path: str, environment: str, value: str) -> None:
        """Store a value."""
        pass

    @abstractmethod
    def validate_auth_config(self, auth_config: dict) -> None:
        """Validate backend-specific authentication configuration."""
        pass
```

Implementations:
- SimpleValueBackend (for non-sensitive values)
- AWS Secrets Manager Backend
- Azure Key Vault Backend
- Additional backends can be easily added

For a comprehensive overview of supported backends, authentication types, and backend configurations, see [Backends and Authentication Types](backends-and-auth.md).

### 5. Schema Validation

The configuration system uses JSON Schema validation to ensure data integrity and consistency:

```mermaid
classDiagram
    class SchemaValidator {
        +validate_config(data: dict) None
        -load_schema() dict
        -handle_validation_error(error: ValidationError) str
    }

    class HelmValuesConfig {
        +from_dict(data: dict) HelmValuesConfig
        +to_dict() dict
        +validate() None
    }

    HelmValuesConfig ..> SchemaValidator : uses
```

#### Schema Structure

The schema (`schemas/v1.json`) defines:
1. **Version Control**
   - Schema version validation
   - Backward compatibility checks

2. **Deployment Configuration**
   - Backend type validation (git-secret, aws, azure, gcp)
   - Authentication method validation
   - Backend-specific configuration validation

3. **Value Configuration**
   - Path format validation (dot notation)
   - Required/optional field validation
   - Sensitive value handling
   - Environment-specific value validation

#### Validation Points

Schema validation occurs at critical points:
1. **Configuration Loading** (`from_dict`)
   - Validates complete configuration structure
   - Ensures all required fields are present
   - Validates data types and formats

2. **Pre-save Validation** (`to_dict`)
   - Ensures configuration remains valid after modifications
   - Validates new values match schema requirements

3. **Path Addition** (`add_config_path`)
   - Validates new path format
   - Ensures path uniqueness
   - Validates metadata structure

#### Error Handling

The validation system provides:
1. **Detailed Error Messages**
   - Exact location of validation failures
   - Clear explanation of validation rules
   - Suggestions for fixing issues

2. **Validation Categories**
   - Schema version mismatches
   - Missing required fields
   - Invalid value formats
   - Backend configuration errors
   - Authentication configuration errors

3. **Error Recovery**
   - Validation before persistence
   - Prevents invalid configurations from being saved
   - Maintains system consistency

This validation ensures:
- Configuration integrity
- Consistent data structure
- Clear error reporting
- Safe configuration updates

## Implementation Details

### 1. Configuration Structure

The configuration follows the v1 schema:
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

### 2. Value Resolution Process

1. Path Lookup:
   - O(1) lookup in `_path_map`
   - Validates path existence
   - Retrieves value metadata

2. Value Resolution:
   - Uses `Value` class to handle resolution
   - Automatically selects storage backend
   - Handles errors and validation

### 3. Security Features

1. Value Protection:
   - Sensitive value marking
   - Secure storage in remote backends
   - Authentication validation

2. File Safety:
   - Automatic file locking
   - Backup before writes
   - Atomic updates

## Logging System

The logging system follows Helm plugin conventions and provides consistent output formatting:

1. **HelmLogger Class**
   - Provides debug and error logging methods
   - Follows Helm output conventions
   - Uses stderr for all output
   - Controls debug output via HELM_DEBUG environment variable

2. **Global Logger Instance**
   - Available via `from helm_values_manager.utils.logger import logger`
   - Ensures consistent logging across all components
   - Simplifies testing with mock support

3. **Performance Features**
   - Uses string formatting for efficiency
   - Lazy evaluation of debug messages
   - Minimal memory overhead

4. **Testing Support**
   - Mockable stderr output
   - Environment variable control
   - String format verification

## Benefits of This Design

1. **Separation of Concerns**
   - Domain logic in `HelmValuesConfig`
   - Storage logic in backends
   - Clean interface boundaries

2. **Extensibility**
   - Easy to add new backends
   - Auth handling per backend
   - Consistent validation

3. **Maintainability**
   - Central configuration management
   - Clear data flow
   - Type safety through domain model

4. **Testing**
   - Easy to mock backends
   - Clear component boundaries
   - Isolated validation testing

## Next Steps

1. Implement the Value class
2. Add comprehensive validation
3. Implement caching strategy
4. Add value encryption support
5. Enhance error handling
