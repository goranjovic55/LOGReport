# Changelog

## [Unreleased]
- Fixed issue where commands from `.fbc` log files were not displayed in the Telnet terminal. The fix involved removing an explicit `command_queue.start_processing()` call in [`FbcCommandService.queue_fieldbus_command()`](src/commander/services/fbc_command_service.py:53). This change ensures that FBC commands now follow the same processing flow as RPC commands, resulting in their outputs being correctly displayed in the terminal.
- Resolved `UnicodeEncodeError` in logging by configuring log file writing to use UTF-8 encoding, enabling proper handling of Unicode characters such as emojis (e.g., '📝').