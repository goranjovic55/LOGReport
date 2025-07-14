# Quick Start Guide

## First-Time Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Prepare configuration
cp nodes_test.json nodes.json
nano nodes.json  # Edit with your nodes

# 3. Set up log directory structure
mkdir -p logs/{FBC,RPC,LOG}/{node1,node2}  # Replace with your node names
```

## Running the Application
```bash
# Standard run
python -m src.main

# With debug logging
python -m src.main --log-level DEBUG
```

## Example Workflows

### Viewing Node Logs
1. Click "Load Nodes" and select your nodes.json
2. Click "Set Log Root" and select your logs directory
3. Expand nodes in tree view to see available logs
4. Double-click any log file to open it

### Executing Commands
```python
# Example: Print FBC structure via API
from commander.services import FbcCommandService
service = FbcCommandService()
service.queue_fieldbus_command("AP01m", "12345")
```

## Configuration Examples

### nodes.json
```json
{
  "nodes": [
    {
      "name": "AP01m",
      "ip_address": "192.168.1.10",
      "tokens": {
        "FBC": ["123", "456"],
        "RPC": ["789"] 
      }
    }
  ]
}
```

## Troubleshooting

### Common Issues
- **Logs not appearing**: 
  - Verify files match naming patterns (e.g., AP01m_192-168-1-10_123.fbc)
  - Check log root directory structure matches node names
- **Connection failures**:
  - Verify IP/port in telnet connection bar
  - Check node status in configuration

### Debugging Tips
```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test node manager directly
from commander.node_manager import NodeManager
nm = NodeManager()
nm.load_configuration()
print(nm.get_all_nodes())