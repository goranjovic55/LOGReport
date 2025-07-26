# Changelog

## [Unreleased]

- Updated memory management workflow documentation in `.docs/memory_management.md` to reflect the improved dual memory consolidation process using `project_memory` and `global_memory` MCP servers.
- Enhanced README.md with a high-level overview of the memory consolidation process, detailing how the system uses dual memory for project-specific and cross-project knowledge.
- Updated documentation workflow to follow the MCP-aligned, command-safe pattern with consistent identity scoping using `document_user`.
- Added sequential reasoning planning using the `sequential_thinking` MCP server for structured documentation updates.
- Incorporated external validation using the `firecrawl_mcp` MCP server to ensure documentation aligns with community standards.
- Updated memory loading, tracking, and persistence steps to use MCP server tools for both project and global memory.
- Finalized memory updates with proper session closure and traceability under the `document_user` identity.
- Implemented context menu filtering system to control command visibility based on node type and section. The `ContextMenuFilterService` now manages filtering rules from configuration, allowing for flexible control of context menu items without code changes.
- Removed AP01m command from FBC subclass group context menus through configuration-driven filtering. This optimization reduces clutter and prevents execution of deprecated commands on specific node types.
- Documented the existing functionality for right-click actions on FBC and RPC group nodes in the README.md. This includes the use of `CommanderWindow.process_all_fbc_subgroup_commands` and `process_all_rpc_subgroup_commands` methods, which utilize `NodeManager` to get child log files and `CommandQueue` to dispatch commands with error handling and sequential processing.
- Fixed issue where commands from `.fbc` log files were not displayed in the Telnet terminal. The fix involved removing an explicit `command_queue.start_processing()` call in [`FbcCommandService.queue_fieldbus_command()`](src/commander/services/fbc_command_service.py:53). This change ensures that FBC commands now follow the same processing flow as RPC commands, resulting in their outputs being correctly displayed in the terminal.
- Resolved `UnicodeEncodeError` in logging by configuring log file writing to use UTF-8 encoding, enabling proper handling of Unicode characters such as emojis (e.g., '📝').
- Consolidated Telnet operations and command services into standardized patterns, promoting reusable components to global memory.
- Implemented the NetworkSession base class for standardized network operations.
- Standardized error handling with global error codes.
- Optimized the memory graph with a hierarchical service taxonomy.