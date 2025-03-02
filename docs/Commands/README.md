# Command Reference

This document provides detailed information about all available commands in the Helm Values Manager plugin.

## Available Commands
- [`init`](#init) - Initialize a new values manager configuration.
- [`add-value-config`](#add-value-config) - Add a new value configuration with metadata.
- [`add-deployment`](#add-deployment) - Add a new deployment configuration.
- [`set-value`](#set-value) - Set a value for a specific path and deployment.
- [`generate`](#generate) - Generate a values file for a specific deployment.

## Command Details

### `init`

Initialize a new values manager configuration.

**Usage:**
```bash
helm values-manager init [options]
```

**Options:**
- `--release, -r`: Name of the Helm release

### `add-value-config`

Add a new value configuration with metadata.

**Usage:**
```bash
helm values-manager add-value-config [options]
```

**Options:**
- `--path, -p`: Configuration path (e.g., 'app.replicas')
- `--description, -d`: Description of what this configuration does (default: empty string)
- `--required, -r`: Whether this configuration is required (default: False)

### `add-deployment`

Add a new deployment configuration.

**Usage:**
```bash
helm values-manager add-deployment [options]
```

**Arguments:**
- `name`: Deployment name (e.g., 'dev', 'prod')

### `set-value`

Set a value for a specific path and deployment.

**Usage:**
```bash
helm values-manager set-value [options]
```

**Options:**
- `--path, -p`: Configuration path (e.g., 'app.replicas')
- `--deployment, -d`: Deployment to set the value for (e.g., 'dev', 'prod')
- `--value, -v`: Value to set

### `generate`

Generate a values file for a specific deployment.

**Usage:**
```bash
helm values-manager generate [options]
```

**Options:**
- `--deployment, -d`: Deployment to generate values for (e.g., 'dev', 'prod')
- `--output, -o`: Directory to output the values file to (default: current directory) (default: .)

## Using Help

Each command supports the `--help` flag for detailed information:

```bash
helm values-manager --help
helm values-manager <command> --help
```
