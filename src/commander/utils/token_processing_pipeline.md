# Token Processing Pipeline

This document describes the standardized token processing pipeline used throughout the application.

## Pipeline Stages

### 1. Input Sanitization
All token inputs should be sanitized before processing:
- Strip leading/trailing whitespace
- Convert to string if not already
- Handle None/empty values appropriately

### 2. Format Normalization
Tokens are normalized based on their type:
- **FBC Tokens**: 
  - Numeric tokens are padded to 3 digits with leading zeros
  - Alphanumeric tokens are converted to uppercase
- **Other Tokens**: 
  - Strip whitespace only

### 3. Validation
Tokens are validated according to their type:
- **FBC Tokens**: Must be exactly 3 digits
- **Other Tokens**: Must be non-empty after sanitization

### 4. Command Formatting
Tokens are formatted for use in commands:
- **FBC Tokens**: Padded to 3 digits and appended with "0000"
- **Other Tokens**: Used as-is

## Implementation

The pipeline is implemented in `src/commander/utils/token_utils.py` with the following functions:

### `normalize_token(token_id: str, token_type: Optional[str] = None) -> str`
Normalizes a token ID according to the rules for its type.

### `validate_token(token: NodeToken) -> bool`
Validates a token object.

### `is_valid_fbc_token(token_id: str) -> bool`
Checks if a token ID is valid for FBC tokens.

### `format_token_for_command(token_id: str, token_type: str = "FBC") -> str`
Formats a token ID for use in commands.

## Usage Examples

### FBC Token Processing
```python
# Input: "1"
normalized = normalize_token("1", "FBC")  # Returns "001"
is_valid = is_valid_fbc_token(normalized)  # Returns True
formatted = format_token_for_command(normalized, "FBC")  # Returns "0010000"

# Input: "abc"
normalized = normalize_token("abc", "FBC")  # Returns "ABC"
is_valid = is_valid_fbc_token(normalized)  # Returns False
```

### RPC Token Processing
```python
# Input: " 123 "
normalized = normalize_token(" 123 ", "RPC")  # Returns "123"
is_valid = validate_token(NodeToken("123", "RPC"))  # Returns True
formatted = format_token_for_command(normalized, "RPC")  # Returns "123"
```

## Backward Compatibility

The token utilities maintain backward compatibility with existing code by:
- Preserving existing behavior for FBC tokens when token_type is not specified
- Providing default values for optional parameters
- Maintaining the same validation rules as the original implementations

## Migration Path

Services currently implementing their own token processing should be updated to use the shared utilities:

1. **FbcCommandService** and **RpcCommandService**: Remove `normalize_token` method and import from `token_utils`
2. **SessionManager**: Update `validate_token` method to use `token_utils.validate_token`
3. **NodeManager**: Update token normalization logic to use `token_utils.normalize_token`
4. **Command generation**: Update command generation to use `token_utils.format_token_for_command`

## Testing

All token processing functions should be thoroughly tested with:
- Valid inputs for each token type
- Invalid inputs (None, empty strings, non-numeric for FBC)
- Edge cases (single digit, maximum length, special characters)
- Backward compatibility scenarios