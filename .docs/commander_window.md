# Commander Window Documentation

## Overview
The main GUI interface built with PyQt6 that manages nodes and log files.

## Key Components
1. **Node Tree (Left Panel)**
   - Displays hierarchical view of nodes and their log files
   - Implemented in `QTreeWidget` with custom items
   - Source: [`src/commander/commander_window.py`](src/commander/commander_window.py:684)

2. **Session Tabs (Right Panel)**
   - Telnet, VNC, FTP tabs for different protocols
   - Each tab has output area and connection controls
   - Source: [`src/commander/commander_window.py`](src/commander/commander_window.py:616)

## Code Examples

### Adding a Node to Tree
```python
def _create_node_item(self, node):
    node_item = QTreeWidgetItem([f"{node.name} ({node.ip_address})"])
    node_item.setIcon(0, get_node_online_icon() if node.status == "online"
                     else get_node_offline_icon())
    node_item.setData(0, Qt.ItemDataRole.UserRole, {
        "type": "node",
        "node_name": node.name
    })
    return node_item
```

### Handling Node Expansion
```python 
def _handle_item_expanded(self, item):
    data = item.data(0, Qt.ItemDataRole.UserRole)
    if data and data.get("type") == "node":
        self._load_node_children(item)  # Loads FBC/RPC/LOG sections
```

## Usage Examples

### Connecting to Telnet
1. Select a node with FBC tokens
2. Right-click → "Print FieldBus Structure"
3. View output in Telnet tab

### Viewing Logs
1. Expand node → LOG section
2. Double-click any log file to open in system viewer

## Common Workflows

### Adding New Node Type
1. Update `NodeManager` to support new type
2. Add new section handler in `_load_node_children()`
3. Create corresponding service class if needed

### Adding New Command Type
1. Create new `CommandService` subclass
2. Add to commander window initialization
3. Update context menu handlers