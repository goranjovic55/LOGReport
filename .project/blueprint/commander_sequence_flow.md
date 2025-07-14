# Commander Application Sequence Flow

## User Interface Initialization
1. CommanderWindow class initializes UI components
2. Sets up dual-pane layout (node tree and session tabs)
3. Configures node tree with context menu capability
4. Loads node configuration if available
5. Populates node tree with scanned log files

## Context Menu Execution Flow
```mermaid
sequenceDiagram
    participant User
    participant CommanderWindow
    participant NodeManager
    participant CommandResolver
    
    User->>CommanderWindow: Right-click FBC log item
    CommanderWindow->>CommanderWindow: Check item data
    CommanderWindow->>CommanderWindow: Validate token_id exists
    CommanderWindow->>CommanderWindow: Create context menu
    User->>CommanderWindow: Select "Print FieldBus Structure"
    CommanderWindow->>CommandResolver: Generate appropriate command
    CommanderWindow->>CommanderWindow: Set command in telnet input
    CommanderWindow->>CommanderWindow: Switch to telnet tab
    CommanderWindow->>CommanderWindow: Focus command input
```

## Key Interactions
- **CTX_MENU**: FieldBus command generation
- **STATUS_FEEDBACK**: Status bar messages
- **CMD_EXEC**: Telnet command execution
- **LOG_COPY**: Session content log saving