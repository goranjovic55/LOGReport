# Log Writer Documentation

## Overview
Manages creation and writing to log files with standardized formats.

## Key Features
- Creates standardized log files
- Appends command outputs to logs
- Maintains open file handles for performance
- Handles file rotation
- Supports multiple log types (FBC, RPC, LOG, LIS)

## Log File Naming
- FBC: `{node}_{ip}_{token}.fbc`
- RPC: `{node}_{ip}_{token}.rpc`
- LOG: `{node}_{timestamp}_LOG.log`
- LIS: `{node}_{timestamp}_LIS.lis`

## Directory Structure
- FBC logs: `{log_root}/FBC/{node}/`
- RPC logs: `{log_root}/RPC/{node}/`
- LOG files: `{log_root}/{node}/`

## Important Methods
- `open_log()`: Creates/opens a log file
- `append_to_log()`: Writes output to log
- `close_log()`: Closes a specific log
- `close_all_logs()`: Cleans up all open logs

## Log Formatting
- Includes timestamp for each entry
- Preserves original command output
- Adds metadata headers
- Enforces consistent line endings