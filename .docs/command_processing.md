# Command Processing Flow

This document explains the command processing flow for `.fbc` (Fieldbus Command) and `.rpc` (Remote Procedure Call) logs.

## Background

Previously, `.fbc` commands were not properly written to files despite being displayed in the terminal. This was due to an explicit call to `command_queue.start_processing()` in the `FbcCommandService.queue_fieldbus_command()` method, which caused the `.fbc` commands to bypass the unified processing flow.

## Fix Implemented

The fix involved removing the explicit `start_processing()` call, aligning `.fbc` command processing with the `.rpc` command flow. Now, both command types are queued and processed uniformly, ensuring:

- Commands are properly queued.
- Outputs are displayed in the Telnet terminal.
- Commands are written to the appropriate log files.

This alignment improves consistency, reliability, and maintainability of command handling.

## Future Plans

- Implement asynchronous batch processing to improve throughput.
- Develop a unified command interface to standardize command handling.
- Enforce command timeout policies for robustness.