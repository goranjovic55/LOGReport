# Changelog

## [Unreleased] - 2025-07-18
### Fixed
- Debugging session for multiple context menu and log file errors:
  - `QMenu` not defined in commander_window.py
  - `CommanderWindow` missing `node_tree` reference
  - `open_log_file()` missing `column` parameter
- Fixed SyntaxError in commander_window.py:
  - Removed unnecessary `try` block at line 1190
  - Corrected indentation of subsequent code
  - Fixed typo (`Q极TextCursor` to `QTextCursor`) at line 1193
- Reverted changes via `git reset --hard` to previous stable commit

## [1.1.0] - 2025-07-14
### Added
- Comprehensive developer documentation in .docs/ directory
- Detailed code examples and usage patterns for all major components
- Quick start guide with setup instructions and examples
- Architecture overview document
- Component-specific documentation:
  - CommanderWindow with UI workflow examples
  - NodeManager with configuration examples
  - CommandServices with API usage
  - LogWriter with file format specifications
- Automatic output logging for context menu commands:
  - Command output is automatically captured and written to selected log files
  - Includes error handling and status messages
  - Supports both manual and automatic command execution
- Troubleshooting guide for common issues

### Changed
- Updated README.md with links to new documentation
- Improved code comments throughout the codebase
- Standardized documentation format across all files
- RPC command format now includes "0000" suffix (e.g., `print from fbc rupi counters {token_id}0000`)
- Context menu text updated to "Print Rupi counters Token 'tokenid_number'" and "Clear Rupi counters 'tokenid_number'"

### Fixed
- RPC tokens now correctly extracted and displayed as numerical/alphanumeric IDs only (no IP addresses or node names)
- LOG file detection in CommanderWindow now correctly:
  - Uses directory path: `log_root/LOG/`
  - Matches files with pattern: `{node.name}_*.log`
  - Extracts tokens from filenames without extension
- Minor documentation inaccuracies in method descriptions
- Updated outdated configuration examples
- Fixed SyntaxError in commander_window.py (line 1185) - corrected incomplete ternary operator to valid Python syntax
- Fixed Telnet command output redirection - responses now correctly display in terminal when executing via right-click on .fbc/.rpc files while maintaining manual log writing capability