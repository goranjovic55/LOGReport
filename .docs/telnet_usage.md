# Telnet Client Usage Guide

## Recent Fixes
- Fixed SyntaxError in command processing
- Corrected output redirection (responses now go to terminal instead of files)
- Improved error handling for malformed commands

## Basic Usage
```python
from commander.telnet_client import TelnetClient

client = TelnetClient(host='192.168.1.1', port=23)
response = client.send_command('status')
print(response)
```

## Command Processing
1. Commands are queued for sequential execution
2. Responses are displayed in the terminal
3. Supports both synchronous and asynchronous modes

## Best Practices
- Always validate commands before sending
- Use the command queue for bulk operations
- Handle connection errors gracefully