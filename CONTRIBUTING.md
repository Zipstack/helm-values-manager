# Contributing to Helm Values Manager

We love your input! We want to make contributing to Helm Values Manager as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code passes all code quality checks.
6. Issue that pull request!

## Development Setup

1. Clone your fork:
```bash
git clone https://github.com/YOUR-USERNAME/helm-values-manager
cd helm-values-manager
```

2. Create a virtual environment:
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

## Code Quality Standards

We use several tools to maintain code quality:

### Pre-commit Hooks

We use pre-commit to run various checks before each commit. The hooks include:

- Code formatting with `black`
- Import sorting with `isort`
- Style guide enforcement with `flake8`
- YAML validation
- Check for large files
- Debug statement checks
- Case conflict checks
- Trailing whitespace removal
- End of file fixes

To run all checks manually:
```bash
pre-commit run --all-files
```

### Testing

We use `pytest` for testing and `tox` for testing against multiple Python versions.

Run all tests:
```bash
tox
```

Run tests for a specific Python version:
```bash
tox -e py39  # For Python 3.9
```

### Documentation

- Use docstrings for all public modules, functions, classes, and methods
- Follow Google style for docstrings
- Keep the README.md and other documentation up to date

## Pull Request Process

1. Update the README.md with details of changes to the interface, if applicable.
2. Update the documentation with any new features or changes.
3. The PR may be merged once you have the sign-off of at least one maintainer.

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the same [MIT License](LICENSE) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using GitHub's [issue tracker](https://github.com/zipstack/helm-values-manager/issues)

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/zipstack/helm-values-manager/issues/new).

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## License

By contributing, you agree that your contributions will be licensed under its MIT License.
