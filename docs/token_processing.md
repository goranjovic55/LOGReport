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

## FBC Token Detection

### Overview

The NodeManager.scan_log_files method is responsible for detecting and mapping log files to FBC tokens. Recent improvements have been made to correctly identify all FBC tokens in node-specific directories.

### Key Improvements

#### 1. Token Classification Logic
- For .log files, the method now checks the filename content to determine the token type
- Files with pattern `XXX_FBC.log`, `XXX_RPC.log`, etc. are correctly classified based on the suffix
- This prevents misclassification of FBC files as LOG type

#### 2. Node Name Extraction
- For node-specific files in node directories, the directory name is used as the node name
- This ensures correct mapping of files to nodes regardless of filename prefixes
- Fallback to filename prefix is used only when directory name doesn't match any known node

#### 3. Token ID Extraction
- Improved extraction of token IDs from filenames with multiple underscores
- For files with pattern `XXX_FBC.log`, the token ID is correctly extracted as `XXX`
- Proper normalization of numeric token IDs to 3-digit format for FBC tokens

### Implementation Details

The scan_log_files method processes files in the following way:

1. For .log files:
   - Extract token type from filename pattern (e.g., `162_FBC.log` → FBC)
   - Use directory name as node name when available
   - Extract token ID from the first part of the filename

2. For .fbc, .rpc, .lis files:
   - Use existing directory structure logic
   - Token type is determined by parent directory
   - Node name is extracted from directory name

3. Token matching:
   - First attempts exact token ID match
   - Falls back to substring matching
   - Uses alphanumeric similarity for closest match

### Configuration Requirements

#### Node Configuration (nodes_test.json)

For proper FBC token detection, the node configuration file must include all expected tokens with their correct types. For example, the AP01m node configuration should include:

```json
[
  {
    "name": "AP01m",
    "ip_address": "192.168.0.11",
    "tokens": [
      {
        "token_id": "162",
        "token_type": "FBC",
        "port": 23,
        "protocol": "telnet"
      },
      {
        "token_id": "163",
        "token_type": "FBC",
        "port": 23,
        "protocol": "telnet"
      },
      {
        "token_id": "164",
        "token_type": "FBC",
        "port": 23,
        "protocol": "telnet"
      }
    ]
  }
]
```

Important notes:
- All FBC tokens (162, 163, 164) must be explicitly listed with `token_type` set to "FBC"
- The IP address must match the actual node IP address
- Port and protocol should be set according to the node's configuration
- Missing or incorrectly typed tokens may not be detected properly during scanning

### Example

For the directory structure:
```
test_logs/
└── AP01m/
    ├── 162_FBC.log
    ├── 163_FBC.log
    └── 164_FBC.log
```

All three FBC tokens (162, 163, 164) are correctly detected and mapped to the AP01m node.

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