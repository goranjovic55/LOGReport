# Project Context - Commander LogCreator

## Application Overview
Commander LogCreator is a PyQt6-based application for managing remote nodes, executing commands, and processing log files. The application features a dual-pane interface with node management on the left and session tabs (Telnet/VNC/FTP) on the right.

## Key Features Implemented
### Node Management
- Hierarchical display of nodes and log files
- Online/offline status indicators
- Log file scanning and organization

### FieldBus Command System
- Context menu for FieldBus operations
- Token extraction from FBC filenames
- Automatic command generation
```python
# Token extraction example
filename = "AP01m_192-168-0-11_162.fbc"
parts = filename.split('_')
token_id = parts[-1].split('.')[0]  # -> "162"
command = f"print from fieldbus io structure {token_id}0000"
```

### Session Management
- Telnet command execution
- VNC/FTP session handling
- Connection status indicators

### Log Processing
- Log file viewing
- Session output capture
- Automated commands for fieldbus operations

## Latest Updates
1. **FieldBus Context Menu**
   - Implemented right-click command generation for FBC items
   - Automatic token recognition from filenames
   - Telnet command autofill

2. **Stability Improvements**
   - Fixed context menu conflicts
   - Enhanced logging for context operations
   - Improved token extraction reliability

## Technical Specifications
- **Core Framework**: PyQt6
- **Network Protocols**: Telnet, FTP, VNC
- **Log Processing**: Custom log parser
- **Version**: 1.1
- **Platform**: Windows

## Next Steps
- Implement export functionality (PDF/CSV)
- Add persistent session history system
- Integrate VNC viewer component
- Develop LIS parser module