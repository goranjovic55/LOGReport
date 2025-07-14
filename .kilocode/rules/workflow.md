## 🐞 Debugging & File Handling Best Practices

- **Path Normalization**: Always normalize file paths to prevent inconsistencies and ensure reliable file system operations across different environments.
- **Comprehensive File I/O Testing**: Implement thorough unit tests for all file input/output operations, especially parsing and filtering logic, to catch edge cases and prevent regressions.
- **Strategic Logging**: Integrate detailed and configurable logging for file scanning, processing, and UI population steps to facilitate effective debugging and traceability.
- **Iterative Debugging**: Encourage an iterative debugging approach with small, verifiable changes to isolate issues quickly and maintain system stability.
- **Clear Separation of Concerns**: Reinforce strict separation between file system interaction, data processing, and UI presentation layers to improve maintainability and reduce coupling.
- **Log File Structure**: Maintain consistent log directory structure (`log_root/LOG/`) for all log files.
- **Log Naming Pattern**: Use standardized log file naming pattern (`{node.name}_*.log`) for easy identification and parsing.
- **Token Extraction**: Extract tokens from log filenames without extensions for consistent processing.

**Usage**:
Kilo Code will automatically apply these rules across all modes. If it suggests creating files or performing refactors, ensure it adheres to this structure—otherwise, prompt correction ("Follow the rule in `.kilocode/rules/structure.md`).
