# ADR-006: Helm-Style Logging System

## Status
Accepted

## Context
As a Helm plugin, our application needs to follow Helm's logging conventions for consistency and user experience. Key considerations include:

1. Debug output control via environment variables
2. Error message formatting
3. Performance in logging operations
4. Integration with Helm's output conventions
5. Testing and verification of log output

## Decision

### 1. Implement HelmLogger Class
Create a dedicated logger class that follows Helm plugin conventions:

```python
class HelmLogger:
    @staticmethod
    def debug(msg: str, *args: Any) -> None:
        if os.environ.get('HELM_DEBUG'):
            if args:
                msg = msg % args
            print("[debug] %s" % msg, file=sys.stderr)

    @staticmethod
    def error(msg: str, *args: Any) -> None:
        if args:
            msg = msg % args
        print("Error: %s" % msg, file=sys.stderr)

    @staticmethod
    def warning(msg: str, *args: Any) -> None:
        if args:
            msg = msg % args
        print("Warning: %s" % msg, file=sys.stderr)
```

### 2. Key Design Decisions

1. **Helm Convention Compliance**
   - Use stderr for all output
   - Prefix debug messages with "[debug]"
   - Prefix error messages with "Error:"
   - Prefix warning messages with "Warning:"
   - Control debug output via HELM_DEBUG environment variable

2. **Performance Optimization**
   - Use string formatting instead of f-strings for consistent behavior
   - Lazy evaluation of debug messages
   - No string concatenation in critical paths

3. **Global Instance Pattern**
   - Provide a global logger instance
   - Enable consistent logging across the codebase
   - Avoid passing logger instances

4. **Testing Support**
   - Mockable stderr for testing
   - Environment variable control in tests
   - String format verification

### 3. Usage Pattern
```python
from helm_values_manager.utils.logger import logger

def some_function():
    logger.debug("Processing %s", value)
    try:
        # do something
        logger.debug("Success!")
    except Exception as e:
        logger.error("Failed: %s", str(e))
    logger.warning("Something unexpected happened")
```

## Consequences

### Positive
1. **Consistent User Experience**
   - Matches Helm's output format
   - Familiar debug control mechanism
   - Clear error messages

2. **Performance**
   - Efficient string formatting
   - Debug messages skipped when disabled
   - Minimal memory overhead

3. **Maintainability**
   - Centralized logging logic
   - Easy to modify output format
   - Simple testing approach

4. **Debugging**
   - Clear debug output control
   - Consistent message format
   - Environment-based control

### Negative
1. **Limited Flexibility**
   - Fixed output format
   - Limited log levels (debug/warning/error)
   - No log file support

2. **Global State**
   - Global logger instance
   - Potential for test interference
   - Need careful test isolation

## Implementation Notes

1. **Testing**
```python
def test_debug_output():
    stderr = StringIO()
    with mock.patch.dict(os.environ, {'HELM_DEBUG': '1'}), \
         mock.patch('helm_values_manager.utils.logger.sys.stderr', stderr):
        logger.debug("Test message")
        assert stderr.getvalue() == "[debug] Test message\n"

def test_warning_output():
    stderr = StringIO()
    with mock.patch('helm_values_manager.utils.logger.sys.stderr', stderr):
        logger.warning("Test warning")
        assert stderr.getvalue() == "Warning: Test warning\n"
```

2. **Integration**
```python
# In PathData class
def validate(self):
    logger.debug("Validating PathData for path: %s", self.path)
    if not self.is_valid():
        logger.error("Invalid PathData: %s", self.path)
    logger.warning("PathData validation completed with warnings")
```
