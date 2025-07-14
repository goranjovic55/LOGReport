# Log File Format Specification

## File Structure
- Logs are stored in `log_root/LOG/` directory structure
- Follows standardized naming pattern: `{node.name}_*.log`

## Recent Optimizations
- Centralized filename parsing logic in dedicated utility modules
- Improved token extraction from filenames (without extensions)
- Added validation for naming conventions

## File Format Examples
```
AP01m_192-168-0-11_162.fbc  # FBC log format
AP01r_192-168-0-27_363.rpc  # RPC log format
AL01_186_LOG.log            # Standard log format
```

## Processing Rules
1. Tokens are extracted from filenames before the extension
2. Node name must match pattern `[A-Z0-9]+`
3. IP addresses must be in standard dotted or dashed notation
4. Port numbers must be numeric

## Test Coverage
- Unit tests cover all parsing utilities
- Integration tests validate full processing pipeline
- 100% coverage required for filename parsing logic