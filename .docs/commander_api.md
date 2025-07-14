# Commander Module API Documentation

## Recent Updates
- Fixed SyntaxError in Telnet client command processing
- Corrected token display logic in UI components
- Telnet command responses now properly output to terminal instead of files

## Command Queue
- Handles asynchronous command execution
- Supports both Telnet and RPC command types
- Thread-safe implementation

## LogWriter
### Enhancements:
- Added OutputDestination enum for clear output handling
- Implemented configurable logging levels
- Improved file writing performance

## Node Manager
- Manages node connections and state
- Uses Observable pattern with signal-based UI updates
- Supports both FBC and RPC node types
- UI updates are decoupled via event signals