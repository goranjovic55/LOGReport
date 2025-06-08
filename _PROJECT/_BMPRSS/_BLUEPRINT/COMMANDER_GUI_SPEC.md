# Commander GUI Specification v2.1

**Last Updated:** 2025-06-08  
**Key Changes:** Added session tabs, enhanced node tree, connection management

## 1. Dual-Pane Interface
```plaintext
┌───────────────────────────────┬───────────────────────────────┐
│       NODE MANAGEMENT PANE    │     SESSION OPERATIONS        │
│         (Fixed 30% width)     │        (70% width)            │
├───────────────────────────────┼───────────────────────────────┤
│ ● Node Tree:                  │ ┌──TABS─────────────────────┐ │
│   ▼ AP01m (192.168.1.101 ●)   │ │  Telnet | VNC  | FTP      │ │
│     ├─162 [FBC]               │ ├───────────────────────────┤ │
│     │   Log: test_logs/AP01m/162_fbc.log │ [Session Content]  │
│     └─163 [VNC]               │ │                           │ │
│         Log: ...163_vnc.log   │ └───────────────┐           │ │
│                               │ ┌──CONNECT BAR──┤           │ │
│ ● Commands:                   │ │ [IP:Port] [●] [Connect]   │ │
│   - p s (Print System)        │ └───────────────┘           │ │
│   - fis (Fieldbus I/O Struct) │                               │
│   - rc (RUPI Counters)        │ [Copy to Log Button]          │
│                               │ [Save Log Session]            │
│ [Add Node] [Edit] [Refresh]   │                               │
└───────────────────────────────┴───────────────────────────────┘
```

## 2. Node Tree Specification

**Node Properties:**
```markdown
- **Name Prefix**: AP/AL prefix validation
- **IP Address**: IPv4 format enforcement
- **Status Indicators**:
  - ● Green: Active session
  - ○ Gray: Offline
  - ⚠ Yellow: Connection issues

- **Token-Level Details**:
  - ID: 3-5 digit token code
  - Type: FBC/RPC/LOG/LIS
  - Protocol: Telnet/VNC/FTP
  - Log Path: `test_logs/<node>/<token>_<type>.log`
  - Handle Status: [Open/Closed]
```

## 3. Session Tabs

### Telnet Tab Features:
```markdown
- **Command Palette**: Predefined token commands
- **History Viewer**: Scrollable executed commands
- **Manual Input**: Raw command editor with:
   - Syntax highlight
   - Token substitution (% → current token)
   - Suggestion autocomplete
- **Output Console**: ANSI-color supported display
- **Bottom Connection Bar**:
   - IP:Port display with connection status
   - Connect/Disconnect buttons

### VNC Tab Features:
```markdown
- **Embedded Viewer**: Tightly integrated VNC client
- **Clipboard Integration**:
   - Right-click copy to system clipboard
   - Copy to Node Log button
   - OCR text extraction option
- **Capture Tools**:
   - Full screen/region selection
   - Auto-refresh interval setting
- **Bottom Connection Bar**: VNC-specific IP:Port and controls

### FTP/TFTP Tab Features:
```markdown
- **Remote Tree**: Hierarchical folder navigation
- **File Preview**: Text file viewing
- **Clipboard Actions**:
   - Copy file content to log
   - Copy file metadata
   - Compare with local version
- **Log Annotations**: Auto-header with source path
- **Bottom Connection Bar**: FTP credentials and server info
```

## 4. Connection Management System
```mermaid
flowchart TD
    A[Select Node+Token] --> B{Protocol}
    B -->|Telnet| C[Set IP:NodeIP Port:2077]
    B -->|VNC| D[Set IP:NodeIP Port:5900+Token]
    B -->|FTP| E[Set IP:NodeIP Port:2121]
    C --> F[Update Connection Bar]
    D --> F
    E --> F
    F --> G[Enable Connect Button]
    
    H[Connect Clicked] --> I{Session Type}
    I -->|Telnet| J[Open Telnet Connection]
    I -->|VNC| K[Launch VNC Viewer]
    I -->|FTP| L[Init FTP Session]
```

## 5. Content Transfer Protocols

**Telnet Output Transfer:**
```python
def transfer_telnet_output(output, log_path):
    with open(log_path, 'a', encoding='utf-8') as log:
        header = f"// TELNET CAPTURE {datetime.now()}"
        log.write(f"{header}\n{'-'*40}\n")
        log.write(output)
```

**VNC Content Transfer:**
```python
def vnc_to_log(viewer, log_path):
    if OCR_ENABLED:
        text = viewer.extract_text()
    else:
        text = viewer.get_clipboard()
    
    with open(log_path, 'a') as log:
        log.write(f"VNC CAPTURE:\n{text}")
```

**FTP File Transfer:**
```python
def ftp_to_log(ftp_client, remote_path, log_path):
    content = ftp_client.retrieve(remote_path)
    with open(log_path, 'a', encoding='utf-8') as log:
        log.write(f"FTP CONTENT [{remote_path}]:\n")
        log.write(content)
```

## 6. Security Implementation
```mermaid
classDiagram
    class CredentialStore {
        +encrypt(credentials)
        +decrypt(token)
        +rotate_keys()
    }
    
    class SessionManager {
        +start_session(type, ip, port)
        +validate_certificate()
        +close_all()
    }
    
    CredentialStore <-- SessionManager
```

**Protocol Security:**
- Telnet: TLS 1.3 encryption
- VNC: SSH tunneling
- FTP: FTPS explicit encryption
- Credential storage: AES-256 encrypted vault

## 7. Performance Targets
| Operation                | Max Latency |
|--------------------------|-------------|
| Telnet Command Execution | ≤ 200ms     |
| VNC Connection           | ≤ 1500ms    |
| OCR Processing (1080p)   | ≤ 800ms     |
| Log Write (1MB)          | ≤ 50ms      |
| GUI Refresh Rate         | 60 FPS      |

## 8. Best Practices
1. **Connection Management**:
   - Auto-reconnect with exponential backoff
   - Session state persistence
   - Connection pooling for high-frequency commands
   
2. **Log Handling**:
   - Atomic file writes
   - Buffer management
   - File rotation at 100MB

3. **Cross-Platform Support**:
   - Windows, macOS, and Linux compatibility
   - Accessibility features
   - High DPI support
```