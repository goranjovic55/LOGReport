# Troubleshooting Guide

This guide provides solutions to common issues related to node resolution and token management in the LOGReport system.

## IP Resolution Issues

### Issue: Token IP Address Not Resolving from Filename

**Symptoms**: The system fails to extract IP address from log filenames like `AP01m_192-168-0-11_162.fbc`.

**Causes**:
- Filename does not match the expected pattern
- IP address format in filename uses different separators
- Log directory structure prevents proper scanning

**Solutions**:
1. Verify the filename follows the pattern: `{node_name}_{ip_address}_{token_id}.{extension}`
2. Ensure IP address uses hyphens as separators (e.g., 192-168-0-11)
3. Check that the log file is in the correct directory structure
4. Verify the NodeManager is scanning the correct log root directory

**Example**:
```
# Correct format
AP01m_192-168-0-11_162.fbc
AP01m_192-168-0-11_163.rpc

# Incorrect formats
AP01m_192.168.0.11_162.fbc  # Uses dots instead of hyphens
192-168-0-11_AP01m_162.fbc  # Wrong order
AP01m_192-168-0-11.fbc      # Missing token ID
```

### Issue: IP Address Mismatch Between Configuration and Filename

**Symptoms**: Warning messages about IP address mismatches between `nodes.json` configuration and extracted filename IP.

**Causes**:
- Configuration file has incorrect IP address
- Log file moved from original location
- Multiple log files with different IPs for same token

**Solutions**:
1. Update the IP address in `nodes.json` to match the actual IP
2. Verify the log file is from the correct node
3. Use the filename IP as the authoritative source when there's a conflict
4. Check for duplicate token configurations

**Configuration Example**:
```json
{
    "name": "AP01m",
    "ip_address": "192.168.0.11",  // Should match filename IP
    "tokens": [
        {
            "token_id": "162",
            "token_type": "FBC",
            "port": 2077,
            "protocol": "telnet"
        }
    ]
}
```

### Issue: Dynamic IP Extraction Not Working

**Symptoms**: IP addresses are not being extracted from directories or filenames.

**Causes**:
- Incorrect regex pattern in NodeManager
- Directory scanning not properly configured
- File permissions preventing directory access

**Solutions**:
1. Verify the regex pattern in `NodeManager._scan_for_dynamic_ips()`:
   ```python
   ip_pattern = r"(\d{1,3}-\d{1,3}-\d{1,3}-\d{1,3})"
   ```
2. Check that the log root directory is correctly specified
3. Verify file system permissions allow directory traversal
4. Enable debug logging to trace the scanning process

## Token Management Issues

### Issue: RPC Command Fails with "Token Not Found"

**Symptoms**: RPC commands fail with "Token not found" error even when token exists.

**Causes**:
- Token type mismatch (FBC token used for RPC command)
- Token ID format mismatch
- Node configuration not loaded

**Solutions**:
1. Verify the token exists with the correct type in `nodes.json`:
   ```json
   {
       "token_id": "162",
       "token_type": "RPC",  // Must be "RPC" for RPC commands
       "port": 2077,
       "protocol": "telnet"
   }
   ```
2. Check that both FBC and RPC tokens are configured for the same ID when needed
3. Verify the node configuration is properly loaded
4. Use the hybrid token resolution fallback by ensuring an FBC token exists with the same ID

### Issue: Hybrid Token Resolution Not Working

**Symptoms**: FBC tokens are not being used as fallback for RPC commands.

**Causes**:
- RpcCommandService.get_token() method not properly implemented
- Token ID formats don't match between FBC and RPC tokens
- NodeManager not properly updating token objects

**Solutions**:
1. Verify the RpcCommandService.get_token() implementation includes fallback logic:
   ```python
   # First try RPC token
   if rpc_token := node.tokens.get(token_id):
       if rpc_token.token_type == "RPC":
           return rpc_token
   
   # Fallback to FBC token
   if fbc_token := node.tokens.get(token_id):
       if fbc_token.token_type == "FBC":
           return NodeToken(
               token_id=fbc_token.token_id,
               token_type="RPC",
               name=fbc_token.name,
               ip_address=fbc_token.ip_address,
               port=fbc_token.port,
               protocol=fbc_token.protocol
           )
   ```
2. Ensure token IDs are consistent between FBC and RPC tokens
3. Verify the NodeManager is properly loading all tokens

### Issue: Temporary Tokens Being Created Unnecessarily

**Symptoms**: System creates temporary tokens with IP address 0.0.0.0.

**Causes**:
- Token not defined in configuration
- Typo in token ID
- Node name mismatch

**Solutions**:
1. Add the missing token to `nodes.json`
2. Verify token IDs match exactly (including case)
3. Check that node names in commands match configuration
4. Use dynamic IP extraction to ensure proper token resolution

## Connection Issues

### Issue: Connection Refused for Valid Tokens

**Symptoms**: Valid tokens fail to establish connections.

**Causes**:
- Incorrect port number in configuration
- Firewall blocking the port
- Target service not running

**Solutions**:
1. Verify port numbers in `nodes.json` match the target service
2. Check firewall settings on both client and server
3. Verify the target service is running and accepting connections
4. Test connectivity using external tools like telnet or ping

### Issue: Intermittent Connection Failures

**Symptoms**: Commands work sometimes but fail at other times.

**Causes**:
- Network instability
- Target service restarts
- Connection timeout settings too aggressive

**Solutions**:
1. Implement retry logic with exponential backoff
2. Increase connection timeout values
3. Monitor network stability
4. Check target service logs for restart patterns

## Debugging Tips

### Enable Debug Logging

Add debug statements to trace the resolution process:

```python
def _scan_for_dynamic_ips(self, log_root: str):
    print(f"[DEBUG] Scanning for dynamic IPs in: {log_root}")
    
    for dirpath, _, filenames in os.walk(log_root):
        dir_name = os.path.basename(dirpath)
        ip_matches = re.findall(ip_pattern, dir_name)
        if ip_matches:
            for ip_match in ip_matches:
                formatted_ip = ip_match.replace('-', '.')
                print(f"[DEBUG] Found IP in directory name: {ip_match} -> {formatted_ip}")
```

### Verify Token Resolution

Test token resolution with known values:

```python
# Test token lookup
token = rpc_service.get_token("AP01m", "162")
print(f"Resolved token: {token.token_id}, IP: {token.ip_address}, Type: {token.token_type}")
```

### Check Configuration Loading

Verify the node configuration is properly loaded:

```python
# List all loaded nodes and tokens
for node_name, node in node_manager.nodes.items():
    print(f"Node: {node_name}")
    for token_id, token in node.tokens.items():
        print(f"  Token: {token_id}, Type: {token.token_type}, IP: {token.ip_address}")
```

## Common Error Messages

| Error Message | Likely Cause | Solution |
|-------------|------------|----------|
| "Node {node_name} not found" | Node not in configuration | Add node to nodes.json |
| "Token not found for ID {token_id}" | Token ID mismatch or missing | Verify token ID and type in configuration |
| "IP address mismatch" | Config IP doesn't match filename IP | Update configuration or use filename IP |
| "Connection refused" | Port blocked or service down | Check firewall and service status |
| "Temporary token created" | Token not configured | Add proper token configuration |

## Prevention Best Practices

1. **Consistent Naming**: Use consistent naming conventions for nodes, tokens, and files
2. **Configuration Validation**: Validate `nodes.json` before deployment
3. **Regular Testing**: Test token resolution with new log files
4. **Documentation**: Maintain up-to-date documentation of token configurations
5. **Monitoring**: Implement monitoring for connection failures and resolution issues