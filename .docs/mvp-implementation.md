# MVP Implementation Guide

## Overview
This document provides guidelines and patterns for implementing the Model-View-Presenter (MVP) architectural pattern in the LOGReporter application. It covers View-Presenter interaction patterns, service integration guidelines, and common pitfalls with their solutions.

## View-Presenter Interaction Patterns

### Signal-Based Communication
Views communicate with Presenters through PyQt signals, which provide a clean decoupling mechanism:

```python
# In View
class NodeTreeView(QTreeWidget):
    item_expanded = pyqtSignal(QTreeWidgetItem)
    node_selected = pyqtSignal(QTreeWidgetItem)

# In Presenter
class NodeTreePresenter(QObject):
    def __init__(self, view, ...):
        super().__init__()
        self.view = view
        # Connect view signals to presenter methods
        self.view.item_expanded.connect(self.handle_item_expanded)
        self.view.node_selected.connect(self.on_node_selected)
```

### Method-Based Updates
Presenters update Views through method calls on view interfaces:

```python
# In Presenter
def populate_node_tree(self):
    self.view.clear()
    # ... populate data ...
    self.view.add_top_level_item(node_item)

# In View
class NodeTreeView(QTreeWidget):
    def add_top_level_item(self, item):
        self.addTopLevelItem(item)
```

### Data Transfer Objects
Use dictionaries or simple data classes for transferring data between View and Presenter:

```python
# In Presenter
def _create_node_item(self, node):
    node_item = QTreeWidgetItem([f"{node.name} ({node.ip_address})"])
    node_item.setData(0, Qt.ItemDataRole.UserRole, {
        "type": "node",
        "node_name": node.name
    })
    return node_item
```

## Service Integration Guidelines

### Dependency Injection
Services should be injected into Presenters through the constructor:

```python
class NodeTreePresenter(QObject):
    def __init__(self, view, node_manager: NodeManager, session_manager: SessionManager,
                 log_writer: LogWriter, command_queue: CommandQueue,
                 fbc_service: FbcCommandService, rpc_service: RpcCommandService,
                 context_menu_service):
        super().__init__()
        self.view = view
        self.node_manager = node_manager
        self.session_manager = session_manager
        self.log_writer = log_writer
        self.command_queue = command_queue
        self.fbc_service = fbc_service
        self.rpc_service = rpc_service
        self.context_menu_service = context_menu_service
```

### Service Orchestration
Presenters should orchestrate calls to multiple services to fulfill a user action:

```python
def process_fieldbus_command(self, token_id, node_name):
    """Process a single fieldbus command."""
    logging.debug(f"Processing Fieldbus command: token_id={token_id}, node_name={node_name}")
    try:
        # Get token first to validate node exists before generating command
        token = self.fbc_service.get_token(node_name, token_id)
        
        # Emit status message before processing
        command = self.fbc_service.generate_fieldbus_command(token_id)
        self.status_message_signal.emit(f"Executing: {command}...", 3000)
        
        # Pass active telnet client for reuse
        telnet_client = getattr(self, 'active_telnet_client', None)
        self.fbc_service.queue_fieldbus_command(node_name, token_id, telnet_client)
        self.command_queue.start_processing()
    except ValueError as e:
        # Handle specific ValueError cases like "Node not found"
        if "not found" in str(e).lower():
            self.status_message_signal.emit(str(e), 3000)
        else:
            self._report_error("Error processing Fieldbus command", e)
    except Exception as e:
        self._report_error("Error processing Fieldbus command", e)
```

### Error Handling
Services should provide meaningful error information to Presenters:

```python
def _report_error(self, message: str, exception: Optional[Exception] = None, duration: int = 5000):
    """
    Report an error to the UI.
    
    Args:
        message: Error message to display
        exception: Optional exception that occurred
        duration: Duration to display the message in milliseconds
    """
    error_msg = f"{message}: {str(exception)}" if exception else message
    logging.error(error_msg)
    self.status_message_signal.emit(error_msg, duration)
```

## Common Pitfalls and Solutions

### 1. Tight Coupling Between View and Presenter

**Pitfall**: Direct access to View components from Presenter
```python
# BAD: Presenter directly accessing View components
def bad_method(self):
    self.view.treeWidget.clear()  # Direct access to UI component
    self.view.treeWidget.addTopLevelItem(item)  # Direct access to UI component
```

