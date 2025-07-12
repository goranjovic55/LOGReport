# Signal Implementation Guidelines

## Standardized Patterns
1. **Base Class Pattern**: 
   - Create a base `ObservableModel` class that inherits from `QObject`
   - Declare common signals like `updated` in the base class
   - All model classes should inherit from `ObservableModel` instead of `QObject` directly

2. **Signal Declaration**:
   ```python
   class ObservableModel(QObject):
       updated = pyqtSignal()  # For general model updates
       data_changed = pyqtSignal(object)  # For specific data changes
   ```

3. **Signal Emission**:
   - Emit signals after completing state changes
   - Avoid emitting signals from constructors
   - Use descriptive signal names that indicate what changed

## Class Interface Documentation
- Document all signals in class docstrings:
  ```python
  class NodeManager(ObservableModel):
      """
      Manages node configurations and emits signals on changes.
      
      Signals:
          updated: Emitted when nodes or tokens are modified
          connection_changed: Emitted when node connection status changes
      """
  ```

- Document signal parameters:
  ```python
  class SessionManager(ObservableModel):
      """
      Manages telnet sessions.
      
      Signals:
          session_started(node: Node): Emitted when session starts
          session_ended(node: Node, reason: str): Emitted when session ends
      """
  ```

## Code Review Checklist
1. **Signal Implementation**:
   - [ ] Does the class inherit from QObject or ObservableModel?
   - [ ] Are signals declared at class level (not in __init__)?
   - [ ] Are signals properly documented in class docstring?

2. **Signal Usage**:
   - [ ] Are signals emitted after state changes (not during)?
   - [ ] Are there any missed signal emissions for state changes?
   - [ ] Are signal connections properly disconnected when objects are destroyed?

3. **Thread Safety**:
   - [ ] Are signals emitted from worker threads using `QMetaObject.invokeMethod`?
   - [ ] Are signal handlers thread-safe?

## Best Practices
1. **Avoid Signal Proliferation**: Prefer generic `updated` signals over highly specific ones
2. **Decoupled Architecture**: 
   - Models should emit signals but not know about their consumers
   - Views should connect to model signals but not modify models directly
3. **Testing**:
   - Unit tests should verify signal emissions
   - Use `QSignalSpy` to test signal emissions in Qt tests

## Example Implementation
```python
from PyQt6.QtCore import QObject, pyqtSignal

class ObservableModel(QObject):
    """Base class for observable models"""
    updated = pyqtSignal()  # Generic update signal
    error_occurred = pyqtSignal(str)  # Error notification signal

class NodeManager(ObservableModel):
    """Manages node configurations"""
    def __init__(self):
        super().__init__()
        self.nodes = {}
        
    def add_node(self, node):
        self.nodes[node.name] = node
        self.updated.emit()  # Notify of changes