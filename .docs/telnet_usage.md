# Telnet Client Usage Guide

## NetworkSession Pattern
- Base class for all network operations
- Provides standardized interface for command execution
- Implements robust connection management with retry logic
- Centralized error handling for all network operations
- Enforces consistent logging and monitoring

## TelnetOperations
- Consolidated module for all Telnet functionality
- Implements connection health checks and automatic recovery
- Standardized prompt pattern matching across all sessions
- Unified response parsing and filtering
- Centralized configuration for timeouts and retries

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