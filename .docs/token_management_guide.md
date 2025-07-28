# Token Management Guide

This guide provides comprehensive information on managing tokens within the LOGReport system, including configuration, usage, and best practices for both FBC (Fieldbus Command) and RPC (Remote Procedure Call) tokens.

## Token Types

The system supports two primary token types:

### FBC Tokens
- Used for fieldbus commands and operations
- Typically associated with direct hardware communication
- Defined with token_type: "FBC" in configuration
- Common use cases: device status queries, configuration changes, real-time monitoring

### RPC Tokens
- Used for remote procedure calls and service operations
- Enable communication with remote systems and services
- Defined with token_type: "RPC" in configuration
- Common use cases: data retrieval, system commands, service interactions

## Configuration

Tokens are configured in the `nodes.json` file, which defines the node structure and associated tokens. The configuration follows this format:

```json
[
    {
        "name": "AP01m",
        "ip_address": "192.168.1.101",
        "tokens": [
            {
                "token_id": "162",
                "token_type": "FBC",
                "port": 2077,
                "protocol": "telnet"
            },
            {
                "token_id": "164",
                "token_type": "RPC",
                "port": 2077,
                "protocol": "telnet"
            },
            {
                "token_id": "162",
                "token_type": "RPC",
                "port": 2077,
                "protocol": "telnet"
            }
        ]
    }
]
```

### Configuration Best Practices

1. **Consistent Naming**: Use consistent naming conventions for nodes and tokens
2. **Documentation**: Add comments to explain complex configurations
3. **Validation**: Validate JSON syntax before deployment
4. **Backup**: Maintain backups of configuration files
5. **Version Control**: Track configuration changes in version control

## Token Resolution Process

The system implements an enhanced token resolution process with fallback logic to ensure reliable command execution.

### Hybrid Token Resolution

The system supports hybrid token resolution where FBC tokens can be used for RPC commands through a fallback mechanism:

1. When an RPC command is requested, the system first looks for a dedicated RPC token with the matching ID
2. If no RPC token is found, it checks for an FBC token with the same ID
3. If an FBC token is found, it creates a temporary RPC token using the FBC token's IP address and other properties
4. If no matching token is found, a temporary RPC token is created with a default IP address

This fallback mechanism ensures that commands can be executed even when dedicated RPC tokens are not configured.

### Dynamic IP Extraction

The system automatically extracts IP addresses from log directory and filenames using regex pattern matching:

```python
def _scan_for_dynamic_ips(self, log_root: str):
    """
    Scans log directory for IPs using regex pattern and updates token objects
    Pattern: r"(\d{1,3}-\d{1,3}-\d{1,3}-\d{1,3})"
    """
    ip_pattern = r"(\d{1,3}-\d{1,3}-\d{1,3}-\d{1,3})"
    
    # Walk through all directories and files
    for dirpath, _, filenames in os.walk(log_root):
        # Process directory names for IP patterns
        dir_name = os.path.basename(dirpath)
        ip_matches = re.findall(ip_pattern, dir_name)
        if ip_matches:
            # Convert IP format from 192-168-0-11 to 192.168.0.11
            for ip_match in ip_matches:
                formatted_ip = ip_match.replace('-', '.')
                # Update tokens with this IP if they don't already have a valid IP
                self._update_tokens_with_ip(formatted_ip)
        
        # Process filenames for IP patterns
        for filename in filenames:
            ip_matches = re.findall(ip_pattern, filename)
            if ip_matches:
                # Convert IP format from 192-168-0-11 to 192.168.0.11
                for ip_match in ip_matches:
                    formatted_ip = ip_match.replace('-', '.')
                    # Update tokens with this IP if they don't already have a valid IP
                    self._update_tokens_with_ip(formatted_ip)
```

## Token Management Procedures

### Adding New Tokens

To add a new token to a node:

1. Open the `nodes.json` file
2. Locate the node configuration
3. Add a new token object to the tokens array
4. Specify the token_id, token_type, port, and protocol
5. Save the file

Example:
```json
{
    "token_id": "165",
    "token_type": "RPC",
    "port": 2077,
    "protocol": "telnet"
}
```

### Modifying Existing Tokens

To modify an existing token:

1. Open the `nodes.json` file
2. Locate the node and token to modify
3. Update the desired properties (port, protocol, etc.)
4. Save the file

### Removing Tokens

To remove a token:

1. Open the `nodes.json` file
2. Locate the node and token to remove
3. Delete the token object from the tokens array
4. Save the file

## Token Usage Examples

### Command Execution

Executing a command using a token:

```python
# Get token for node AP01m with token ID 162
token = rpc_service.get_token("AP01m", "162")

# Execute command
command = f"print from fbc rupi counters {token.token_id}0000"
telnet_client.send_command(command)
```

### Batch Operations

Processing multiple tokens in a batch:

```python
# Process all FBC tokens in a subgroup
for token in node.tokens.values():
    if token.token_type == "FBC":
        fbc_service.queue_fieldbus_command(node.name, token.token_id)

# Process all RPC tokens in a subgroup
for token in node.tokens.values():
    if token.token_type == "RPC":
        rpc_service.queue_rpc_command(node.name, token.token_id)
```

## Best Practices

### Configuration Management

1. **Use Version Control**: Track all configuration changes in version control
2. **Document Changes**: Maintain a changelog for configuration updates
3. **Test Changes**: Test configuration changes in a development environment first
4. **Backup Regularly**: Regularly backup configuration files

### Token Design

1. **Consistent IDs**: Use consistent token ID formats across nodes
2. **Clear Naming**: Use descriptive names for nodes and tokens
3. **Group Related Tokens**: Group related tokens together in the configuration
4. **Document Purpose**: Add comments explaining the purpose of each token

### Security Considerations

1. **Access Control**: Restrict access to configuration files
2. **Audit Logs**: Maintain audit logs of configuration changes
3. **Secure Protocols**: Use secure communication protocols when possible
4. **Regular Reviews**: Regularly review token configurations for security

## Integration with Other Components

### Commander Window

The Commander window UI displays tokens and allows users to execute commands. The context menu filtering system controls which commands are visible based on node type, section type, and command type.

### Command Queue

The CommandQueue manages the execution of commands using tokens. It ensures commands are processed in sequence and handles error conditions.

### Log Writer

The LogWriter component validates token IP addresses against those extracted from filenames and provides warnings for mismatches.

## Troubleshooting

See the [Troubleshooting Guide](troubleshooting_guide.md) for common issues and solutions related to token management.

## Future Improvements

Planned enhancements to token management include:
- Support for additional token types
- Enhanced validation and error reporting
- Configuration-based priority rules for token resolution
- Improved UI for token management
- Integration with external authentication systems