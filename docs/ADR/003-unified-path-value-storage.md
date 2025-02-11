# ADR 003: Unified Path and Value Storage

## Status
Accepted

## Context
In our previous design (ADR 002), we had two separate dictionaries in `HelmValuesConfig`:
1. `_path_map` for storing path metadata and validation
2. `_local_values` for storing local values

This separation added unnecessary complexity and potential for inconsistency.

## Decision

### 1. Unified Storage Structure
We will use a single dictionary with a nested structure:

```python
_path_map = {
    "app.replicas": {  # path
        "metadata": {
            "description": "Number of replicas",
            "required": True,
            "sensitive": False
        },
        "values": {
            "dev": "3",  # local value
            "prod": ValueBackend  # remote value
        }
    }
}
```

### 2. Value Resolution Strategy
- Local values are stored directly in the values dict
- Remote values are represented by their respective backend instances
- The get_value method will automatically resolve the appropriate storage

```python
def get_value(self, path: str, environment: str) -> str:
    if path not in self._path_map:
        raise PathNotFoundError(f"Path not defined: {path}")

    env_values = self._path_map[path]["values"]
    if environment not in env_values:
        raise ValueError(f"No value set for {path} in {environment}")

    value = env_values[environment]
    if isinstance(value, ValueBackend):
        return value.get_value(self._generate_key(path, environment))
    return value
```

## Consequences

### Positive
1. **Simplified Data Structure**
   - Single source of truth for paths and values
   - Clearer relationship between paths and their values
   - More intuitive code organization

2. **Better Performance**
   - Single lookup for both metadata and values
   - Reduced memory usage
   - Simpler caching if needed

3. **Improved Maintainability**
   - Less code to maintain
   - Fewer potential points of failure
   - Easier to understand and debug

### Negative
1. **More Complex Value Resolution**
   - Need to check value type before resolving
   - Slightly more complex serialization/deserialization

## Implementation Notes

1. **Path Definition**
```python
config.add_config_path(
    path="app.replicas",
    description="Number of replicas",
    required=True
)
```

2. **Value Setting**
```python
# Setting local value
config.set_value("app.replicas", "dev", "3")

# Setting remote value (automatically creates backend)
config.set_value("app.secrets.key", "prod", "secret-value")
```

3. **Serialization**
```python
def to_dict(self) -> dict:
    result = {}
    for path, data in self._path_map.items():
        result[path] = {
            "metadata": data["metadata"],
            "values": {
                env: value if not isinstance(value, ValueBackend) else None
                for env, value in data["values"].items()
            }
        }
    return result
```
