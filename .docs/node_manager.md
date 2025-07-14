# Node Manager Documentation

## Core Responsibilities
- Manages node configurations from JSON files
- Scans and organizes log files
- Tracks node status (online/offline)
- Provides node data to other components

## Key Implementation Details

### Configuration Loading
```python
def load_configuration(self):
    """Loads node config from JSON file"""
    try:
        with open(self.config_path) as f:
            data = json.load(f)
            self.nodes = [Node(**node_data) for node_data in data['nodes']]
        return True
    except Exception as e:
        logging.error(f"Config load failed: {str(e)}")
        return False
```

### Log File Scanning
```python
def scan_log_files(self):
    """Finds all log files matching patterns"""
    for node in self.nodes:
        # Scan FBC logs
        fbc_dir = os.path.join(self.log_root, 'FBC', node.name)
        for f in glob.glob(f"{node.name}_*.fbc", root_dir=fbc_dir):
            token = self._extract_fbc_token(f)
            node.add_token('FBC', token)
```

## Usage Examples

### Getting Node Information
```python
# Get node by name
node = node_manager.get_node('AP01m')

# Get all nodes 
all_nodes = node_manager.get_all_nodes()

# Check node status
if node.status == 'online':
    print(f"{node.name} is available")
```

### Adding a New Node Programmatically
```python
new_node = Node(name='NEW_NODE', ip_address='192.168.1.100')
new_node.add_token('FBC', '12345')
node_manager.add_node(new_node)
```

## Common Patterns

### Finding Log Files for a Node
```python
def get_log_files(node_name, log_type):
    """Returns all log files for a node of given type"""
    log_dir = os.path.join(node_manager.log_root, log_type, node_name)
    return glob.glob(os.path.join(log_dir, f"{node_name}_*.*"))
```

### Handling New Log Types
1. Add new token pattern in `_extract_token_id()`
2. Update `scan_log_files()` to handle new directory structure
3. Add new constants for file extensions

## Error Handling
The manager provides these validation methods:
- `validate_node_config()` - Checks config integrity
- `validate_log_paths()` - Verifies log directories exist
- `check_node_connectivity()` - Tests node availability