# ADR 004: Value Resolution Strategy

## Status
Accepted

## Context
In ADR 003, we identified a potential issue with value resolution in our unified storage design:
- Need to check value types before resolving
- More complex serialization/deserialization
- Less explicit about value storage strategy

## Decision

### 1. Introduce Value Class
Instead of storing raw values or backend instances, we'll introduce a `Value` class to encapsulate the resolution logic:

```python
class Value:
    def __init__(self, path: str, environment: str,
                 storage_type: str = "local",
                 backend: Optional[ValueBackend] = None):
        self.path = path
        self.environment = environment
        self.storage_type = storage_type
        self._backend = backend
        self._value: Optional[str] = None

    def get(self) -> str:
        """Get the resolved value"""
        if self.storage_type == "local":
            return self._value
        return self._backend.get_value(
            self._generate_key(self.path, self.environment)
        )

    def set(self, value: str) -> None:
        """Set the value"""
        if self.storage_type == "local":
            self._value = value
        else:
            self._backend.set_value(
                self._generate_key(self.path, self.environment),
                value
            )

    def to_dict(self) -> dict:
        """Serialize for storage"""
        return {
            "storage_type": self.storage_type,
            "value": self._value if self.storage_type == "local" else None
        }

    @classmethod
    def from_dict(cls, data: dict, path: str,
                 environment: str, backend: Optional[ValueBackend] = None) -> 'Value':
        """Deserialize from storage"""
        value = cls(path, environment, data["storage_type"], backend)
        if data["storage_type"] == "local":
            value._value = data["value"]
        return value
```

### 2. Updated Path Map Structure

```python
_path_map = {
    "app.replicas": {
        "metadata": {
            "description": "Number of replicas",
            "required": True,
            "sensitive": False
        },
        "values": {
            "dev": Value(path="app.replicas", environment="dev", storage_type="local"),
            "prod": Value(path="app.replicas", environment="prod",
                         storage_type="aws", backend=aws_backend)
        }
    }
}
```

### 3. Simplified Value Operations

```python
class HelmValuesConfig:
    def set_value(self, path: str, environment: str, value: str) -> None:
        if path not in self._path_map:
            raise PathNotFoundError(f"Path not defined: {path}")

        deployment = self._get_deployment(environment)
        values = self._path_map[path]["values"]

        if environment not in values:
            # Create new Value instance
            backend = self._create_backend(deployment) if deployment.backend != "local" else None
            values[environment] = Value(
                path=path,
                environment=environment,
                storage_type=deployment.backend,
                backend=backend
            )

        values[environment].set(value)

    def get_value(self, path: str, environment: str) -> str:
        if path not in self._path_map:
            raise PathNotFoundError(f"Path not defined: {path}")

        values = self._path_map[path]["values"]
        if environment not in values:
            raise ValueError(f"No value set for {path} in {environment}")

        return values[environment].get()
```

## Consequences

### Positive
1. **Cleaner Value Resolution**
   - No type checking needed
   - Value resolution logic encapsulated in one place
   - Clear separation of concerns

2. **Better Serialization**
   - Explicit serialization/deserialization methods
   - Clear structure for stored data
   - Easy to extend for new storage types

3. **Improved Type Safety**
   - Strong typing for values
   - Compiler/type checker can catch errors
   - Better IDE support

4. **More Maintainable**
   - Value-related logic isolated
   - Easier to add new storage types
   - Clearer code intent

### Negative
1. **Additional Class**
   - One more class to maintain
   - Slightly more complex object model
   - Minor memory overhead

## Implementation Notes

1. **Creating Values**
```python
# Local value
value = Value(path="app.replicas", environment="dev", storage_type="local")
value.set("3")

# Remote value
value = Value(path="app.secrets.key", environment="prod",
              storage_type="aws", backend=aws_backend)
value.set("secret-value")
```

2. **Serialization Example**
```python
# To JSON
config_json = {
    "app.replicas": {
        "metadata": {...},
        "values": {
            "dev": {
                "storage_type": "local",
                "value": "3"
            },
            "prod": {
                "storage_type": "aws",
                "value": None  # Remote values not serialized
            }
        }
    }
}
```
