# Testing Guide

This document outlines the testing standards and practices for the Helm Values Manager project.

## Test Organization

```
tests/
├── unit/                # Unit tests
│   ├── models/         # Tests for core models
│   │   └── test_value.py
│   └── backends/       # Tests for backend implementations
├── integration/        # Integration tests
│   └── backends/      # Backend integration tests
└── conftest.py        # Shared test fixtures
```

## Test Categories

### Unit Tests

Unit tests focus on testing individual components in isolation. They should:
- Test a single unit of functionality
- Mock external dependencies
- Be fast and independent
- Cover both success and error cases

Example from `test_value.py`:
```python
def test_value_init_local():
    """Test Value initialization with local storage."""
    value = Value(path="app.replicas", environment="dev")
    assert value.path == "app.replicas"
    assert value.environment == "dev"
    assert value.storage_type == "local"
```

### Integration Tests

Integration tests verify component interactions, especially with external services:
- Test actual backend implementations
- Verify configuration loading
- Test end-to-end workflows

## Testing Standards

### 1. Test Organization
- Group related tests in classes
- Use descriptive test names
- Follow the file structure of the implementation
- Keep test files focused and manageable

### 2. Test Coverage
- Aim for 100% code coverage
- Test all code paths
- Include edge cases
- Test error conditions

### 3. Test Quality
- Follow Arrange-Act-Assert pattern
- Keep tests independent
- Use appropriate assertions
- Write clear test descriptions

Example:
```python
def test_set_invalid_type():
    """Test setting a non-string value."""
    value = Value(path="app.replicas", environment="dev")
    with pytest.raises(ValueError, match="Value must be a string"):
        value.set(3)
```

### 4. Fixtures and Mocks
- Use fixtures for common setup
- Mock external dependencies
- Keep mocks simple and focused
- Use appropriate scoping

Example:
```python
@pytest.fixture
def mock_backend():
    """Create a mock backend for testing."""
    backend = Mock(spec=ValueBackend)
    backend.get_value.return_value = "mock_value"
    return backend
```

## Running Tests

### Local Development
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/unit/models/test_value.py

# Run with coverage
python -m pytest --cov=helm_values_manager
```

### Using Tox
```bash
# Run tests in all environments
tox

# Run for specific Python version
tox -e py39
```

## Test Documentation

Each test should have:
1. Clear docstring explaining purpose
2. Well-structured setup and teardown
3. Clear assertions with messages
4. Proper error case handling

Example:
```python
def test_from_dict_missing_path():
    """Test deserializing with missing path field."""
    data = {
        "environment": "dev",
        "storage_type": "local",
        "value": "3"
    }
    with pytest.raises(ValueError, match="Missing required field: path"):
        Value.from_dict(data)
```

## Best Practices

1. **Test Independence**
   - Each test should run in isolation
   - Clean up after tests
   - Don't rely on test execution order

2. **Test Readability**
   - Use clear, descriptive names
   - Document test purpose
   - Keep tests simple and focused

3. **Test Maintenance**
   - Update tests when implementation changes
   - Remove obsolete tests
   - Keep test code as clean as production code

4. **Performance**
   - Keep unit tests fast
   - Use appropriate fixtures
   - Mock expensive operations

## Continuous Integration

Our CI pipeline:
- Runs all tests
- Checks code coverage
- Enforces style guidelines
- Runs security checks

## Further Reading

- [Code Structure](code-structure.md)
- [Contributing Guide](../../CONTRIBUTING.md)
- [Pre-commit Hooks](pre-commit-hooks.md)
