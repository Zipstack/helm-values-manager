# ADR-011: Command Structure for Deployments and Backends

Date: 2025-02-28

## Status

Accepted

## Context

The Helm Values Manager needs to support multiple backend types (git-secret, aws, azure, gcp) and authentication methods (env, file, direct, managed_identity) for storing and retrieving values. The current implementation uses a single `add-deployment` command with many parameters, which can be complex and difficult to use.

As we implement more backend types and authentication methods, the command structure needs to be intuitive, discoverable, and maintainable. The command interface should guide users to provide the correct parameters for each backend and authentication type.

## Decision

We will adopt a nested subcommand structure for deployment and backend management with the following pattern:

```
helm values add-deployment [name]

helm values add-backend [backend] --deployment=[name] [backend_options]
  - helm values add-backend aws --deployment=prod --region=us-west-2
  - helm values add-backend azure --deployment=prod --vault-url=https://myvault.vault.azure.net
  - helm values add-backend gcp --deployment=prod --project-id=my-project
  - helm values add-backend git-secret --deployment=prod
```

Initially, deployments will be created with a `no-backend` type and `no-auth` authentication, indicating that they don't have a backend or authentication configured yet. This allows for deployments that might not need sensitive values, while providing a clear path to add a backend later if needed.

For authentication, we will use a similar pattern:

```
helm values add-auth [auth_type] --deployment=[name] [auth_options]
  - helm values add-auth direct --deployment=prod --credentials='{...}'
  - helm values add-auth env --deployment=prod --env-prefix=AWS_
  - helm values add-auth file --deployment=prod --auth-path=~/.aws/credentials
  - helm values add-auth managed-identity --deployment=prod
```

This approach:
1. Separates the concerns of creating a deployment, configuring a backend, and setting up authentication
2. Uses subcommands to provide context-specific options and help text
3. Follows a natural workflow of first creating a deployment, then adding backend and auth configuration
4. Supports deployments without sensitive values through the `no-backend` option

For the initial implementation, we will only implement the `add-deployment` command, with the backend and auth commands to be implemented later.

## Consequences

### Positive

- **Improved User Experience**: Users only see options relevant to their current task
- **Better Discoverability**: Each subcommand can have its own help text explaining the specific options
- **Progressive Disclosure**: Complex options are only shown when needed
- **Reduced Cognitive Load**: Users don't need to remember all possible combinations of options
- **Better Validation**: Each command can validate its specific inputs more effectively
- **Maintainability**: New backend types and auth methods can be added without changing existing commands
- **Flexibility**: Users can create deployments without immediately configuring backends, allowing for more flexible workflows
- **Safety**: The `no-backend` option provides a clear indication that a deployment is not configured for sensitive values, and validation can prevent adding sensitive values to such deployments

### Negative

- **More Commands**: Users need to run multiple commands to fully configure a deployment
- **Learning Curve**: Users need to learn the command structure and workflow
- **Implementation Complexity**: More commands means more code to maintain

### Neutral

- **Alignment with Other Tools**: This approach is similar to other CLI tools like `git` and `kubectl`
- **Documentation Requirements**: We will need to document the command workflow clearly

## Implementation Notes

1. For the initial implementation, we will only implement the `add-deployment` command, which will create a deployment with minimal configuration.
2. The `add-deployment` command will validate that the deployment name is unique and create a basic deployment entry in the configuration.
3. The backend and auth commands will be implemented later, with appropriate validation to ensure that the referenced deployment exists.
4. We will use Typer's nested command structure to implement this design.
5. The `Deployment` class will need to support a "partial" state where backend and auth configuration may not be fully defined yet.

## Related Issues

- GitHub Issue #[TBD]: Implement command structure for deployments and backends
