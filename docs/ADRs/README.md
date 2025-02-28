# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) for the Helm Values Manager project.

## What is an ADR?
An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences.

## Creating New ADRs

For new ADRs, use the [ADR template](adr-template.md) as a starting point.

## ADR Index

### [ADR-001: Helm Values Manager as a Helm Plugin](001-helm-values-manager.md)
- **Status**: Accepted
- **Context**: Need for managing configurations and secrets across multiple Kubernetes deployments
- **Decision**: Implement as a Helm plugin in Python with key-value storage model
- **Impact**: Defines core architecture and integration approach

### [ADR-002: Config Path and Storage Design](002-config-path-and-storage-design.md)
- **Status**: Accepted
- **Context**: Need for separate config definition from value storage
- **Decision**: Implement path map and standardized command pattern
- **Impact**: Establishes core data structures and file operations
- **Dependencies**: ADR-001

### [ADR-003: Unified Path and Value Storage](003-unified-path-value-storage.md)
- **Status**: Accepted
- **Context**: Complexity from separate path and value storage
- **Decision**: Unified dictionary structure for paths and values
- **Impact**: Simplifies storage and improves consistency
- **Dependencies**: ADR-002

### [ADR-004: Value Resolution Strategy](004-value-resolution-strategy.md)
- **Status**: Accepted
- **Context**: Need for clear value resolution in unified storage
- **Decision**: Introduce Value class for encapsulation
- **Impact**: Clarifies value handling and storage strategy
- **Dependencies**: ADR-003

### [ADR-005: Unified Backend Approach](005-unified-backend-approach.md)
- **Status**: Accepted
- **Context**: Split logic in Value class for different storage types
- **Decision**: Remove storage type distinction, use SimpleValueBackend
- **Impact**: Simplifies Value class and unifies storage interface
- **Dependencies**: ADR-004

### [ADR-006: Helm-Style Logging System](006-helm-style-logging.md)
- **Status**: Accepted
- **Context**: Need for consistent logging following Helm conventions
- **Decision**: Implement HelmLogger with Helm-style output
- **Impact**: Ensures consistent user experience and debugging
- **Dependencies**: ADR-001

### [ADR-007: Sensitive Value Storage](007-sensitive-value-storage.md)
- **Status**: Accepted
- **Context**: Need for secure handling of sensitive configuration values
- **Decision**: Store sensitive values using reference-based approach in secure backends
- **Impact**: Ensures security while maintaining flexibility and traceability
- **Dependencies**: ADR-005

### [ADR-008: Remove Command Registry](008-remove-command-registry.md)
- **Status**: Accepted
- **Context**: Command Registry pattern adds unnecessary complexity
- **Decision**: Remove registry in favor of direct command instantiation
- **Impact**: Simplifies code and aligns better with Typer's design

### [ADR-009: Custom Configuration File Paths](009-custom-configuration-file-paths.md)
- **Status**: Proposed
- **Context**: Limited flexibility with hardcoded configuration file paths
- **Decision**: Add support for custom configuration file paths
- **Impact**: Increases flexibility and improves integration capabilities
- **Dependencies**: ADR-001

### [ADR-010: Configuration Update and Merge](010-configuration-update-and-merge.md)
- **Status**: Proposed
- **Context**: Need to incorporate chart owner configuration updates without losing user customizations
- **Decision**: Implement configuration comparison and smart merging with multiple strategies
- **Impact**: Simplifies configuration updates and reduces risk of missing required changes
- **Dependencies**: ADR-001

### [ADR-011: Command Structure for Deployments and Backends](011-command-structure-for-deployments.md)
- **Status**: Accepted
- **Context**: Need for intuitive command structure for managing deployments with multiple backends and auth types
- **Decision**: Implement nested subcommand structure for deployment, backend, and auth configuration
- **Impact**: Improves user experience, discoverability, and maintainability
- **Dependencies**: ADR-001
