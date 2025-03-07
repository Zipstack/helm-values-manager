# ADR-012: Backend-Specific Command Registration

Date: 2025-03-07

## Status

Proposed

## Context

In [ADR-011](011-command-structure-for-deployments.md), we established a command structure for deployments and backends using a nested subcommand pattern. This ADR builds upon and extends that foundation rather than replacing it. The nested subcommand structure defined in ADR-011 remains valid and forms the basis for our enhanced approach.

As we implement more backend types with varying authentication methods and configuration options, we've identified an opportunity to further improve the user experience.

The current approach uses a generic `add-backend` command with many parameters, which requires users to know which parameters are applicable to which backend type. This can lead to confusion and errors, especially as we add more backend types with specialized configuration requirements.

We need a more intuitive and maintainable way to expose backend-specific options while ensuring that users only see options relevant to their chosen backend.

## Decision

We will implement a backend-specific command registration system that automatically generates backend-specific commands based on the available backend implementations. This approach will:

1. Create dedicated commands for each backend type (e.g., `add-backend-aws`, `add-backend-gcp`, `add-backend-azure`)
2. Expose only the relevant options for each backend type
3. Provide backend-specific help text and validation
4. Allow for easy addition of new backends without modifying the core command structure

The implementation will use a decorator pattern to register backend classes and their associated CLI options:

```python
# Base backend registration decorator
def register_backend(backend_type: str, description: str):
    def decorator(cls):
        # Register the backend class with the command registry
        return cls
    return decorator

# Example usage
@register_backend("aws", "AWS Secret Manager backend")
class AWSSecretManagerBackend(ValueBackend):
    # Backend implementation
    pass

@register_backend("gcp", "Google Cloud Secret Manager backend")
class GCPSecretManagerBackend(ValueBackend):
    # Backend implementation
    pass
```

Each backend class will define its specific CLI options using a schema or configuration object:

```python
@register_backend("gcp", "Google Cloud Secret Manager backend")
class GCPSecretManagerBackend(ValueBackend):
    # Define CLI options for this backend
    cli_options = [
        CliOption("--service-account", help="Service account JSON credentials", required=True),
        CliOption("--project-id", help="GCP project ID", required=False),
    ]

    # Backend implementation
    def __init__(self, auth_config: Dict[str, str]) -> None:
        # Initialize with backend-specific options
        pass
```

The command registration system will dynamically generate commands at runtime:

```
helm values add-backend-gcp --deployment=prod --service-account='{...}'
helm values add-backend-aws --deployment=prod --region=us-west-2 --profile=default
```

This approach maintains compatibility with the existing command structure while providing a more intuitive interface for backend-specific configuration.

## Consequences

### Positive

- **Improved User Experience**: Users only see options relevant to their chosen backend
- **Better Discoverability**: Each backend command has its own help text
- **Type Safety**: Backend-specific options can be strongly typed and validated
- **Maintainability**: New backends can be added without modifying existing code
- **Documentation**: Help text is automatically generated from backend definitions
- **Consistency**: All backends follow the same registration pattern

### Negative

- **Implementation Complexity**: Requires a more sophisticated command registration system
- **Learning Curve**: Developers adding new backends need to understand the registration pattern
- **Command Proliferation**: More commands in the CLI interface

### Neutral

- **Compatibility**: Maintains compatibility with the existing command structure
- **Testing**: Requires testing of dynamically generated commands

## Implementation Notes

1. Create a backend registry that tracks available backend types and their options
2. Implement a decorator for registering backend classes
3. Define a schema for backend CLI options
4. Create a command generator that builds Typer commands from backend definitions
5. Update the CLI entrypoint to include dynamically generated commands
6. Update documentation to reflect the new command structure

## Related Issues

- GitHub Issue #[TBD]: Implement backend-specific command registration
