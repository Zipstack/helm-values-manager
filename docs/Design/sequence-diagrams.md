# Helm Values Manager - CLI Command Sequence Diagrams

## 1. Init Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant BaseCommand
    participant HelmValuesConfig
    participant FileSystem

    User->>CLI: helm values init
    activate CLI

    CLI->>BaseCommand: execute()
    activate BaseCommand

    BaseCommand->>BaseCommand: acquire_lock()
    BaseCommand->>HelmValuesConfig: create_empty_config()
    activate HelmValuesConfig

    HelmValuesConfig->>HelmValuesConfig: initialize_empty_structure()
    HelmValuesConfig->>JSON Schema: get_schema_template()
    activate JSON Schema
    JSON Schema-->>HelmValuesConfig: schema template
    deactivate JSON Schema

    HelmValuesConfig-->>BaseCommand: config instance
    deactivate HelmValuesConfig

    BaseCommand->>FileSystem: write_config_file()
    activate FileSystem
    FileSystem-->>BaseCommand: success
    deactivate FileSystem

    BaseCommand->>BaseCommand: release_lock()
    BaseCommand-->>CLI: success
    deactivate BaseCommand

    CLI-->>User: "Initialized empty helm-values.json"
    deactivate CLI
```

## 2. Add Value Config Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant BaseCommand
    participant HelmValuesConfig
    participant PathValidator

    User->>CLI: helm values add-value-config --path=app.replicas --required
    activate CLI

    CLI->>BaseCommand: execute()
    activate BaseCommand

    BaseCommand->>BaseCommand: acquire_lock()
    BaseCommand->>BaseCommand: load_config()
    BaseCommand->>HelmValuesConfig: add_config_path(path, description, required)
    activate HelmValuesConfig

    HelmValuesConfig->>PathValidator: validate_path(path)
    activate PathValidator
    PathValidator-->>HelmValuesConfig: validation result
    deactivate PathValidator

    HelmValuesConfig->>HelmValuesConfig: create_path_data()
    HelmValuesConfig-->>BaseCommand: success
    deactivate HelmValuesConfig

    BaseCommand->>FileSystem: write_config_file()
    BaseCommand->>BaseCommand: release_lock()
    BaseCommand-->>CLI: success
    deactivate BaseCommand

    CLI-->>User: "Added value config 'app.replicas'"
    deactivate CLI
```

## 3. Add Deployment Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant BaseCommand
    participant HelmValuesConfig

    User->>CLI: helm values add-deployment prod
    activate CLI

    CLI->>BaseCommand: execute()
    activate BaseCommand

    BaseCommand->>BaseCommand: acquire_lock()
    BaseCommand->>BaseCommand: load_config()
    BaseCommand->>HelmValuesConfig: add_deployment(name)
    activate HelmValuesConfig

    HelmValuesConfig->>HelmValuesConfig: validate_deployment_name(name)
    HelmValuesConfig->>HelmValuesConfig: create_deployment(name)
    HelmValuesConfig-->>BaseCommand: success
    deactivate HelmValuesConfig

    BaseCommand->>FileSystem: write_config_file()
    activate FileSystem
    FileSystem-->>BaseCommand: success
    deactivate FileSystem

    BaseCommand->>BaseCommand: release_lock()
    BaseCommand-->>CLI: success
    deactivate BaseCommand

    CLI-->>User: "Added deployment 'prod'"
    deactivate CLI
```

## 3.1 Add Backend Command Flow (Future Implementation)

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant BaseCommand
    participant HelmValuesConfig
    participant ValueBackend

    User->>CLI: helm values add-backend aws --deployment=prod --region=us-west-2
    activate CLI

    CLI->>BaseCommand: execute()
    activate BaseCommand

    BaseCommand->>BaseCommand: acquire_lock()
    BaseCommand->>BaseCommand: load_config()
    BaseCommand->>HelmValuesConfig: add_backend_to_deployment(name, backend, backend_config)
    activate HelmValuesConfig

    HelmValuesConfig->>HelmValuesConfig: validate_deployment_exists(name)
    HelmValuesConfig->>ValueBackend: validate_backend_config(backend, backend_config)
    activate ValueBackend
    ValueBackend-->>HelmValuesConfig: validation result
    deactivate ValueBackend

    HelmValuesConfig->>HelmValuesConfig: update_deployment_backend(name, backend, backend_config)
    HelmValuesConfig-->>BaseCommand: success
    deactivate HelmValuesConfig

    BaseCommand->>FileSystem: write_config_file()
    activate FileSystem
    FileSystem-->>BaseCommand: success
    deactivate FileSystem

    BaseCommand->>BaseCommand: release_lock()
    BaseCommand-->>CLI: success
    deactivate BaseCommand

    CLI-->>User: "Added aws backend to deployment 'prod'"
    deactivate CLI
```

