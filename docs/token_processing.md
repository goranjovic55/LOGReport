# Sequential Token Processing Implementation

## Overview

This document describes the implementation of sequential token processing for FBC/RPC services in the LOGReporter application. The implementation ensures that tokens are processed one at a time with proper completion-based chaining and safety mechanisms.

## Key Features

### 1. Sequential Processing
- Tokens are processed one at a time in the order they appear
- Each token is queued only after the previous one completes
- Completion-based chaining ensures proper sequencing
- Direct callback mechanism for immediate next token processing

### 2. Safety Mechanisms
- **Circuit Breaker**: Stops processing after 3 consecutive failures
- **Timeouts**: Overall processing timeout to prevent indefinite execution
- **Resource Management**: Proper cleanup of resources between tokens

### 3. Error Handling
- Individual token failures don't halt the entire batch
- Detailed error tracking and reporting
- Isolated logging for each token
- Circuit breaker integration with failure tracking

## Implementation Details

### SequentialCommandProcessor Class

The `SequentialCommandProcessor` class manages sequential execution of tokens with isolated logging and error handling. Key methods include:

#### process_tokens_sequentially()
Main entry point for sequential token processing:
- Initializes processing state and creates unique batch ID
- Sets up batch logging with token count
- Prepares each token with isolated logging context
- Normalizes tokens according to protocol-specific rules
- Adds commands to queue for sequential execution
- Uses direct callbacks for immediate next token processing

#### _on_command_completed()
Callback method triggered when a command completes:
- Updates processing statistics (success/failure counts)
- Releases telnet client resources
- Writes token-specific results to log
- Closes token-specific log file
- Checks for batch completion and emits final signals
- Performs batch logging finalization

#### _prepare_token_context()
Creates isolated context for each token:
- Normalizes token ID based on protocol
- Validates node IP address
- Opens token-specific log file
- Writes standardized metadata header to log

#### _release_telnet_client()
Releases telnet client resources:
- Safely closes telnet connections
- Handles exceptions during cleanup
- Resets client reference to prevent reuse

#### process_sequential_batch()
Processes subgroup tokens with circuit breaker:
- Uses consecutive failure tracking (3 failures trigger circuit breaker)
- Per-command timeout handling
- Isolated logging per token
- Periodic resource cleanup

### Safety Mechanisms

#### Circuit Breaker
- **Only activated in `process_sequential_batch` method**
- Triggers after 3 consecutive command failures
- Stops further processing in the current batch
- Requires manual reset before new operations

#### Timeouts
- Per-command timeout tracking
- Overall processing timeout based on token count
- Configurable timeout values
- Graceful termination on timeout

#### Resource Management
- Telnet client cleanup after each token
- Qt event processing to prevent UI freezing
- Garbage collection for memory optimization
- Batch logging resource management

### Batch Logging System
- Unique batch ID generated for each operation
- Centralized batch log with summary statistics
- Token-specific logs with standardized headers
- Metadata includes:
  - Token ID
  - Node name
  - Timestamp
  - Protocol
  - Batch ID

## Usage Examples

### Processing FBC Tokens with Error Handling
```python
processor = SequentialCommandProcessor(command_queue, fbc_service, rpc_service, session_manager, logging_service)
tokens = [NodeToken(token_id="162", token_type="FBC"), NodeToken(token_id="163", token_type="FBC")]
try:
    processor.process_fbc_commands("AP01m", tokens)
except Exception as e:
    logger.error(f"Processing failed: {str(e)}")
```

### Processing Mixed Tokens with Normalization
```python
processor = SequentialCommandProcessor(command_queue, fbc_service, rpc_service, session_manager, logging_service)
tokens = [
    NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),
    NodeToken(token_id="163a", token_type="RPC", node_ip="192.168.0.11")
]
processor.process_tokens_sequentially("AP01m", tokens, action="print")
```

### Subgroup Processing with Circuit Breaker
```python
processor = SequentialCommandProcessor(command_queue, fbc_service, rpc_service, session_manager, logging_service)
tokens = [NodeToken(token_id="163", token_type="RPC"), NodeToken(token_id="164", token_type="RPC")]
results = processor.process_sequential_batch(
    tokens, 
    "FBC", 
    {"node_name": "AP01m", "command": "print"}
)
for result in results:
    if not result.success:
        logger.warning(f"Token {result.token} failed: {result.error}")
```

## Backward Compatibility

The implementation maintains backward compatibility with existing interfaces:
- All existing method signatures are preserved
- Command queue interface remains unchanged
- Signal emissions follow existing patterns
- No breaking changes to public API

## Testing

Unit tests verify:
- Single token processing
- Multiple token processing with partial failures
- Circuit breaker activation
- Timeout handling
- Resource cleanup
- Progress tracking
- Completion-based chaining

## Performance Considerations

- Minimal memory footprint through proper resource management
- Efficient event processing to prevent UI freezing
- Optimized logging with batch operations
- Direct callback mechanism for reduced latency
