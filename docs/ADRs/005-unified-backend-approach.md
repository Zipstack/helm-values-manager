# ADR-005: Unified Backend Approach for Value Storage

## Status
Proposed

## Context
Currently, the Value class handles two distinct storage types: local and remote. This creates a split in logic within the Value class, requiring different code paths and validation rules based on the storage type. This complexity makes the code harder to maintain and test.

## Decision
We will remove the storage_type distinction from the Value class and implement a SimpleValueBackend for non-sensitive data (previously handled as "local" storage). This means:

1. Value class will:
   - Only interact with backends through a unified interface
   - Not need to know about storage types
   - Have simpler logic and better separation of concerns

2. Storage backends will:
   - Include a new SimpleValueBackend for non-sensitive data
   - All implement the same ValueBackend interface
   - Be responsible for their specific storage mechanisms

3. Configuration will:
   - Use SimpleValueBackend internally for non-sensitive values
   - Use secure backends (AWS/Azure) for sensitive values
   - Backend selection handled by the system based on value sensitivity

## Consequences

### Positive
1. **Cleaner Value Class**
   - Removes storage type logic
   - Single consistent interface for all operations
   - Better separation of concerns

2. **Unified Testing**
   - All storage types tested through the same interface
   - No need for separate local/remote test cases
   - Easier to mock and verify behavior

3. **More Flexible**
   - Easy to add new backend types
   - Consistent interface for all storage types
   - Clear extension points

4. **Better Security Model**
   - Storage backend choice driven by data sensitivity
   - Clear separation between sensitive and non-sensitive data
   - Explicit in configuration

### Negative
1. **Slight Performance Impact**
   - Additional method calls for simple value operations
   - Extra object creation for SimpleValueBackend

### Neutral
1. **Configuration Changes**
   - Backend selection based on value sensitivity
   - Transparent to end users

## Implementation Plan

1. **Backend Development**
   ```python
   class SimpleValueBackend(ValueBackend):
       def __init__(self):
           self._values = {}

       def get_value(self, path: str, environment: str) -> str:
           key = self._make_key(path, environment)
           return self._values[key]

       def set_value(self, path: str, environment: str, value: str) -> None:
           key = self._make_key(path, environment)
           self._values[key] = value
   ```

2. **Value Class Simplification**
   ```python
   @dataclass
   class Value:
       path: str
       environment: str
       _backend: ValueBackend

       def get(self) -> str:
           return self._backend.get_value(self.path, self.environment)

       def set(self, value: str) -> None:
           if not isinstance(value, str):
               raise ValueError("Value must be a string")
           self._backend.set_value(self.path, self.environment, value)
   ```

3. **Configuration Example**
   ```json
   {
     "version": "1.0",
     "release": "my-app",
     "deployments": {
       "prod": {
         "backend": "aws",
         "auth": {
           "type": "managed_identity"
         },
         "backend_config": {
           "region": "us-west-2"
         }
       }
     },
     "config": [
       {
         "path": "app.replicas",
         "description": "Number of application replicas",
         "required": true,
         "sensitive": false,
         "values": {
           "dev": "3",
           "prod": "5"
         }
       },
       {
         "path": "app.secretKey",
         "description": "Application secret key",
         "required": true,
         "sensitive": true,
         "values": {
           "dev": "dev-key-123",
           "prod": "prod-key-456"
         }
       }
     ]
   }
   ```

   The system will automatically:
   - Use SimpleValueBackend for non-sensitive values (app.replicas)
   - Use configured secure backend for sensitive values (app.secretKey)