## 3.2 Add Auth Command Flow (Future Implementation)

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant BaseCommand
    participant HelmValuesConfig
    participant ValueBackend

    User->>CLI: helm values add-auth direct --deployment=prod --credentials='{...}'
    activate CLI

    CLI->>BaseCommand: execute()
    activate BaseCommand

    BaseCommand->>BaseCommand: acquire_lock()
    BaseCommand->>BaseCommand: load_config()
    BaseCommand->>HelmValuesConfig: add_auth_to_deployment(name, auth_type, auth_config)
    activate HelmValuesConfig

    HelmValuesConfig->>HelmValuesConfig: validate_deployment_exists(name)
    HelmValuesConfig->>ValueBackend: validate_auth_config(auth_type, auth_config)
    activate ValueBackend
    ValueBackend-->>HelmValuesConfig: validation result
    deactivate ValueBackend

    HelmValuesConfig->>HelmValuesConfig: update_deployment_auth(name, auth_type, auth_config)
    HelmValuesConfig-->>BaseCommand: success
    deactivate HelmValuesConfig

    BaseCommand->>FileSystem: write_config_file()
    activate FileSystem
    FileSystem-->>BaseCommand: success
    deactivate FileSystem

    BaseCommand->>BaseCommand: release_lock()
    BaseCommand-->>CLI: success
    deactivate BaseCommand

    CLI-->>User: "Added direct authentication to deployment 'prod'"
    deactivate CLI
```

## 4. Set Value Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant BaseCommand
    participant HelmValuesConfig
    participant Value
    participant ValueBackend
    participant Storage

    User->>CLI: helm values set-value path value --env=prod
    activate CLI

    CLI->>BaseCommand: execute()
    activate BaseCommand

    BaseCommand->>BaseCommand: acquire_lock()
    BaseCommand->>BaseCommand: load_config()
    BaseCommand->>HelmValuesConfig: set_value(path, env, value)
    activate HelmValuesConfig

    HelmValuesConfig->>HelmValuesConfig: find_config_item(path)
    HelmValuesConfig->>HelmValuesConfig: get_backend_for_config(config_item, env)

    alt Sensitive Value
        HelmValuesConfig->>HelmValuesConfig: get_deployment(env)
        HelmValuesConfig->>ValueBackend: create_secure_backend(deployment)
    else Non-Sensitive Value
        HelmValuesConfig->>ValueBackend: create_simple_backend()
    end

    HelmValuesConfig->>Value: create(path, env, backend)
    activate Value
    Value->>ValueBackend: set_value(path, env, value)
    activate ValueBackend

    alt Secure Backend
        ValueBackend->>Storage: write(key, value)
        Storage-->>ValueBackend: success
    end

    ValueBackend-->>Value: success
    deactivate ValueBackend
    Value-->>HelmValuesConfig: success
    deactivate Value

    HelmValuesConfig-->>BaseCommand: success
    deactivate HelmValuesConfig

    BaseCommand->>FileSystem: write_config_file()
    BaseCommand->>BaseCommand: release_lock()
    BaseCommand-->>CLI: success
    deactivate BaseCommand

    CLI-->>User: "Value set successfully"
    deactivate CLI
```

