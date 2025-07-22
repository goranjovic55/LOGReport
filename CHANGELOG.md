# Changelog

## [Unreleased]

- Documented the existing functionality for right-click actions on FBC and RPC group nodes in the README.md. This includes the use of `CommanderWindow.process_all_fbc_subgroup_commands` and `process_all_rpc_subgroup_commands` methods, which utilize `NodeManager` to get child log files and `CommandQueue` to dispatch commands with error handling and sequential processing.
- Fixed issue where commands from `.fbc` log files were not displayed in the Telnet terminal. The fix involved removing an explicit `command_queue.start_processing()` call in [`FbcCommandService.queue_fieldbus_command()`](src/commander/services/fbc_command_service.py:53). This change ensures that FBC commands now follow the same processing flow as RPC commands, resulting in their outputs being correctly displayed in the terminal.
- Resolved `UnicodeEncodeError` in logging by configuring log file writing to use UTF-8 encoding, enabling proper handling of Unicode characters such as emojis (e.g., '📝').
- Consolidated Telnet operations and command services into standardized patterns, promoting reusable components to global memory.
- Implemented the NetworkSession base class for standardized network operations.
- Standardized error handling with global error codes.
- Optimized the memory graph with a hierarchical service taxonomy.