# Command Services Documentation

## Core Implementation

### FBC Command Service
```python
class FbcCommandService:
    def queue_fieldbus_command(self, node_name, token_id):
        """Queues FBC command for execution"""
        command = f"print from fbc io structure {token_id}0000"
        self.command_queue.add_command(command, node_name, token_id)
        
    def handle_response(self, response):
        """Processes FBC command response"""
        if "ERROR" in response:
            self.report_error(response)
        else:
            self.log_writer.append_to_log(response)
```

### RPC Command Service  
```python
class RpcCommandService:
    def queue_rpc_command(self, node_name, token_id, action):
        """Queues RPC print/clear command"""
        if action == "print":
            cmd = f"print from fbc rupi counters {token_id}0000"
        else:
            cmd = f"clear fbc rupi counters {token_id}0000"
        self.command_queue.add_command(cmd, node_name, token_id)
```

## Usage Examples

### Executing FBC Command
```python
# From CommanderWindow context menu
fbc_service.queue_fieldbus_command("AP01m", "12345")

# Manually via queue
command_queue.add_command(
    "print from fbc io structure 123450000",
    node="AP01m",
    token="12345"
)
```

### Handling Command Results
```python
# Example response handler
def on_command_complete(response):
    if "structure" in response:
        parse_fieldbus_structure(response)
    elif "counters" in response:
        parse_rupi_counters(response)
```

## Common Patterns

### Adding New Command Type
1. Create new CommandService subclass
2. Implement command formatting
3. Add response handling
4. Register with CommanderWindow

### Error Handling Flow
```python
try:
    response = telnet_session.send_command(cmd)
    if "ERROR" in response:
        raise CommandError(response)
    return response
except SocketError as e:
    self.reconnect()
    raise
```

## Integration Points

### With CommanderWindow
- Updates status bar messages
- Provides context menu actions
- Manages command input/output

### With LogWriter
- Appends all successful command outputs
- Includes metadata in log entries
- Handles log file rotation