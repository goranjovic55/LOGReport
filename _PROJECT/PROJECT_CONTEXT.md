# Project Context - Commander LogCreator

## Project Structure
```
d:/_APP/LOGReport
├── .gitignore
├── BUILD-INSTRUCTIONS.md
├── build.bat
├── create_venv.ps1
├── errors.txt
├── LOGReporter.spec
├── nodes_list.txt
├── nodes_test.json
├── nodes.json
├── README.md
├── requirements-narrow.txt
├── requirements.txt
├── run_dev.ps1
├── system.log
├── TAB_log_report_20250529.pdf
├── TEST_log_report_20250604.pdf
├── test_qt.py
├── test_telnet_server.py
├── version_info.txt
├── _DIA/
├── _PROJECT/
│   ├── PROJECT_CONTEXT.md
│   ├── _BMPRSS/
│   │   ├── _BLUEPRINT/
│   │   │   ├── COMMANDER_GUI_SPEC.md
│   │   │   ├── COMMANDER_GUI.md
│   │   │   ├── COMMANDER_SEQUENCE_FLOW.md
│   │   │   ├── FILE_PROCESSING.md
│   │   │   ├── GUI_DESIGN.md
│   │   │   ├── OUTPUT_SPECIFICATION.md
│   │   │   └── SYSTEM_ARCHITECTURE.md
│   │   ├── _CODE/
│   │   │   ├── _STANDARDS/
│   │   │   │   ├── LSR_STANDARD.md
│   │   │   │   ├── README.md
│   │   │   │   ├── LSR_EXAMPLES/
│   │   │   │   │   ├── EXAMPLE_LOG.md
│   │   │   │   │   ├── EXAMPLE_RULE.md
│   │   │   │   │   └── EXAMPLE_SUMMARY.md
│   │   │   │   └── LSR_TEMPLATES/
│   │   │   │       ├── LOG_TEMPLATE.md
│   │   │   │       ├── RULE_TEMPLATE.md
│   │   │   │       └── SUMMARY_TEMPLATE.md
│   │   │   └── ... (other files in _CODE)
│   │   ├── _MODELS/
│   │   ├── _PLAN/
│   │   ├── _ROADMAP/
│   │   ├── _STANDARD/
│   │   │   ├── LSR_AUTOMATION_SCRIPTS.ps1
│   │   │   └── PROJECT_STANDARDS.md
│   │   ├── _STATUS/
│   │   └── _STRUCTURE/
│   ├── _LATEST_CHANGE/
│   │   ├── commander_window.py
│   │   ├── log_writer.py
│   │   └── PROJECT_CONTEXT.md
│   ├── _PLAN/
│   ├── _ROADMAP/
│   │   └── DEV_ROADMAP.md
│   ├── _STATUS/
│   └── _STRUCTURE/
├── assets/
├── build/
│   └── LOGReporter/
│       ├── Analysis-00.toc
│       ├── base_library.zip
│       ├── EXE-00.toc
│       ├── LOGReporter.pkg
│       ├── PKG-00.toc
│       ├── PYZ-00.pyz
│       ├── PYZ-00.toc
│       ├── warn-LOGReporter.txt
│       ├── xref-LOGReporter.html
│       └── localpycs/
│           ├── pyimod01_archive.pyc
│           ├── pyimod02_importers.pyc
│           ├── pyimod03_ctypes.pyc
│           ├── pyimod04_pywin32.pyc
│           └── struct.pyc
├── src/
│   ├── generator.py
│   ├── gui_workers.py
│   ├── gui.py
│   ├── log_creator.py
│   ├── main.py
│   ├── node_config_dialog.py
│   ├── nodes.json
│   ├── processor.py
│   ├── commander/
│   │   ├── __init__.py
│   │   ├── commander_window.py
│   │   ├── icons.py
│   │   ├── log_writer.py
│   │   ├── models.py
│   │   ├── node_manager.py
│   │   ├── qt_init.py
│   │   ├── session_manager.py
│   │   ├── telnet_client.py
│   │   ├── widgets.py
│   │   ├── commands/
│   │   │   └── telnet_commands.py
│   │   └── utils/
│   │       └── telnet_filters.py
│   ├── gui/
│   ├── runtime_hooks/
│   │   └── runtime_hook.py
│   └── utils/
│       └── file_utils.py
├── test_logs/
│   ├── AL01/
│   │   └── 186_LOG.log
│   ├── AL02/
│   │   └── 386_LOG.log
│   ├── AL03/
│   │   └── 451_LIS.log
│   ├── AP01m/
│   │   ├── 162_FBC.log
│   │   ├── 163_RPC.log
│   │   └── 163_VNC.log
│   ├── ... (other test_logs directories)
└── upx/
    └── upx.exe
```

## Implementation Status
### Node Management (Complete)
- Hierarchical node display
- Online/offline status indicators
- Log file scanning and organization
- Context menu for FieldBus operations

### Command Execution (Complete)
- Telnet command execution
- Connection management
- Session persistence
- Command history

### Log Processing (Complete)
- Log file viewing
- Session output capture
- Automated fieldbus command generation
- Log file rotation

### GUI Components (Complete)
- Dual-pane interface (nodes + sessions)
- Dark theme implementation
- Progress indicators
- Status bar notifications

## Technical Specifications
- **Core Framework**: PyQt6 6.4.2
- **Network Protocols**: Telnet (implemented), VNC/FTP (planned)
- **Log Processing**: Custom parser with token extraction
- **Report Generation**: PDF/DOCX via reportlab/python-docx
- **Version**: 1.2
- **Platform**: Windows 10/11

## Dependencies
### Core Functionality
- PyQt6==6.4.2
- reportlab==4.0.4
- python-docx==0.8.11

### Network Operations
- telnetlib3==1.0.4
- paramiko==3.4.0 (SSH tunneling)

### Additional Components
- keyring==24.3.0 (credential storage)
- pytesseract==0.3.10 (OCR)
- Pillow==10.3.0 (image processing)

### Build Tools
- pyinstaller==6.5.0
- pefile==2023.2.7

## Build Process
### Requirements
- Python 3.10+
- Windows OS
- UPX executable (optional for compression)

### Steps:
```powershell
# 1. Create virtual environment
.\create_venv.ps1

# 2. Install dependencies
pip install -r requirements-narrow.txt

# 3. Build executable
.\build.bat
```

### Output:
- Standalone executable: `dist\LOGReporter\LOGReporter.exe`
- Build artifacts: `build\` directory
- Compression: UPX used if available

### Verification:
1. Executable launches Commander interface
2. Node connections functional
3. Command execution works
4. Log processing operational

## Next Steps
- Implement VNC/FTP session support
- Add PDF/CSV export functionality
- Develop persistent session history
- Create LIS parser module
- Refine log analysis algorithms