**Solution**: Use interface methods in View
```python
# GOOD: Presenter using View interface methods
def good_method(self):
    self.view.clear()  # Interface method
    self.view.add_top_level_item(item)  # Interface method
```

### 2. Business Logic in View

**Pitfall**: View containing business logic or data processing
```python
# BAD: View with business logic
class NodeTreeView(QTreeWidget):
    def process_node_data(self, raw_data):
        # Business logic in View - should be in Model/Service
        processed_data = []
        for item in raw_data:
            if item.is_valid():
                processed_data.append(transform(item))
        return processed_data
```

**Solution**: Move business logic to Model/Service
```python
# GOOD: View without business logic
class NodeTreeView(QTreeWidget):
    def display_nodes(self, processed_nodes):
        # Only display logic, no business logic
        for node in processed_nodes:
            self.addTopLevelItem(self._create_node_item(node))
```

### 3. Presenter with UI Code

**Pitfall**: Presenter containing direct UI manipulation code
```python
# BAD: Presenter with direct UI code
class NodeTreePresenter(QObject):
    def update_node_display(self, node):
        # Direct UI manipulation - should be in View
        item = self.view.find_item_by_name(node.name)
        item.setForeground(0, QBrush(QColor("red")))
        item.setBackground(0, QBrush(QColor("yellow")))
```

**Solution**: Presenter delegates UI updates to View
```python
# GOOD: Presenter delegating to View
class NodeTreePresenter(QObject):
    def update_node_display(self, node):
        # Delegate to View
        self.view.update_node_style(node.name, "error")

# In View
class NodeTreeView(QTreeWidget):
    def update_node_style(self, node_name, style_type):
        item = self.find_item_by_name(node_name)
        if style_type == "error":
            item.setForeground(0, QBrush(QColor("red")))
            item.setBackground(0, QBrush(QColor("yellow")))
```

### 4. Inconsistent State Management

**Pitfall**: State managed in multiple places
```python
# BAD: State scattered across components
class NodeTreePresenter(QObject):
    def __init__(self):
        self.selected_node = None  # State in Presenter
        
class NodeTreeView(QTreeWidget):
    def __init__(self):
        self.current_selection = None  # Duplicate state in View
```

**Solution**: Centralize state in Model
```python
# GOOD: State centralized in Model
class NodeManager:
    def __init__(self):
        self.selected_node = None  # Single source of truth
        
class NodeTreePresenter(QObject):
    def __init__(self, view, node_manager: NodeManager):
        self.view = view
        self.node_manager = node_manager  # Access centralized state
        
class NodeTreeView(QTreeWidget):
    def update_display(self, node_manager):
        # Access state from Model through Presenter
        selected = node_manager.selected_node
```

### 5. Overly Complex Presenters

**Pitfall**: Presenters handling too many responsibilities
```python
# BAD: Presenter with too many responsibilities
class NodeTreePresenter(QObject):
    def handle_everything(self):
        # UI logic
        # Data processing
        # Network communication
        # File I/O
        # Database operations
        pass
```

**Solution**: Apply Single Responsibility Principle
```python
# GOOD: Focused Presenter responsibilities
class NodeTreePresenter(QObject):
    def handle_ui_logic(self):
        # Only UI coordination logic
        pass
        
# Delegate to services for other responsibilities
class FileService:
    def handle_file_operations(self):
        pass
        
class NetworkService:
    def handle_network_communication(self):
        pass
```

## Best Practices

### 1. Clear Interface Contracts
Define clear interfaces between View and Presenter with well-documented methods.

### 2. Consistent Naming Conventions
Use consistent naming for signals, methods, and variables across View-Presenter pairs.

### 3. Testable Design
Ensure Presenters can be easily unit tested with mock Views and Services.

### 4. Event-Driven Updates
Use signals and events for communication rather than direct method calls where possible.

### 5. Minimal View Logic
Keep View components as simple as possible, containing only display and user input handling.

### 6. Presenter as Conductor
Use Presenter as a conductor that orchestrates the interactions between View, Model, and Services.

### 7. Error Propagation
Ensure errors are properly propagated from Services through Presenter to View for user feedback.