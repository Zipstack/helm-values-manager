# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-15

### Added
- Initial release of helm-values-manager
- Schema-driven configuration management for Helm values
- Multi-environment support (dev, staging, prod, etc.)
- Interactive CLI commands for schema and values management
- Secret management with environment variable support
- Type validation for all value types (string, number, boolean, array, object)
- Values generation to standard values.yaml format
- Comprehensive validation with detailed error reporting
- Default value support with removal capability
- Helm plugin and standalone CLI installation options
- Rich terminal output with color support
- Comprehensive test suite with 98+ tests

### Features
- `init` - Initialize new schema.json with optional force flag
- `schema add` - Interactive schema entry creation
- `schema list/get/update/remove` - Full CRUD for schema entries
- `values set/set-secret` - Set regular and secret values per environment
- `values get/list/remove` - Manage environment-specific values
- `values init` - Interactive setup for unset values
- `validate` - Validate schema and values with detailed error reporting
- `generate` - Generate values.yaml for specific environments

### Security
- Secrets stored as references, resolved only at generation time
- Environment variable validation for secret references
- No actual secrets stored in configuration files

[1.0.0]: https://github.com/Zipstack/helm-values-manager/releases/tag/v1.0.0