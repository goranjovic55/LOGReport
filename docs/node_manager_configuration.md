# NodeManager Configuration Documentation

## Overview

The NodeManager is responsible for loading, parsing, and managing node configuration for the LOGReport Commander application. This document provides comprehensive documentation on configuration handling, format support, and best practices.

## Configuration File Structure

### Supported Formats

The NodeManager supports two configuration formats:

#### 1. New Format (Recommended)

```json
[
  {
    "name": "TEST_NODE",
    "ip_address": "192.168.1.1",
    "tokens": [
      {
        "token_id": "162",
        "token_type": "FBC",
        "ip_address": "192.168.1.1",
        "port": 23,
        "protocol": "telnet"
      },
      {
        "token_id": "abc123",
        "token_type": "RPC",
        "ip_address": "192.168.1.1",
        "port": 23,
        "protocol": "telnet"
      }
    ]
  }
]
```

#### 2. Old Format (Automatically Converted)

```json
[
  {
    "name": "TEST_NODE",
    "ip": "192.168.1.1",
    "tokens": ["162", "163", "164"],
    "types": ["FBC", "FBC", "FBC"]
  }
]
```

### Configuration Schema

#### Node Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique node identifier |
| `ip_address` | string | Yes | Node IP address |
| `tokens` | array | Yes | Array of token objects |

#### Token Object

| Field | Type | Required | Description | Default |
|-------|------|----------|-------------|---------|
| `token_id` | string | Yes | Unique token identifier | - |
| `token_type` | string | Yes | Token type (FBC, RPC, LOG, LIS) | - |
| `ip_address` | string | No | Token-specific IP address | Node IP |
| `port` | integer | Yes | Connection port | - |
| `protocol` | string | No | Connection protocol | "telnet" |

## Configuration Loading

### Basic Usage

```python
from src.commander.node_manager import NodeManager

# Create NodeManager instance
nm = NodeManager()

# Load configuration (uses default path)
nm.load_configuration()

# Load from custom path
nm.load_configuration("custom_config.json")

# Check if loading succeeded
if nm.get_all_nodes():
    print(f"Loaded {len(nm.get_all_nodes())} nodes")
else:
    print("No nodes loaded or configuration error")
```

### Configuration Validation

The NodeManager performs comprehensive validation:

#### File Validation
- File existence check
- File size limit (10MB maximum)
- Read permissions verification
- JSON format validation

#### Structure Validation
- Root element must be an array
- Each node must have required fields
- Token array must be properly formatted
- Port numbers must be valid (1-65535)

#### Data Validation
- Node names must be non-empty strings
- IP addresses must be valid strings
- Token IDs must be non-empty after normalization
- Token types must be valid strings

## Error Handling

### Common Error Scenarios

#### 1. File Not Found
```python
try:
    nm.load_configuration("nonexistent.json")
except FileNotFoundError:
    print("Configuration file not found")
```

#### 2. Invalid JSON Format
```python
try:
    nm.load_configuration("invalid.json")
except json.JSONDecodeError:
    print("Invalid JSON format")
```

#### 3. Missing Required Fields
```python
# Invalid configuration (missing ip_address)
invalid_config = [
    {
        "name": "TEST_NODE",
        "tokens": []
    }
]
# Will be logged as skipped node
```

#### 4. Invalid Port Numbers
```python
# Invalid configuration (port out of range)
invalid_config = [
    {
        "name": "TEST_NODE",
        "ip_address": "192.168.1.1",
        "tokens": [
            {
                "token_id": "162",
                "token_type": "FBC",
                "port": 70000  # Invalid port
            }
        ]
    }
]
# Token will be skipped with error message
```

### Error Logging

The NodeManager provides detailed logging:

```python
import logging

# Configure logging to see detailed messages
logging.basicConfig(level=logging.INFO)

# Load configuration with detailed logging
nm = NodeManager()
```

Log messages include:
- Configuration file loading status
- Format detection and conversion
- Node processing statistics
- Token validation results
- Error details with context

## Token Normalization

### Normalization Rules

The NodeManager applies token normalization consistently:

#### FBC Tokens
- Numeric tokens: Pad to 3 digits (e.g., "1" → "001")
- Alphanumeric tokens: Convert to uppercase (e.g., "abc" → "ABC")

#### RPC Tokens
- Convert to lowercase
- Remove non-alphanumeric characters

#### LOG/LIS Tokens
- Convert to lowercase
- Remove non-alphanumeric characters

### Usage Example

```python
from src.commander.node_manager import NodeManager

nm = NodeManager()
nm.load_configuration("nodes.json")

# Access normalized tokens
node = nm.get_node("TEST_NODE")
if node:
    for token in node.tokens.values():
        print(f"Original: {token.token_id}, Type: {token.token_type}")
```

## Configuration Management

### Creating Configuration Files

#### Programmatic Creation

```python
from src.commander.node_manager import NodeManager

# Create empty configuration
nm = NodeManager()
nm.create_empty_config("new_config.json")

# Add nodes programmatically
nm.add_node({
    "name": "NEW_NODE",
    "ip_address": "192.168.1.100",
    "tokens": [
        {
            "token_id": "001",
            "token_type": "FBC",
            "port": 23
        }
    ]
})

# Save configuration
nm.save_configuration("new_config.json")
```

#### Manual Creation

Create a JSON file with the new format structure:

```json
[
  {
    "name": "MANUAL_NODE",
    "ip_address": "192.168.1.50",
    "tokens": [
      {
        "token_id": "001",
        "token_type": "FBC",
        "port": 23,
        "protocol": "telnet"
      },
      {
        "token_id": "rpc001",
        "token_type": "RPC",
        "port": 23,
        "protocol": "telnet"
      }
    ]
  }
]
```

