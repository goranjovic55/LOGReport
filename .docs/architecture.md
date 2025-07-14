# LOGReport Architecture Overview

## Core Components

### Commander Module
- **commander_window.py**: Main GUI window with node tree view and session management
- **node_manager.py**: Manages node configurations and log file scanning
- **log_writer.py**: Handles log file creation and writing
- **command_queue.py**: Processes commands sequentially

### Services
- **fbc_command_service.py**: Handles FieldBus Controller commands
- **rpc_command_service.py**: Handles Remote Procedure Call commands

## Data Flow
1. User loads node configuration
2. NodeManager scans for log files
3. CommanderWindow displays nodes and logs in tree view
4. User executes commands which are processed by CommandQueue
5. Results are written to logs via LogWriter

## Key Design Patterns
- Model-View-Presenter for GUI components
- Command pattern for telnet/RPC commands
- Observer pattern for status updates