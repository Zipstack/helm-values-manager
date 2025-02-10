# Helm Values Manager - CLI Command Sequence Diagrams

## 1. Init Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant HelmValuesConfig
    participant FileSystem

    User->>CLI: helm values init
    activate CLI

    CLI->>HelmValuesConfig: create_empty_config()
    activate HelmValuesConfig

    HelmValuesConfig->>HelmValuesConfig: initialize_empty_structure()
    HelmValuesConfig->>JSON Schema: get_schema_template()
    activate JSON Schema
    JSON Schema-->>HelmValuesConfig: schema template
    deactivate JSON Schema

    HelmValuesConfig->>FileSystem: write_config_file("helm-values.json")
    activate FileSystem
    FileSystem-->>HelmValuesConfig: success
    deactivate FileSystem

    HelmValuesConfig-->>CLI: config instance
    deactivate HelmValuesConfig

    CLI-->>User: "Initialized empty helm-values.json"
    deactivate CLI
```

## 2. Add Deployment Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant HelmValuesConfig
    participant ValueBackend
    participant JSON Schema

    User->>CLI: helm values add-deployment --name=prod --backend=aws
    activate CLI

    CLI->>HelmValuesConfig: load_config("helm-values.json")
    activate HelmValuesConfig

    HelmValuesConfig->>JSON Schema: validate_schema(config_data)
    activate JSON Schema
    JSON Schema-->>HelmValuesConfig: validation result
    deactivate JSON Schema

    CLI->>HelmValuesConfig: add_deployment(name, backend, auth)
    HelmValuesConfig->>ValueBackend: validate_auth_config(auth)
    activate ValueBackend
    ValueBackend-->>HelmValuesConfig: validation result
    deactivate ValueBackend

    HelmValuesConfig->>HelmValuesConfig: update_deployments()
    HelmValuesConfig->>FileSystem: write_config_file()
    activate FileSystem
    FileSystem-->>HelmValuesConfig: success
    deactivate FileSystem

    HelmValuesConfig-->>CLI: success
    deactivate HelmValuesConfig

    CLI-->>User: "Added deployment 'prod'"
    deactivate CLI
```

## 3. Set Value Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant HelmValuesConfig
    participant ValueBackend
    participant Storage

    User->>CLI: helm values set-value path value --env=prod
    activate CLI

    CLI->>HelmValuesConfig: load_config("helm-values.json")
    activate HelmValuesConfig

    HelmValuesConfig->>HelmValuesConfig: validate_path(path)
    HelmValuesConfig->>HelmValuesConfig: get_deployment("prod")
    HelmValuesConfig->>HelmValuesConfig: validate_value(value)

    HelmValuesConfig->>ValueBackend: create_backend(deployment)
    activate ValueBackend
    ValueBackend->>ValueBackend: validate_auth_config()

    ValueBackend->>Storage: set_value(path, "prod", value)
    activate Storage
    Storage-->>ValueBackend: success
    deactivate Storage

    ValueBackend-->>HelmValuesConfig: success
    deactivate ValueBackend

    HelmValuesConfig->>HelmValuesConfig: update_config_file()
    HelmValuesConfig-->>CLI: success
    deactivate HelmValuesConfig

    CLI-->>User: "Value set successfully"
    deactivate CLI
```

## 4. Get Value Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant HelmValuesConfig
    participant ValueBackend
    participant Storage

    User->>CLI: helm values get-value path --env=prod
    activate CLI

    CLI->>HelmValuesConfig: load_config("helm-values.json")
    activate HelmValuesConfig

    HelmValuesConfig->>HelmValuesConfig: validate_path(path)
    HelmValuesConfig->>HelmValuesConfig: get_deployment("prod")

    HelmValuesConfig->>ValueBackend: create_backend(deployment)
    activate ValueBackend
    ValueBackend->>ValueBackend: validate_auth_config()

    ValueBackend->>Storage: get_value(path, "prod")
    activate Storage
    Storage-->>ValueBackend: value
    deactivate Storage

    ValueBackend-->>HelmValuesConfig: value
    deactivate ValueBackend

    HelmValuesConfig-->>CLI: value
    deactivate HelmValuesConfig

    CLI-->>User: display value
    deactivate CLI
```

## 5. Validate Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant HelmValuesConfig
    participant ValueBackend
    participant Validator

    User->>CLI: helm values validate
    activate CLI

    CLI->>HelmValuesConfig: load_config("helm-values.json")
    activate HelmValuesConfig

    HelmValuesConfig->>Validator: validate_schema()
    activate Validator
    Validator-->>HelmValuesConfig: schema validation result
    deactivate Validator

    loop for each deployment
        HelmValuesConfig->>ValueBackend: create_backend(deployment)
        activate ValueBackend
        ValueBackend->>ValueBackend: validate_auth_config()
        ValueBackend->>ValueBackend: test_connection()
        ValueBackend-->>HelmValuesConfig: validation result
        deactivate ValueBackend
    end

    loop for each config value
        HelmValuesConfig->>HelmValuesConfig: validate_value_definition()
        HelmValuesConfig->>HelmValuesConfig: validate_required_values()
    end

    HelmValuesConfig-->>CLI: validation results
    deactivate HelmValuesConfig

    CLI-->>User: display validation report
    deactivate CLI
