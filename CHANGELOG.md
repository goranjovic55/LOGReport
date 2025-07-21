## [Unreleased]
### Fixed
- Fixed ConnectionAbortedError (WinError 10053) in Telnet socket tests by:
  - Removing problematic socket test byte sending in command_queue.py
  - Adding explicit ConnectionAbortedError handling in telnet_client.py
  - Confirming proper CTRL+x and CTRL+z sequence handling in TelnetClient
- Fixed AttributeError in TelnetSession by adding prompt_pattern initialization ([#123](https://github.com/your/repo/issues/123))
# Changelog

## [Unreleased] - 2025-07-20
### Added
- Memory consolidation analysis for src/commander/ directory
- Comprehensive type hinting for NodeToken attributes
- get_or_create_session method implementation in SessionManager
- Enhanced error handling for Telnet writes in telnet_client.py
- Type hinting for `item` parameter in `_handle_queued_command_result` method

### Fixed
- AttributeError in command_queue.py by standardizing NodeToken attribute names (node_name → name, node_ip → ip_address)
- Improved empty response handling in command_queue.py to log warnings instead of raising ValueErrors
- 'SessionManager' object has no attribute 'get_or_create_session' error
- ConnectionError in TelnetSession.send_command with improved error handling
- Corrected NodeToken attribute usage in command_queue.py
- TypeError in commander_window.py by changing dictionary-style access to attribute access for QueuedCommand objects
- Architectural documentation for core components:
  - NodeToken and Node entity relationships
  - CommanderWindow orchestration patterns
  - Command service interfaces
- New development guidelines:
  - Explicit interface definitions
  - Modular architecture principles
  - Pre-development planning requirements
- QueuedCommand dataclass for type-safe queue items in command_queue.py

### Changed
- Unified token handling across command services
- Improved abstraction layers for features and services
- Memory graph updated with merged duplicates and grouped clusters
- SessionManager decoupled from CommandQueue by passing it directly via constructor
- Streamlined automatic command logging logic by centralizing path resolution in LogWriter

### Fixed
- Duplicate code in token handling resolved
- Missing abstraction layers identified and addressed
- Naming inconsistencies cleaned up in memory graph
- CommandWorker.run() now properly executes commands via TelnetSession
- _handle_queued_command_result now correctly logs command results
- TelnetSession is properly passed to CommandWorker during creation
- Verified consistent logging behavior for both manual and automatic commands

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
## [Fixed]
- Telnet connection failures caused by type mismatch in prompt pattern matching
- Added missing logging imports in telnet_client.py and session_manager.py
- Improved debug logging for Telnet connection sequence