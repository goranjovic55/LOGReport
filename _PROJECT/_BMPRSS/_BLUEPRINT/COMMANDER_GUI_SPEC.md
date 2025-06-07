# Commander GUI Specification

## 1. User Interface Layout
```
┌───────────────────────────────────────────┐
│         COMMANDER CONSOLE v1.0            │
├───────────────────────┬───────────────────┤
│                       │                   │
│   NODE MANAGEMENT     │    ACTIVE SESSION │
│   (30% width)         │    (70% width)    │
│                       │                   │
│  ┌──────────────────┐ │  ┌──────────────┐ │
│  │ Node Tree        │ │  │ DNA Debugger │ │
│  │ ● AP01m (Online) │ │  │ Terminal     │ │
│  │   ├─ 162 (FBC)   │ │  │ &gt; print_fie..│ │
│  │   └─ 163 (RPC)   │ │  │ [output]     │ │
│  │ ○ AP01r (Offline)│ │  └──────────────┘ │
│  └──────────────────┘ │                   │
│                       │  ┌──────────────┐ │
│  ┌──────────────────┐ │  │ VNC Viewer   │ │
│  │ Command List     │ │  │ [Screenshot] │ │
│  │ - FBC: Print IO  │ │  └──────────────┘ │
│  │ - RPC: Get Hist  │ │                   │
│  └──────────────────┘ └───────────────────┘
├───────────────────────┬───────────────────┤
│ [Execute] [Status]    │ [Save Log] [Config]│
└───────────────────────┴───────────────────┘
```

## 2. Functional Requirements

### 2.1 Node Management
- **Tree Structure**:
  - Nodes grouped by type/region
  - Expandable token lists per node
  - Icon indicators: Online/Offline/Warning
- **Node Properties**:
  - Host/IP for VNC connections
  - Token-to-command mappings
  - Last connection timestamp

### 2.2 Session Management
- **DNA Debugger Panel**:
  - Central telnet session to debug-host:2077
  - Command history with arrow-key navigation
  - ANSI color support for terminal output
  - Auto-connect on startup
- **VNC Viewer**:
  - Tabbed interface for multiple nodes
  - Screenshot capture tool
  - Customizable zoom levels

### 2.3 Command Execution
- **DNA Commands**:
  ```json
  {
    "FBC": "print_fieldbus ${token}0000",
    "RPC": "print_rpc_logs ${token}",
    "LOG": "get_system_logs ${token}"
  }
  ```
- **VNC Sequences**:
  - Token-specific keyboard macros
  - Configurable delays between keystrokes
  - Visual macro recorder

### 2.4 Log Saving
- **Auto-Save Rules**:
  - File naming: `test_logs/&lt;node>/&lt;token>_&lt;type>.log`
  - Automatic daily folder rotation
  - File lock detection (max 5 retries)
- **Output Formatting**:
  - LSR-compliant headers
  ```plaintext
  === DNA COMMAND LOG ===
  Node: AP01m
  Token: 162
  Type: FBC
  Timestamp: 20250605-142356
  Command: print_fieldbus 1620000
  =======================
  [output data]
  ```
  - OCR text cleanup filters

## 3. Technical Specifications

### 3.1 Hardware Requirements
- Minimum:
  - CPU: Quad-core 2.4GHz
  - RAM: 8GB
  - GPU: OpenGL 3.3 support (for VNC rendering)
- Recommended:
  - CPU: Hexa-core 3.2GHz+
  - RAM: 16GB
  - GPU: Dedicated with 4GB VRAM

### 3.2 Performance Targets
| Operation                | Target      |
|--------------------------|-------------|
| DNA Command Execution    | &lt; 200ms latency |
| VNC Connection           | &lt; 1500ms handshake |
| OCR Processing (1920x1080)| &lt; 800ms |
| Log Saving (1MB)         | &lt; 50ms |

### 3.3 Security Requirements
1. **Credential Storage**:
   - AES-256 encrypted credentials
   - System keyring integration
   - Automatic session token rotation
2. **Session Protection**:
   - TLS 1.3 for DNA debugger
   - VNC over SSH tunneling
   - Command execution auditing
3. **Access Control**:
   - Role-based permissions
   - Command allowlisting
   - Audit logging to syslog

## 4. Reliability Specifications

### 4.1 Error Handling
- **DNA Debugger Failures**:
  - Auto-reconnect with exponential backoff
  - Command queuing during outages
  - Session resume after disconnect
- **VNC System**:
  - Frame buffer recovery
  - Connection health monitoring
  - Fallback to raw screenshots when OCR fails
- **File System**:
  - Write retries for busy files
  - Temp file shadowing
  - Filesystem watcher integration

### 4.2 Logging Requirements
```python
# Sample log entry format
{
  "timestamp": "2025-06-05T14:30:45Z",
  "node": "AP01m",
  "token": "162",
  "command": "print_fieldbus 1620000",
  "status": "success",
  "duration": 234,  # ms
  "output_size": 14567,  # bytes
  "error": null
}
```
- Log retention: 30 days compressed

## 5. Compatibility Requirements
1. **Platform Support**:
   - Windows 10/11 (64-bit)
   - macOS 12+ (Intel/Apple Silicon)
   - Ubuntu LTS 22.04+ 
2. **VNC Implementations**:
   - TightVNC 2.8.x
   - TigerVNC 1.13.x
   - RealVNC 6+ 
3. **Environment Dependencies**:
   - Python 3.10+
   - Tesseract OCR 5.2+
   - OpenSSL 3.0+
