# Contributing to Helm Values Manager

We love your input! We want to make contributing to Helm Values Manager as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

Before starting work:
1. Check if a GitHub issue exists for your feature/bug
   - If not, create a new issue using the appropriate template:
     - Bug Report: For reporting bugs
     - Feature Request: For proposing new features
     - Documentation: For documentation improvements
   - If yes, comment on the issue to let others know you're working on it

For contributors with write access:
1. Create a new branch from `main` using the issue number (see Branch Naming below)
2. Make your changes following our development guidelines
3. Create a pull request

For contributors without write access:
1. Fork the repository
2. Create a new branch in your fork
   - We recommend creating a branch even in your fork to:
     - Keep your fork's main branch clean and in sync with upstream
     - Work on multiple issues simultaneously
     - Make PR feedback changes easier
3. Make your changes in the branch
4. Create a pull request from your fork's branch to our main repository

For all contributors:
1. If you've added code that should be tested, add tests
2. If you've changed APIs, update the documentation
3. Ensure the test suite passes
4. Make sure your code passes all code quality checks

## Version Control Guidelines

### Branch Naming Convention

All branches should follow this naming convention:

```
<issue-number>-<short-description>
```

For example:
- `123-add-aws-secrets-backend`
- `456-fix-path-validation`
- `789-update-documentation`

Note: This naming convention is required for branches in the main repository. When working in your own fork, we recommend:
1. Creating a dedicated branch for each issue (don't work in main)
2. Following the same naming convention for consistency
3. Keeping your fork's main branch clean for easy upstream syncing

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification with issue number references:

```
<type>[optional scope]: #<issue-number> <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

Examples:
```
feat: #123 add AWS Secrets backend
fix: #456 handle empty paths correctly
docs: #789 update installation guide
test: #234 add integration tests for Value class
```

For multiple issues, include all issue numbers:
```
fix: #111 #222 resolve path handling edge cases
```

Note:
- Always include the issue number with a `#` prefix
- Place the issue number before the description
- Multiple issues should be space-separated
- The description should still be clear without the issue number

## Important Documentation

Before contributing, please review these important documents:

1. [Code Structure](docs/Development/code-structure.md) - Understanding the codebase organization
2. [Testing Guide](docs/Development/testing.md) - Testing standards and practices
3. [Architecture Overview](docs/Design/low-level-design.md) - System architecture and design decisions
4. [ADRs](docs/ADRs/) - Architecture Decision Records

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

#### Required Extensions

When contributing to documentation, please note that we use the following extensions:

- **Mermaid**: For creating diagrams and visualizations in markdown. All architecture and flow diagrams should be written using Mermaid.
  ```mermaid
  graph TD
    A[Process Start] --> B[Process End]
  ```

To preview Mermaid diagrams locally, you can:
- Use VS Code with the "Markdown Preview Mermaid Support" extension
- Use any Markdown editor that supports Mermaid rendering
- Preview on GitHub, which has native Mermaid support

## Pull Request Process

1. Update the README.md with details of changes to the interface, if applicable.
2. Update the documentation with any new features or changes.
3. The PR may be merged once you have the sign-off of at least one maintainer.

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the same [MIT License](./LICENSE) that covers the project. Feel free to contact the maintainers if that's a concern.

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

By contributing, you agree that your contributions will be licensed under its [MIT License](./LICENSE).
