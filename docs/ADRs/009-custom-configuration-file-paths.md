# 9. Custom Configuration File Paths

Date: 2025-02-27

## Status

Proposed

## Context

Currently, the Helm Values Manager uses hardcoded file paths for its configuration and lock files:
- Configuration file: `helm-values.json`
- Lock file: `.helm-values.lock`

These paths are defined in the `BaseCommand` class and used across all commands. This approach has several limitations:

1. **Limited Flexibility**: Users cannot manage multiple configurations in the same directory
2. **Naming Constraints**: Organizations may have specific naming conventions that conflict with our hardcoded names
3. **Integration Challenges**: Difficult to integrate with existing systems that might have their own file organization
4. **Location Restrictions**: Configuration files must be in the current working directory

Users have expressed interest in being able to specify custom file paths for their configuration files, which would address these limitations and provide greater flexibility.

## Decision

We will enhance the Helm Values Manager to support custom configuration file paths by:

1. **Adding a `--config-file` option to all commands**:
   ```python
   config_file: str = typer.Option(
       "helm-values.json",
       "--config-file",
       "-c",
       help="Path to the configuration file"
   )
   ```

2. **Updating the `BaseCommand` class to accept a config file path**:
   ```python
   def __init__(self, config_file: str = "helm-values.json") -> None:
       """Initialize the base command.

       Args:
           config_file: Path to the configuration file
       """
       self.config_file = config_file
       self.lock_file = self._generate_lock_file_path(config_file)
       self._lock_fd: Optional[int] = None
   ```

3. **Generating the lock file name based on the config file path**:
   ```python
   def _generate_lock_file_path(self, config_file: str) -> str:
       """Generate the lock file path based on the config file path.

       Args:
           config_file: Path to the configuration file

       Returns:
           str: Path to the lock file
       """
       # Expand user home directory if present (e.g., ~/configs)
       expanded_path = os.path.expanduser(config_file)
       config_path = Path(expanded_path)

       # Check if the path is a directory
       if config_path.is_dir():
           # Use default filename in the specified directory
           config_path = config_path / "helm-values.json"

       # Create lock file name based on the config file stem (name without extension)
       lock_file = f".{config_path.stem}.lock"
       return str(config_path.parent / lock_file)
   ```

4. **Propagating the config file path to all command instances**:
   ```python
   @app.command()
   def init(
       release_name: str = typer.Option(..., "--release", "-r", help="Name of the Helm release"),
       config_file: str = typer.Option("helm-values.json", "--config-file", "-c", help="Path to the configuration file"),
   ):
       """Initialize a new helm-values configuration."""
       command = InitCommand(config_file=config_file)
       result = command.execute(release_name=release_name)
       echo(result)
   ```

## Consequences

### Positive

1. **Increased Flexibility**: Users can manage multiple configurations in the same directory
2. **Custom Naming**: Organizations can follow their own naming conventions
3. **Better Integration**: Easier to integrate with existing systems and workflows
4. **Location Freedom**: Configuration files can be placed in any directory

### Negative

1. **API Change**: All command functions need to be updated to accept the new parameter
2. **Complexity**: Slightly more complex code to handle different file paths
3. **Testing**: Additional test cases needed to verify the functionality
4. **Documentation**: Documentation needs to be updated to reflect the new option

### Neutral

1. **Backward Compatibility**: Default values ensure backward compatibility with existing usage
2. **Lock File Naming**: Lock files will be named based on the configuration file name

## Implementation Notes

1. The implementation should be backward compatible, using the current hardcoded paths as defaults
2. All commands should propagate the config file path to their respective command instances
3. Documentation should be updated to reflect the new option
4. Tests should be added to verify the functionality with custom file paths

## Related Issues

- GitHub Issue [#17](https://github.com/Zipstack/helm-values-manager/issues/17): Support for custom configuration file paths