## 5. Get Value Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant BaseCommand
    participant HelmValuesConfig
    participant Value
    participant ValueBackend
    participant Storage

    User->>CLI: helm values get-value path --env=prod
    activate CLI

    CLI->>BaseCommand: execute()
    activate BaseCommand

    BaseCommand->>BaseCommand: acquire_lock()
    BaseCommand->>BaseCommand: load_config()
    BaseCommand->>HelmValuesConfig: get_value(path, env)
    activate HelmValuesConfig

    HelmValuesConfig->>HelmValuesConfig: find_config_item(path)
    HelmValuesConfig->>HelmValuesConfig: get_backend_for_config(config_item, env)

    alt Sensitive Value
        HelmValuesConfig->>HelmValuesConfig: get_deployment(env)
        HelmValuesConfig->>ValueBackend: create_secure_backend(deployment)
    else Non-Sensitive Value
        HelmValuesConfig->>ValueBackend: create_simple_backend()
    end

    HelmValuesConfig->>Value: create(path, env, backend)
    activate Value
    Value->>ValueBackend: get_value(path, env)
    activate ValueBackend

    alt Secure Backend
        ValueBackend->>Storage: read(key)
        Storage-->>ValueBackend: value
    end

    ValueBackend-->>Value: value
    deactivate ValueBackend
    Value-->>HelmValuesConfig: value
    deactivate Value

    HelmValuesConfig-->>BaseCommand: value
    deactivate HelmValuesConfig

    BaseCommand->>BaseCommand: release_lock()
    BaseCommand-->>CLI: value
    deactivate BaseCommand

    CLI-->>User: value
    deactivate CLI
```

## 6. Validate Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant BaseCommand
    participant HelmValuesConfig
    participant ValueBackend
    participant Validator

    User->>CLI: helm values validate
    activate CLI

    CLI->>BaseCommand: execute()
    activate BaseCommand

    BaseCommand->>BaseCommand: load_config()
    BaseCommand->>HelmValuesConfig: validate_schema()
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

    HelmValuesConfig-->>BaseCommand: validation results
    deactivate HelmValuesConfig

    BaseCommand-->>CLI: validation results
    deactivate BaseCommand

    CLI-->>User: display validation report
    deactivate CLI
```

## 7. Generate Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant BaseCommand
    participant HelmValuesConfig
    participant Value
    participant ValueBackend
    participant Generator

    User->>CLI: helm values generate --env=prod
    activate CLI

    CLI->>BaseCommand: execute()
    activate BaseCommand

    BaseCommand->>BaseCommand: load_config()
    BaseCommand->>HelmValuesConfig: get_all_values(env)
    activate HelmValuesConfig

    loop For Each Path
        HelmValuesConfig->>Value: get()
        activate Value

        alt Local Storage
            Value->>Value: return_local_value()
        else Remote Storage
            Value->>ValueBackend: get_value(key)
            ValueBackend-->>Value: value
        end

        Value-->>HelmValuesConfig: resolved_value
        deactivate Value
    end

    HelmValuesConfig->>Generator: create_values_yaml(values)
    activate Generator
    Generator-->>HelmValuesConfig: yaml_content
    deactivate Generator

    HelmValuesConfig-->>BaseCommand: yaml_content
    deactivate HelmValuesConfig

    BaseCommand->>FileSystem: write_values_yaml()
    BaseCommand-->>CLI: success
    deactivate BaseCommand

    CLI-->>User: "Generated values.yaml"
    deactivate CLI
```

## 8. List Values Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant BaseCommand
    participant HelmValuesConfig
    participant Value
    participant ValueBackend
    participant Storage
    participant TableFormatter

    User->>CLI: helm values list-values --env=prod
    activate CLI

    CLI->>BaseCommand: execute()
    activate BaseCommand

    BaseCommand->>BaseCommand: load_config()
    BaseCommand->>HelmValuesConfig: get_deployment("prod")
    activate HelmValuesConfig

    HelmValuesConfig->>Value: get()
    activate Value

    alt Local Storage
        Value->>Value: return_local_value()
    else Remote Storage
        Value->>ValueBackend: get_value(key)
        ValueBackend-->>Value: value
    end

    Value-->>HelmValuesConfig: resolved_value
    deactivate Value

    HelmValuesConfig->>TableFormatter: format_table(values)
    activate TableFormatter
    TableFormatter-->>HelmValuesConfig: formatted table
    deactivate TableFormatter

    HelmValuesConfig-->>BaseCommand: formatted table
    deactivate HelmValuesConfig

    BaseCommand-->>CLI: formatted table
    deactivate BaseCommand

    CLI-->>User: display values table
    deactivate CLI
```

