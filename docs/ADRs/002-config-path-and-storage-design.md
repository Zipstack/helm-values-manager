# ADR 002: Config Path and Storage Design

## Status
Accepted

## Context
When implementing the Helm Values Manager, we identified several key design considerations:

1. Users need to define configuration structure (paths, descriptions, requirements) independently of setting values
2. As a CLI plugin, each command is executed independently, requiring consistent file operations
3. The initial design included a PlainText backend which added unnecessary complexity
4. Path lookups and validations needed optimization for better performance

## Decision

### 1. Separate Config Definition from Values
- Allow users to define configuration paths and metadata without setting values
- Support metadata like description, required flag, and sensitivity flag
- Enable validation of structure before any values are set

### 2. Standardized Command Pattern
- Implement a BaseCommand class for consistent file operations
- Include file locking to prevent concurrent modifications
- Add automatic backup before writes
- Handle common error scenarios uniformly

```python
class BaseCommand:
    def execute(self):
        try:
            config = self.load_config()
            result = self.run(config)
            self.save_config(config)
            return result
        except Exception as e:
            # Handle errors, cleanup
            raise
```

### 3. Simplified Storage Design
- Remove PlainTextBackend
- Store local values directly in HelmValuesConfig
- Use specialized backends (AWS, Azure) only for remote storage
- Maintain clear separation between local and remote storage

### 4. Optimized Path Management
- Implement a path map for O(1) lookups
- Validate path uniqueness during definition
- Store local values with efficient key structure
- Separate path definition from value storage

```python
class HelmValuesConfig:
    def __init__(self):
        self._path_map = {}      # Fast path lookups
        self._local_values = {}  # Local value storage
```

## Consequences

### Positive
1. **Better User Experience**
   - Clear separation between structure definition and value setting
   - Improved validation capabilities
   - More intuitive configuration management

2. **Improved Performance**
   - O(1) path lookups
   - Reduced complexity in local storage
   - More efficient validation

3. **Enhanced Maintainability**
   - Consistent command pattern
   - Clear separation of concerns
   - Simplified storage architecture

4. **Better Safety**
   - Built-in file locking
   - Automatic backups
   - Strict path validation

### Negative
1. **Additional Complexity**
   - New base command pattern to learn
   - More sophisticated path management

## Implementation Notes

1. **Command Implementation**
```python
class SetValueCommand(BaseCommand):
    def run(self, config):
        config.set_value(self.path, self.env, self.value)
```

2. **Path Definition**
```python
config.add_config_path(
    path="app.replicas",
    description="Number of application replicas",
    required=True
)
```

3. **Value Storage**
```python
# Local storage
config.set_value("app.replicas", "dev", "3")

# Remote storage (AWS/Azure)
config.set_value("app.secrets.key", "prod", "secret-value")
```
