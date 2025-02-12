# Code Structure

This document outlines the organization and structure of the Helm Values Manager codebase.

## Package Organization

```
helm_values_manager/
├── models/              # Core data models
│   ├── __init__.py
│   └── value.py        # Value class for configuration management
├── backends/           # Storage backend implementations
│   ├── __init__.py
│   ├── base.py        # Abstract base class for backends
│   ├── aws.py         # AWS Secrets Manager backend
│   └── azure.py       # Azure Key Vault backend
└── cli.py             # CLI implementation
```

## Core Components

### Models Package

The `models` package contains the core data structures used throughout the application.

#### Value Class
The `Value` class is a fundamental component that handles configuration values:

```python
class Value:
    """
    Represents a configuration value with storage strategy.

    Attributes:
        path (str): Configuration path (e.g., "app.replicas")
        environment (str): Environment name (e.g., "dev", "prod")
        storage_type (str): Type of storage ("local" or "remote")
    """
```

**Key Features:**
- Dual storage support (local/remote)
- Serialization capabilities
- Input validation
- Error handling

For implementation details, see the [Value Class Implementation Guide](value-class.md).

### Backends Package

The `backends` package provides storage implementations for different providers:

- `base.py`: Abstract base class defining the backend interface
- `aws.py`: AWS Secrets Manager implementation
- `azure.py`: Azure Key Vault implementation

Each backend must implement:
```python
class ValueBackend(ABC):
    @abstractmethod
    def get_value(self, key: str) -> str:
        """Get a value from storage."""
        pass

    @abstractmethod
    def set_value(self, key: str, value: str) -> None:
        """Set a value in storage."""
        pass
```

## Design Principles

1. **Clean Architecture**
   - Clear separation of concerns
   - Dependency inversion for backends
   - Model independence from storage

2. **Error Handling**
   - Custom exceptions for domain errors
   - Comprehensive error messages
   - Graceful error recovery

3. **Security**
   - Secure value storage
   - Input validation
   - No sensitive data logging

4. **Testing**
   - Unit tests for all components
   - Integration tests for backends
   - High code coverage requirement

## Further Reading

- [Architecture Overview](architecture.md)
- [Testing Guide](testing.md)
- [Security Guidelines](security.md)
