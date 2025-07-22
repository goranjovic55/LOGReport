# Command Services Documentation

## Service Architecture

### CommandService (Base Class)
- Abstract base class for all command services
- Defines common interface for command queuing and execution
- Standardizes error handling and response processing
- Provides dependency injection for command queue and log writer

### FBC Command Service
```python
class FbcCommandService(CommandService):
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
class RpcCommandService(CommandService):
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

### Standardized Error Handling
```python
# Base CommandService error handling
def execute_command(self, command, node_name, token_id):
    try:
        response = self.telnet_session.send_command(command)
        if "ERROR" in response:
            self.handle_error(response, node_name, token_id)
            return None
        return response
    except ConnectionError as e:
        self.logger.error(f"Connection failed for {node_name}: {e}")
        self.reconnect()
        raise
    except TimeoutError as e:
        self.logger.error(f"Command timeout for {node_name}: {e}")
        self.handle_timeout(command, node_name)
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