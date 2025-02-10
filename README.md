# Helm Values Manager

🚀 A powerful Helm plugin for managing values and secrets across multiple environments.

## Features

- 🔐 **Secure Secret Management**: Safely handle sensitive data
- 🌍 **Multi-Environment Support**: Manage values for dev, staging, prod, and more
- 🔄 **Value Inheritance**: Define common values and override per environment
- 🔍 **Secret Detection**: Automatically identify and protect sensitive data
- 📦 **Easy Integration**: Works seamlessly with existing Helm workflows

## Requirements

- Python 3.9 or higher
- Helm 3.x
- pip (Python package installer)

## Installation

```bash
helm plugin install https://github.com/zipstack/helm-values-manager
```

## Quick Start

1. Initialize a new configuration:
```bash
helm values-manager init
```

This creates:
- `values-manager.yaml` configuration file
- `values` directory with environment files (`dev.yaml`, `staging.yaml`, `prod.yaml`)

2. View available commands:
```bash
helm values-manager --help
```

## Development

### Setup Development Environment

1. Clone the repository:
```bash
git clone https://github.com/zipstack/helm-values-manager
cd helm-values-manager
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

### Running Tests

Run tests with tox (will test against multiple Python versions):
```bash
tox
```

Run tests for a specific Python version:
```bash
tox -e py39  # For Python 3.9
```

### Code Quality

This project uses several tools to maintain code quality:

- **pre-commit**: Runs various checks before each commit
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Style guide enforcement

Run all code quality checks manually:
```bash
pre-commit run --all-files
```

## Contributing

🙌 PRs and contributions are welcome! Let's build a better Helm secret & config manager together.

Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to contribute to this project.

## 📌 License

🔓 Open-source under the **MIT License**.

### 🌟 Star this repo if you find it useful! 🌟

[![Star](https://img.shields.io/github/stars/zipstack/helm-values-manager?style=social)](https://github.com/zipstack/helm-values-manager)
