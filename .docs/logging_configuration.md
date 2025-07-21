# Logging Configuration and Unicode Handling

## Issue

A `UnicodeEncodeError` was encountered during logging when special Unicode characters (e.g., emojis like '📝') were present in log messages. This caused logging failures and incomplete log files.

## Resolution

The logging system was updated to explicitly use UTF-8 encoding when writing log files. This change ensures that all Unicode characters are correctly handled and logged without errors.

## Details

- Log files are now opened with `encoding='utf-8'`.
- This resolves issues with characters outside the ASCII range.
- Improves robustness and compatibility with diverse log content.

## Future Enhancements

- Consider implementing a backslashreplace fallback strategy for any unexpected encoding issues.
- Optimize the logging pipeline for higher throughput and lower latency.
- Explore memory-mapped logging for efficient file I/O operations.