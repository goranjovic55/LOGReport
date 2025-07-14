# Changelog

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
- Troubleshooting guide for common issues

### Changed
- Updated README.md with links to new documentation
- Improved code comments throughout the codebase
- Standardized documentation format across all files

### Fixed
- LOG file detection in CommanderWindow now correctly:
  - Uses directory path: `log_root/LOG/`
  - Matches files with pattern: `{node.name}_*.log`
  - Extracts tokens from filenames without extension
- Minor documentation inaccuracies in method descriptions
- Updated outdated configuration examples