```

## 6. Generate Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant HelmValuesConfig
    participant ValueBackend
    participant Generator
    participant Storage

    User->>CLI: helm values generate --env=prod
    activate CLI

    CLI->>HelmValuesConfig: load_config("helm-values.json")
    activate HelmValuesConfig

    HelmValuesConfig->>HelmValuesConfig: get_deployment("prod")
    HelmValuesConfig->>ValueBackend: create_backend(deployment)
    activate ValueBackend

    loop for each config value
        ValueBackend->>Storage: get_value(path, "prod")
        activate Storage
        Storage-->>ValueBackend: value
        deactivate Storage
    end

    ValueBackend-->>HelmValuesConfig: all values
    deactivate ValueBackend

    HelmValuesConfig->>Generator: create_values_yaml(values)
    activate Generator
    Generator->>Generator: format_yaml()
    Generator->>Generator: write_file("values.yaml")
    Generator-->>HelmValuesConfig: success
    deactivate Generator

    HelmValuesConfig-->>CLI: success
    deactivate HelmValuesConfig

    CLI-->>User: "Generated values.yaml"
    deactivate CLI
```

## 7. List Values Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant HelmValuesConfig
    participant ValueBackend
    participant Storage
    participant TableFormatter

    User->>CLI: helm values list-values --env=prod
    activate CLI

    CLI->>HelmValuesConfig: load_config("helm-values.json")
    activate HelmValuesConfig

    HelmValuesConfig->>HelmValuesConfig: get_deployment("prod")
    HelmValuesConfig->>ValueBackend: create_backend(deployment)
    activate ValueBackend

    loop for each config value
        ValueBackend->>Storage: get_value(path, "prod")
        activate Storage
        Storage-->>ValueBackend: value
        deactivate Storage
    end

    ValueBackend-->>HelmValuesConfig: all values
    deactivate ValueBackend

    HelmValuesConfig->>TableFormatter: format_table(values)
    activate TableFormatter
    TableFormatter-->>HelmValuesConfig: formatted table
    deactivate TableFormatter

    HelmValuesConfig-->>CLI: formatted table
    deactivate HelmValuesConfig

    CLI-->>User: display values table
    deactivate CLI
```

## 8. List Deployments Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant HelmValuesConfig
    participant TableFormatter

    User->>CLI: helm values list-deployments
    activate CLI

    CLI->>HelmValuesConfig: load_config("helm-values.json")
    activate HelmValuesConfig

    HelmValuesConfig->>HelmValuesConfig: get_all_deployments()

    HelmValuesConfig->>TableFormatter: format_table(deployments)
    activate TableFormatter
    TableFormatter-->>HelmValuesConfig: formatted table
    deactivate TableFormatter

    HelmValuesConfig-->>CLI: formatted table
    deactivate HelmValuesConfig

    CLI-->>User: display deployments table
    deactivate CLI
```

## 9. Remove Deployment Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant HelmValuesConfig
    participant ValueBackend
    participant Storage

    User->>CLI: helm values remove-deployment prod
    activate CLI

    CLI->>HelmValuesConfig: load_config("helm-values.json")
    activate HelmValuesConfig

    HelmValuesConfig->>HelmValuesConfig: validate_deployment_exists("prod")
    HelmValuesConfig->>HelmValuesConfig: check_deployment_in_use()

    HelmValuesConfig->>ValueBackend: create_backend(deployment)
    activate ValueBackend

    ValueBackend->>Storage: cleanup_values("prod")
    activate Storage
    Storage-->>ValueBackend: success
    deactivate Storage

    ValueBackend-->>HelmValuesConfig: success
    deactivate ValueBackend

    HelmValuesConfig->>HelmValuesConfig: remove_deployment("prod")
    HelmValuesConfig->>HelmValuesConfig: write_config_file()

    HelmValuesConfig-->>CLI: success
    deactivate HelmValuesConfig

    CLI-->>User: "Deployment 'prod' removed"
    deactivate CLI
```

## 10. Remove Value Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant HelmValuesConfig
    participant ValueBackend
    participant Storage

    User->>CLI: helm values remove-value path --env=prod
    activate CLI

    CLI->>HelmValuesConfig: load_config("helm-values.json")
    activate HelmValuesConfig

    HelmValuesConfig->>HelmValuesConfig: validate_path(path)
    HelmValuesConfig->>HelmValuesConfig: get_deployment("prod")

    HelmValuesConfig->>ValueBackend: create_backend(deployment)
    activate ValueBackend

    ValueBackend->>Storage: remove_value(path, "prod")
    activate Storage
    Storage-->>ValueBackend: success
    deactivate Storage

    ValueBackend-->>HelmValuesConfig: success
    deactivate ValueBackend

    HelmValuesConfig->>HelmValuesConfig: update_config_file()
    HelmValuesConfig-->>CLI: success
    deactivate HelmValuesConfig

    CLI-->>User: "Value removed successfully"
    deactivate CLI
```

Each diagram shows:
- The exact CLI command being executed
- All components involved in processing the command
- Data flow between components
- Validation steps
- File system operations
- Success/error handling

The main CLI commands covered are:
1. `init` - Initialize new configuration
2. `add-deployment` - Add a new deployment configuration
3. `set-value` - Set a value for a specific path and environment
4. `get-value` - Retrieve a value for a specific path and environment
5. `validate` - Validate the entire configuration
6. `generate` - Generate values.yaml for a specific environment
7. `list-values` - List all values for a specific environment
8. `list-deployments` - List all deployments
9. `remove-deployment` - Remove a deployment configuration
10. `remove-value` - Remove a value for a specific path and environment
