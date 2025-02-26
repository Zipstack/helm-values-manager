# 8. Remove Command Registry Pattern

Date: 2025-02-26

## Status

Accepted

## Context

We initially implemented a Command Registry pattern to manage and discover commands in our Helm plugin. The registry was designed to:
- Register commands with unique names
- Retrieve command instances by name
- Potentially support future features like plugins, middleware, and dynamic command loading

However, our current implementation shows that:
1. Commands are statically defined in CLI functions using Typer
2. Each CLI function directly knows which command to instantiate
3. We don't have requirements for:
   - Plugin system or third-party extensions
   - Dynamic command loading/discovery
   - Command aliasing or middleware
   - Runtime command configuration

The registry adds an unnecessary layer of indirection:
```python
# Current approach with registry
registry = CommandRegistry()
registry.register("init", InitCommand)
command = registry.get_command("init")()

# Simplified to
command = InitCommand()
```

## Decision

We will remove the Command Registry pattern and use direct command instantiation because:
1. It simplifies the code by removing unnecessary abstraction
2. It follows YAGNI (You Ain't Gonna Need It) principle
3. Our commands are fixed and well-defined as part of the Helm plugin
4. Typer handles CLI command registration and discovery
5. We don't have current or planned requirements that would benefit from a registry

## Consequences

### Positive
1. Simpler, more maintainable code
2. Less indirection and complexity
3. Easier to understand command flow
4. Reduced testing surface
5. Better alignment with Typer's design

### Negative
1. If we need these features in the future, we'll need to:
   - Reimplement the registry pattern
   - Update all command instantiation points
   - Add command discovery mechanism

### Neutral
1. Command implementation and interface remain unchanged
2. CLI functionality remains the same
3. User experience is unaffected

## Future Considerations

If we need registry features in the future, we should consider:
1. Plugin system requirements
2. Command discovery needs
3. Middleware requirements
4. Integration with Helm plugin system

## Related
- [ADR-001] Initial Architecture Decision
