# Logging Architecture

## Overview
The logging system in LOGReport handles creation, management, and writing of log files for different protocol types (FBC, RPC, LOG, LIS). It ensures proper separation and organization of logs while maintaining performance through efficient file handle management.

## Log Key Structure
The LogWriter uses composite keys in the format `(token_id, protocol)` where:
- `token_id`: Numeric identifier from node configuration
- `protocol`: Lowercase string ("fbc", "rpc", etc.)

This prevents log file conflicts when multiple protocols share the same token ID.

## Key Components

### LogWriter
Primary class responsible for:
- Creating and managing log file handles
- Writing command outputs to appropriate logs
- Maintaining open file handles for performance
- Handling file rotation and cleanup

### LoggingService
Orchestrates the logging process:
- Coordinates between command execution and log writing
- Manages log lifecycle events
- Handles error conditions in logging

### FbcCommandService / RpcCommandService
Protocol-specific services that:
- Generate appropriate commands for their protocol
- Interface with LogWriter for log management
- Handle protocol-specific formatting and processing

## Log File Organization

### Directory Structure
- FBC logs: `{log_root}/FBC/{node}/`
- RPC logs: `{log_root}/RPC/{node}/`
- LOG files: `{log_root}/{node}/`

### File Naming Convention
- FBC: `{node}_{ip}_{token}.fbc`
- RPC: `{node}_{ip}_{token}.rpc`
- LOG: `{node}_{timestamp}_LOG.log`
- LIS: `{node}_{timestamp}_LIS.lis`

## Composite Key Implementation
The system implements composite keys to prevent conflicts between different protocol types that share the same token ID. For example, token ID 162 can now have separate logs for FBC and RPC protocols:
- `(162, "fbc")` → AP01m_192-168-0-11_162.fbc
- `(162, "rpc")` → AP01m_192-168-0-11_163.rpc

This ensures that each protocol type maintains its own log file even when using the same token identifier.

## Performance Considerations
- File handles are kept open during active sessions
- Batch writing operations to reduce I/O overhead
- Efficient key lookup using composite key structure
- Memory-efficient handling of multiple concurrent logs

## Error Handling
- Graceful handling of file I/O errors
- Automatic retry mechanisms for transient failures
- Comprehensive logging of error conditions
- Fallback behavior for inaccessible log directories