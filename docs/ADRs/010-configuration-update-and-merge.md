# ADR-010: Configuration Update and Merge

Date: 2025-02-27

## Status

Proposed

## Context

Chart owners may update their configuration schema over time, adding new configuration paths, modifying metadata, or removing obsolete paths. Users who have already configured their deployments need a way to incorporate these updates without losing their existing configurations.

Currently, the Helm Values Manager does not provide a mechanism to update an existing configuration with changes from a new version. This leads to several challenges:

1. Users must manually identify and apply changes between configuration versions
2. There's a risk of missing new required configuration paths
3. Users may lose their existing values when updating to a new configuration
4. Conflicts between user customizations and chart owner updates are difficult to resolve

A structured approach to configuration updates would improve the user experience and reduce the risk of configuration errors.

## Decision

We will implement a configuration update and merge feature that allows users to incorporate changes from a new configuration file while preserving their existing values and deployments.

The feature will:

1. Compare the current configuration with the new one to identify:
   - Added configuration paths
   - Removed configuration paths
   - Modified metadata (description, required, sensitive flags)
   - Potential conflicts

2. Provide multiple merge strategies:
   - "Smart" (default): Preserve user values while adopting new metadata and paths
   - "Theirs": Prefer the new configuration but keep existing values where possible
   - "Ours": Prefer the existing configuration but add new paths

3. Validate the merged configuration to ensure it meets all requirements
   - Identify missing required values
   - Ensure all paths have valid values for their environments

4. Provide clear reporting of changes and required actions

This will be implemented as a new `update-config` command in the CLI.

## Consequences

### Positive

- Users can easily update their configurations when chart owners release updates
- Existing user values are preserved during updates
- New required configurations are clearly identified
- The risk of missing important configuration changes is reduced
- The update process becomes more transparent and less error-prone

### Negative

- Adds complexity to the codebase
- May require additional schema versioning to handle major changes
- Conflict resolution might still require manual intervention in complex cases

### Neutral

- Users will need to learn a new command and its options
- May need to adjust the configuration schema to better support versioning and updates

## Implementation Notes

The implementation will require:

1. A new `UpdateConfigCommand` class that extends `BaseCommand`
2. Configuration comparison logic to identify differences
3. Merge strategies to combine configurations
4. Validation to ensure the merged configuration is valid
5. Reporting to communicate changes and required actions

The command will be exposed through the CLI as:

```
helm values update-config [source-file] [--strategy=smart|theirs|ours] [--report-only]
```

## Related Issues

- GitHub Issue [#19](https://github.com/Zipstack/helm-values-manager/issues/19): Configuration Update and Merge Feature
