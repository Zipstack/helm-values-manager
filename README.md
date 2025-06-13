# helm-values-manager

A Helm plugin for managing value configurations across multiple environments with schema-driven validation and secret management.

## Installation

```bash
helm plugin install https://github.com/yourusername/helm-values-manager
```

## Usage

Initialize a new schema:
```bash
helm values-manager init
```

Add a value to the schema:
```bash
helm values-manager schema add
```

Set values for an environment:
```bash
helm values-manager values set --env dev
```

Generate values.yaml:
```bash
helm values-manager generate --env dev
```