### Configuration Migration

#### Old to New Format Conversion

The NodeManager automatically detects and converts old format configurations:

```python
# Old format configuration
old_config = [
    {
        "name": "LEGACY_NODE",
        "ip": "192.168.1.10",
        "tokens": ["162", "163", "abc"],
        "types": ["FBC", "FBC", "RPC"]
    }
]

# NodeManager will automatically convert to new format
nm = NodeManager()
nm.load_configuration("legacy_config.json")  # Will be converted
```

### Configuration Validation Script

```python
import json
from src.commander.node_manager import NodeManager

def validate_config(file_path):
    """Validate configuration file and report issues"""
    nm = NodeManager()
    
    print(f"Validating configuration: {file_path}")
    
    if nm.load_configuration(file_path):
        nodes = nm.get_all_nodes()
        print(f"✅ Configuration loaded successfully")
        print(f"📊 Loaded {len(nodes)} nodes")
        
        for node in nodes:
            print(f"🔹 Node: {node.name} ({len(node.tokens)} tokens)")
            for token in node.tokens.values():
                print(f"  - Token: {token.token_id} ({token.token_type})")
        
        return True
    else:
        print("❌ Configuration validation failed")
        return False

# Usage
validate_config("nodes.json")
```

## Best Practices

### Configuration File Organization

1. **Use Version Control**: Keep configuration files in version control
2. **Environment Separation**: Use different files for development, testing, and production
3. **Backup Configuration**: Regular backups of configuration files
4. **Documentation**: Document configuration changes and their impact

### Configuration Structure

1. **Consistent Naming**: Use consistent node and token naming conventions
2. **Logical Grouping**: Group related nodes together
3. **Documentation**: Add comments for complex configurations
4. **Validation**: Always validate configuration files before deployment

### Performance Considerations

1. **File Size**: Keep configuration files under 10MB
2. **Token Count**: Limit tokens per node for better performance
3. **Caching**: Utilize built-in token normalization caching
4. **Logging**: Configure appropriate logging levels for production

## Troubleshooting

### Common Issues

#### 1. Configuration Not Loading

**Symptoms**: `load_configuration()` returns `False`

**Solutions**:
- Check file path and existence
- Verify JSON format validity
- Check file permissions
- Review error logs for specific issues

#### 2. Tokens Not Appearing

**Symptoms**: Nodes load but tokens are missing

**Solutions**:
- Verify token object structure
- Check required fields (token_id, token_type, port)
- Validate token ID normalization
- Review error logs for token processing issues

#### 3. Circular Import Errors

**Symptoms**: Import errors when using NodeManager

**Solutions**:
- Ensure proper import order
- Use relative imports correctly
- Check for circular dependencies

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Create NodeManager with debug output
nm = NodeManager()
```

### Configuration Testing

```python
def test_configuration(file_path):
    """Test configuration file and provide detailed feedback"""
    nm = NodeManager()
    
    print(f"Testing configuration: {file_path}")
    
    # Test loading
    if not nm.load_configuration(file_path):
        print("❌ Failed to load configuration")
        return False
    
    # Test node access
    nodes = nm.get_all_nodes()
    print(f"✅ Loaded {len(nodes)} nodes")
    
    # Test token access
    total_tokens = sum(len(node.tokens) for node in nodes)
    print(f"✅ Loaded {total_tokens} tokens")
    
    # Test node selection
    if nodes:
        first_node = nodes[0]
        nm.set_selected_node(first_node.name)
        selected = nm.get_selected_node()
        print(f"✅ Node selection works: {selected.name}")
    
    return True

# Usage
test_configuration("nodes.json")
```

## API Reference

### NodeManager Class

#### Constructor

```python
NodeManager()
```

Creates a new NodeManager instance with default configuration.

#### Methods

##### `load_configuration(file_path: str = None) -> bool`

Load configuration from JSON file.

**Parameters**:
- `file_path` (str, optional): Path to configuration file

**Returns**:
- `bool`: True if successful, False otherwise

##### `save_configuration(file_path: str = None) -> bool`

Save current configuration to JSON file.

**Parameters**:
- `file_path` (str, optional): Path to save configuration file

**Returns**:
- `bool`: True if successful, False otherwise

##### `get_node(node_name: str) -> Optional[Node]`

Get node by name.

**Parameters**:
- `node_name` (str): Node name to retrieve

**Returns**:
- `Node`: Node object if found, None otherwise

##### `get_all_nodes() -> List[Node]`

Get all loaded nodes.

**Returns**:
- `List[Node]`: List of all node objects

##### `add_node(node_data: dict) -> None`

Add a new node programmatically.

**Parameters**:
- `node_data` (dict): Node configuration data

##### `set_selected_node(node_name: str) -> None`

Set the currently selected node.

**Parameters**:
- `node_name` (str): Name of node to select

##### `get_selected_node() -> Optional[Node]`

Get the currently selected node.

**Returns**:
- `Node`: Selected node object or None

## Version History

- **v1.0.0**: Basic configuration loading
- **v1.1.0**: Added format conversion support
- **v1.2.0**: Enhanced validation and error handling
- **v1.3.0**: Added token normalization integration
- **v1.4.0**: Improved logging and statistics
- **v1.5.0**: Added configuration validation and migration tools

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review error logs for detailed information
3. Validate configuration files using the provided tools
4. Test with minimal configuration to isolate issues