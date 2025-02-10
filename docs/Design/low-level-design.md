# Low Level Design - Helm Values Manager

## Core Components

### Domain Model

The core domain model is represented by `HelmValuesConfig`, which is the central data structure for managing configuration values.

```mermaid
classDiagram
    class HelmValuesConfig {
        +List~Deployment~ deployments
        +List~ConfigValue~ config
        +from_dict(data: dict) HelmValuesConfig
        +to_dict() dict
        +validate() None
        +get_value(path: str, environment: str) str
        +set_value(path: str, environment: str, value: str) None
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
    }

    HelmValuesConfig "1" *-- "*" ConfigValue
    HelmValuesConfig "1" *-- "*" Deployment
```

### Value Storage

The value storage system follows a clean separation between the domain model and storage backends:

```mermaid
classDiagram
    class ValueBackend {
        <<interface>>
        +get_value(path: str, environment: str)* str
        +set_value(path: str, environment: str, value: str)* None
        +validate_auth_config(auth_config: dict)* None
    }

    class PlainTextBackend {
        -Path values_file
        +get_value(path: str, environment: str) str
        +set_value(path: str, environment: str, value: str) None
        +validate_auth_config(auth_config: dict) None
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

    ValueBackend <|.. PlainTextBackend
    ValueBackend <|.. AWSSecretsBackend
    ValueBackend <|.. AzureKeyVaultBackend
```

### Configuration Flow

The configuration flow shows how data moves through the system:

```mermaid
sequenceDiagram
    participant CLI
    participant HelmValuesConfig
    participant ValueBackend
    participant Storage
    participant Schema

    Note over CLI,Schema: Configuration Loading
    CLI->>HelmValuesConfig: load_config(config_file)
    activate HelmValuesConfig
    HelmValuesConfig->>Schema: validate_schema(config_data)
    Schema-->>HelmValuesConfig: validation result

    Note over CLI,Schema: Value Operations
    CLI->>HelmValuesConfig: get_value(path, env)
    HelmValuesConfig->>HelmValuesConfig: validate_path(path)
    HelmValuesConfig->>HelmValuesConfig: get_deployment(env)
    HelmValuesConfig->>ValueBackend: create_backend(deployment)
    activate ValueBackend
    ValueBackend->>ValueBackend: validate_auth_config()
    ValueBackend->>Storage: read_value(path, env)
    Storage-->>ValueBackend: value
    ValueBackend-->>HelmValuesConfig: value
    deactivate ValueBackend
    HelmValuesConfig-->>CLI: value

    Note over CLI,Schema: Configuration Updates
    CLI->>HelmValuesConfig: set_value(path, env, value)
    HelmValuesConfig->>HelmValuesConfig: validate_value(value)
    HelmValuesConfig->>ValueBackend: create_backend(deployment)
    activate ValueBackend
    ValueBackend->>Storage: write_value(path, env, value)
    Storage-->>ValueBackend: success
    ValueBackend-->>HelmValuesConfig: success
    deactivate ValueBackend
    HelmValuesConfig->>HelmValuesConfig: update_config_file()
    HelmValuesConfig-->>CLI: success

    deactivate HelmValuesConfig
```

This flow diagram shows:
1. **Configuration Loading**
   - Loading from JSON file
   - Schema validation
   - Deployment configuration

2. **Value Operations**
   - Path validation
   - Deployment resolution
   - Backend creation and auth
   - Storage interaction

3. **Configuration Updates**
   - Value validation
   - Storage updates
   - Configuration persistence

## Implementation Details

### HelmValuesConfig as Central Model

1. `HelmValuesConfig` acts as the central model and coordinator:
   - Manages configuration validation
   - Handles backend creation and lifecycle
   - Provides a unified interface for value operations

2. Value operations flow:
   ```python
   class HelmValuesConfig:
       def get_value(self, path: str, environment: str) -> str:
           # Find the deployment for this path/environment
           deployment = self._get_deployment(environment)

           # Create and validate the backend
           backend = self._create_backend(deployment)

           # Get the value through the backend
           return backend.get_value(path, environment)
   ```

### Backend Implementation

1. Each backend implements the `ValueBackend` interface:
   ```python
   class ValueBackend(ABC):
       @abstractmethod
       def get_value(self, path: str, environment: str) -> str:
           pass

       @abstractmethod
       def set_value(self, path: str, environment: str, value: str) -> None:
           pass

       @abstractmethod
       def validate_auth_config(self, auth_config: dict) -> None:
           pass
   ```

2. Backends handle storage-specific operations:
   - Authentication
   - Value serialization/deserialization
   - Storage-specific error handling

### Authentication Flow

1. Authentication is handled per deployment:
   ```python
   class HelmValuesConfig:
       def _create_backend(self, deployment: Deployment) -> ValueBackend:
           # Create the appropriate backend
           backend = self._backend_factory.create(deployment.backend)

           # Validate auth config
           backend.validate_auth_config(deployment.auth)

           return backend
   ```

2. Each backend defines its auth requirements:
   ```python
   class AWSSecretsBackend(ValueBackend):
       def validate_auth_config(self, auth_config: dict) -> None:
           if auth_config["type"] == "direct":
               required = ["access_key_id", "secret_access_key"]
               self._validate_required_fields(auth_config, required)
   ```

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

1. Implement the backend factory pattern
2. Add more comprehensive validation in `HelmValuesConfig`
3. Implement caching strategy for backend instances
4. Add observability (logging, metrics)
5. Implement value encryption for sensitive data
