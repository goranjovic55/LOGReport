# SequentialCommandProcessor Documentation

## Overview

The `SequentialCommandProcessor` is a core component of the Commander application responsible for handling memory-optimized, mode-adaptive iterative processing of FBC/RPC subclass group commands. It ensures sequential execution of commands with proper resource management, progress tracking, and error handling.

The processor is designed to handle large batches of commands efficiently while maintaining system stability through careful resource management and memory optimization techniques.

## Key Features

- **Sequential Processing**: Ensures commands are executed one at a time in the correct order
- **Memory Optimization**: Implements garbage collection and resource cleanup to minimize memory footprint
- **Mode-Adaptive Workflow**: Adapts processing behavior based on command type (FBC/RPC)
- **Resource Management**: Efficiently manages telnet connections and system resources
- **Progress Tracking**: Provides real-time progress updates during command execution
- **Error Handling**: Comprehensive error handling with timeout management
- **Thread Safety**: Implements thread-safe operations for concurrent access

## Memory Optimization Techniques

The SequentialCommandProcessor implements several memory optimization strategies:

1. **Periodic Garbage Collection**: Automatically triggers garbage collection every 10 commands to free up memory
2. **Resource Cleanup**: Properly disposes of telnet clients and other resources after processing
3. **Qt Event Processing**: Regularly processes Qt events to prevent UI freezing during long operations
4. **Token List Management**: Clears token lists after processing to free memory
5. **Timer Management**: Properly stops and cleans up timers used for command waiting

## Mode-Adaptive Iterative Workflow

The processor adapts its behavior based on the command type:

### FBC Commands
- Generates fieldbus commands using the pattern: `print from fbc io structure {token}0000`
- Processes tokens with type "FBC"

### RPC Commands
- Generates RPC commands with configurable actions (print/clear)
- Default action is "print" with command pattern: `print from fbc rupi counters {token}0000`
- Alternative action is "clear" with command pattern: `clear fbc rupi counters {token}0000`
- Processes tokens with type "RPC"

## Resource Management Strategies

1. **Telnet Client Reuse**: Reuses existing telnet connections when available to minimize connection overhead
2. **Connection Management**: Properly manages telnet session connections through the SessionManager
3. **Timeout Handling**: Implements 30-second timeout for command execution with automatic recovery
4. **Thread Pool Management**: Uses a single-threaded thread pool to ensure sequential execution

## Error Handling and Progress Tracking

### Error Handling
- Comprehensive exception handling for all command processing operations
- Timeout detection with automatic recovery (30-second timeout)
- Connection error handling with detailed logging
- Graceful degradation when individual commands fail

### Progress Tracking
- Real-time progress updates through Qt signals
- Status messages for UI feedback
- Completion reporting with success/failure statistics
- Progress percentage calculation for user feedback

## Usage Instructions

### Initialization
The SequentialCommandProcessor requires several dependencies to be initialized:

```python
from src.commander.services.sequential_command_processor import SequentialCommandProcessor

processor = SequentialCommandProcessor(
    command_queue=command_queue,
    fbc_service=fbc_service,
    rpc_service=rpc_service,
    session_manager=session_manager
)
```

### Processing FBC Commands
To process a list of FBC tokens:

```python
processor.process_fbc_commands(
    node_name="NODE_NAME",
    tokens=fbc_tokens_list,
    telnet_client=optional_telnet_client
)
```

### Processing RPC Commands
To process a list of RPC tokens:

```python
processor.process_rpc_commands(
    node_name="NODE_NAME",
    tokens=rpc_tokens_list,
    action="print",  # or "clear"
    telnet_client=optional_telnet_client
)
```

### Stopping Processing
To stop command processing:

```python
processor.stop_processing()
```

## API Documentation

### Class: SequentialCommandProcessor

#### Constructor
```python
SequentialCommandProcessor(command_queue, fbc_service, rpc_service, session_manager, parent=None)
```

**Parameters:**
- `command_queue` (CommandQueue): Queue for command execution
- `fbc_service` (FbcCommandService): Service for FBC command operations
- `rpc_service` (RpcCommandService): Service for RPC command operations
- `session_manager` (SessionManager): Manager for session operations
- `parent` (QObject, optional): Parent QObject

#### Methods

##### `process_fbc_commands(node_name, tokens, telnet_client=None)`
Process FBC commands sequentially with resource management.

**Parameters:**
- `node_name` (str): Name of the node containing the tokens
- `tokens` (List[NodeToken]): List of FBC tokens to process
- `telnet_client` (object, optional): Optional telnet client to reuse

##### `process_rpc_commands(node_name, tokens, action="print", telnet_client=None)`
Process RPC commands sequentially with resource management.

**Parameters:**
- `node_name` (str): Name of the node containing the tokens
- `tokens` (List[NodeToken]): List of RPC tokens to process
- `action` (str): Action to perform ("print" or "clear")
- `telnet_client` (object, optional): Optional telnet client to reuse

##### `stop_processing()`
Stop processing commands and clear the command queue.

#### Signals

##### `status_message`
Emitted when a status message should be displayed.

**Parameters:**
- `message` (str): Status message
- `duration` (int): Duration to display message in milliseconds

##### `progress_updated`
Emitted when progress is updated.

**Parameters:**
- `current` (int): Number of completed commands
- `total` (int): Total number of commands

##### `processing_finished`
Emitted when processing is finished.

**Parameters:**
- `success_count` (int): Number of successful commands
- `total_count` (int): Total number of commands

## Examples

### Example 1: Processing FBC Commands for a Node

```python
# Get node and its FBC tokens
node = node_manager.get_node("AP01m")
fbc_tokens = [t for t in node.tokens.values() if t.token_type == "FBC"]

# Process all FBC tokens sequentially
processor.process_fbc_commands(
    node_name="AP01m",
    tokens=fbc_tokens
)
```

### Example 2: Processing RPC Commands with Clear Action

```python
# Get node and its RPC tokens
node = node_manager.get_node("AP01m")
rpc_tokens = [t for t in node.tokens.values() if t.token_type == "RPC"]

# Process all RPC tokens with clear action
processor.process_rpc_commands(
    node_name="AP01m",
    tokens=rpc_tokens,
    action="clear"
)
```

### Example 3: Processing with Reused Telnet Connection

```python
# Reuse an existing telnet connection for efficiency
telnet_client = session_manager.get_debugger_session()

# Process commands using the existing connection
processor.process_fbc_commands(
    node_name="AP01m",
    tokens=fbc_tokens,
    telnet_client=telnet_client
)
```

## Integration with Other Components

The SequentialCommandProcessor integrates with several other components in the system:

1. **CommandQueue**: Manages the execution queue for commands
2. **FbcCommandService**: Handles FBC command generation and queuing
3. **RpcCommandService**: Handles RPC command generation and queuing
4. **SessionManager**: Manages telnet sessions and connections
5. **NodeTreePresenter**: Initiates batch processing operations

## Performance Considerations

1. **Memory Usage**: The processor is optimized to minimize memory usage during large batch operations
2. **Connection Efficiency**: Reusing telnet connections reduces connection overhead
3. **UI Responsiveness**: Regular Qt event processing prevents UI freezing
4. **Error Recovery**: Automatic timeout handling prevents hanging operations

## Best Practices

1. **Resource Management**: Always ensure proper cleanup by calling `stop_processing()` when needed
2. **Connection Reuse**: Reuse telnet connections when processing multiple command batches
3. **Error Handling**: Implement proper error handling in calling code to handle processing failures
4. **Progress Monitoring**: Connect to progress signals to provide user feedback during long operations