## 9. List Deployments Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant BaseCommand
    participant HelmValuesConfig
    participant TableFormatter

    User->>CLI: helm values list-deployments
    activate CLI

    CLI->>BaseCommand: execute()
    activate BaseCommand

    BaseCommand->>BaseCommand: load_config()
    BaseCommand->>HelmValuesConfig: get_all_deployments()
    activate HelmValuesConfig

    HelmValuesConfig->>TableFormatter: format_table(deployments)
    activate TableFormatter
    TableFormatter-->>HelmValuesConfig: formatted table
    deactivate TableFormatter

    HelmValuesConfig-->>BaseCommand: formatted table
    deactivate HelmValuesConfig

    BaseCommand-->>CLI: formatted table
    deactivate BaseCommand

    CLI-->>User: display deployments table
    deactivate CLI
```

## 10. Remove Deployment Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant BaseCommand
    participant HelmValuesConfig
    participant ValueBackend
    participant Storage

    User->>CLI: helm values remove-deployment prod
    activate CLI

    CLI->>BaseCommand: execute()
    activate BaseCommand

    BaseCommand->>BaseCommand: acquire_lock()
    BaseCommand->>BaseCommand: load_config()
    BaseCommand->>HelmValuesConfig: validate_deployment_exists("prod")
    activate HelmValuesConfig

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

    HelmValuesConfig-->>BaseCommand: success
    deactivate HelmValuesConfig

    BaseCommand->>BaseCommand: release_lock()
    BaseCommand-->>CLI: success
    deactivate BaseCommand

    CLI-->>User: "Deployment 'prod' removed"
    deactivate CLI
```

## 11. Remove Value Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant BaseCommand
    participant HelmValuesConfig
    participant Value
    participant ValueBackend
    participant Storage

    User->>CLI: helm values remove-value path --env=prod
    activate CLI

    CLI->>BaseCommand: execute()
    activate BaseCommand

    BaseCommand->>BaseCommand: acquire_lock()
    BaseCommand->>BaseCommand: load_config()
    BaseCommand->>HelmValuesConfig: validate_path(path)
    activate HelmValuesConfig

    HelmValuesConfig->>HelmValuesConfig: get_deployment("prod")

    HelmValuesConfig->>Value: remove()
    activate Value

    alt Local Storage
        Value->>Value: remove_local_value()
    else Remote Storage
        Value->>ValueBackend: remove_value(key)
        ValueBackend-->>Value: success
    end

    Value-->>HelmValuesConfig: success
    deactivate Value

    HelmValuesConfig->>HelmValuesConfig: update_config_file()
    HelmValuesConfig-->>BaseCommand: success
    deactivate HelmValuesConfig

    BaseCommand->>BaseCommand: release_lock()
    BaseCommand-->>CLI: success
    deactivate BaseCommand

    CLI-->>User: "Value removed successfully"
    deactivate CLI
```

## 12. Remove Value Config Command Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant BaseCommand
    participant HelmValuesConfig
    participant Value

    User->>CLI: helm values remove-value-config --path=app.replicas
    activate CLI

    CLI->>BaseCommand: execute()
    activate BaseCommand

    BaseCommand->>BaseCommand: acquire_lock()
    BaseCommand->>BaseCommand: load_config()
    BaseCommand->>HelmValuesConfig: remove_config_path(path)
    activate HelmValuesConfig

    HelmValuesConfig->>HelmValuesConfig: check_path_exists(path)

    alt Has Values
        HelmValuesConfig->>HelmValuesConfig: check_no_values_exist(path)
        loop For Each Environment
            HelmValuesConfig->>Value: remove()
            Value-->>HelmValuesConfig: success
        end
    end

    HelmValuesConfig->>HelmValuesConfig: remove_path_data()
    HelmValuesConfig-->>BaseCommand: success
    deactivate HelmValuesConfig

    BaseCommand->>FileSystem: write_config_file()
    BaseCommand->>BaseCommand: release_lock()
    BaseCommand-->>CLI: success
    deactivate BaseCommand

    CLI-->>User: "Removed value config 'app.replicas'"
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
2. `add-value-config` - Define a new value configuration with metadata
3. `add-deployment` - Add a new deployment configuration
4. `set-value` - Set a value for a specific path and environment
5. `get-value` - Retrieve a value for a specific path and environment
6. `validate` - Validate the entire configuration
7. `generate` - Generate values.yaml for a specific environment
8. `list-values` - List all values for a specific environment
9. `list-deployments` - List all deployments
10. `remove-deployment` - Remove a deployment configuration
11. `remove-value` - Remove a value for a specific path and environment
12. `remove-value-config` - Remove a value configuration and its associated values
