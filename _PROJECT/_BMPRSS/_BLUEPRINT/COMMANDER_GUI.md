# Commander GUI Blueprint

## Functional Overview
The Commander GUI provides centralized management of DNA system nodes through:
1. **Central DNA Debugger Session**: Single telnet connection for system-wide log retrieval
2. **Node-Specific VNC Connections**: Direct visual access to individual nodes
3. **Token-Based Command Execution**: Log retrieval commands mapped to specific tokens
4. **Automatic Log Saving**: Direct writing to structured log directories

## Command Processing Flow
```mermaid
sequenceDiagram
    User->>Commander: Select node, token, and log type
    alt Telnet Command
        Commander->>DNA_Debugger: Send formatted command
        DNA_Debugger->>Node: Route via token
        Node->>DNA_Debugger: Return log data
        DNA_Debugger->>Commander: Forward output
    else VNC Command
        Commander->>VNC_Viewer: Direct connection
        VNC_Viewer->>Node: Send keyboard sequence
        Node->>VNC_Viewer: Return visual output
        VNC_Viewer->>OCR: Extract text from screenshot
    end
    Commander->>LogFormatter: Apply LSR standards
    LogFormatter->>Filesystem: Save to test_logs/&lt;node>/&lt;token>_&lt;type>.log
```

## Log Retrieval Command Schema
```json
{
  "log_types": {
    "FBC": {
      "command": "print_fieldbus ${token}0000",
      "description": "Retrieve fieldbus I/O structure data"
    },
    "RPC": {
      "command": "print_rpc_logs ${token}",
      "description": "Get RPC command history"
    },
    "LOG": {
      "command": "get_system_logs ${token}",
      "description": "Retrieve system-level logs"
    }
  },
  "vnc_sequences": {
    "FBC_162": ["Ctrl+Alt+F1"],
    "FBC_163": ["Ctrl+Alt+F2"],
    "RPC_360": ["Ctrl+Alt+R"],
    "LOG_ALL": ["Ctrl+Alt+L"]
  }
}
```

## Session Management
1. **DNA Debugger Connection**:
   - Host/IP: debug-host.vendor.com
   - Port: 2077 (fixed for system)
   - Protocol: Telnet with TLS encryption
   - Credential management: Central credential service

2. **VNC Node Connections**:
   - Per-node host/IP configuration 
   - Port assignment: 5900 + token suffix
   - Independent credential sets
   - SSL encryption

## Core Components
1. **Connection Manager**: Maintains active sessions
2. **Command Resolver**: Translates token/type to commands
3. **Output Processor**: Formats responses per LSR standard
4. **Log Archiver**: Rotates and compresses old logs

