# Project Standards (v2.0)

## Python Guidelines
- PEP 8 compliance
- Type hints required for all public methods
- Google-style docstrings
- Logger usage instead of print() statements
- Unit tests for critical functionality
- Function length under 30 lines where possible

## Configuration Handling
- **JSON format** for all complex configurations
- Consistent naming: `lowercase_with_underscores`
- JSON Schema validation for configuration files
- Programmatic configuration generation preferred
- Versioned configuration formats

### Example Configuration
```json
[
  {
    "name": "node_name",
    "tokens": ["t1", "t2"],
    "types": ["FBC", "RPC"]
  }
]
```

## Error Handling
```python
class AppError(Exception):
    """Base exception for application errors"""
    pass

def process_file(path: str) -> dict:
    try:
        # Core logic
    except (FileNotFoundError, UnicodeDecodeError) as e:
        logger.error(f"Processing failed: {str(e)}")
        raise AppError(
            f"Error processing {path}"
        ) from e
```

## Best Practices
1. **GUI Design**
   - Consistent dark/light theme support
   - Responsive layouts with spacings
   - Clear visual hierarchy
   - Dedicated dialogs for complex operations

2. **Tool Integration**
   - Atomic operations
   - Path abstraction for cross-platform
   - Error reporting to GUI
   - Progress feedback during long operations

3. **Code Structure**
   - Modular design
   - Single responsibility principle
   - Explicit imports
   - Dependency inversion

## File Organization
```
_PROJECT/
├── _BMPRSS/
│   ├── _BLUEPRINT/
│   ├── _CODE/
│   ├── _STANDARD/
│   └── ... 
└── _DIA/ (Generated directories)
    ├── FBC/
    ├── RPC/
    ├── LOG/
    └── LIS/
```

## Update Protocol
1. Increment version number in standards file
2. Update all blueprint documentation
3. Run smoke tests after significant changes
4. Document changes in DEV_ROADMAP.md
