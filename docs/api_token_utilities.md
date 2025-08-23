# Token Utilities API Documentation

## Overview

The Token Utilities module provides comprehensive token normalization, validation, and processing functions for the LOGReport Commander application. This module ensures consistent token handling across the entire system.

## Module Structure

```
src/commander/utils/token_utils.py
├── TokenValidator Class
├── TokenRateLimiter Class
├── Global Utility Functions
└── Singleton Instances
```

## Classes

### TokenValidator

The `TokenValidator` class provides core token validation and normalization functionality.

#### Constructor

```python
TokenValidator()
```

**Description**: Initializes the token validator with logging and caching setup.

#### Methods

##### `normalize_token(token: str) -> str`

**Description**: Normalizes a token string with caching for performance.

**Parameters**:
- `token` (str): Raw token string to normalize

**Returns**:
- `str`: Normalized token string

**Normalization Rules**:
- **FBC Tokens**: 3-digit numeric tokens are padded with zeros, alphanumeric tokens are converted to uppercase
- **RPC Tokens**: Converted to lowercase, non-alphanumeric characters removed
- **LOG/LIS Tokens**: Basic lowercase conversion with character filtering
- **Numeric Tokens**: Padded with leading zeros to make 3 digits if length < 3

**Examples**:
```python
from src.commander.utils.token_utils import normalize_token

# FBC token normalization
normalize_token("162")      # Returns "162"
normalize_token("abc")      # Returns "ABC" (FBC alphanumeric)
normalize_token("1a")       # Returns "1A" (FBC alphanumeric)

# RPC token normalization
normalize_token("xyz123")   # Returns "xyz123"
normalize_token("ABC-123")  # Returns "abc123"

# Numeric token padding
normalize_token("1")        # Returns "001"
normalize_token("12")       # Returns "012"
```

##### `validate_token(token: str) -> bool`

**Description**: Validates a token against the standard pattern.

**Parameters**:
- `token` (str): Token string to validate

**Returns**:
- `bool`: True if token is valid, False otherwise

**Validation Rules**:
- Token must match the pattern `^[a-zA-Z0-9]+$`
- Token must not be empty
- Token must be a string

**Examples**:
```python
from src.commander.utils.token_utils import validate_token

validate_token("162")      # Returns True
validate_token("abc")      # Returns True
validate_token("abc-123")  # Returns False (contains hyphen)
validate_token("")         # Returns False (empty)
validate_token(123)        # Returns False (not a string)
```

##### `is_fbc_token(token: str) -> bool`

**Description**: Check if a token is an FBC token (3 digits followed by optional lowercase letter).

**Parameters**:
- `token` (str): Token string to check

**Returns**:
- `bool`: True if token is FBC type, False otherwise

**FBC Token Pattern**: `^\d{3}[a-z]?$`

**Examples**:
```python
from src.commander.utils.token_utils import is_fbc_token

is_fbc_token("162")      # Returns True
is_fbc_token("162a")     # Returns True
is_fbc_token("abc")      # Returns False
is_fbc_token("16")       # Returns False (too short)
```

##### `is_rpc_token(token: str) -> bool`

**Description**: Check if a token is an RPC token (alphanumeric, not FBC).

**Parameters**:
- `token` (str): Token string to check

**Returns**:
- `bool`: True if token is RPC type, False otherwise

**RPC Token Pattern**: `^[a-z0-9]+$` and not FBC

**Examples**:
```python
from src.commander.utils.token_utils import is_rpc_token

is_rpc_token("abc123")   # Returns True
is_rpc_token("162")      # Returns False (is FBC)
is_rpc_token("ABC123")   # Returns False (uppercase)
is_rpc_token("abc-123")  # Returns False (contains hyphen)
```

##### `validate_token_node(token, node_name: str = None) -> bool`

**Description**: Validate that a token's node information is valid.

**Parameters**:
- `token`: NodeToken object to validate
- `node_name` (str, optional): Node name to validate against

**Returns**:
- `bool`: True if node information is valid, False otherwise

**Validation Checks**:
- Token must have `ip_address` and `token_id` attributes
- IP address must be non-empty and a string
- Node name must match if provided

**Examples**:
```python
from src.commander.utils.token_utils import validate_token_node

# Basic validation
token = type('Token', (), {'ip_address': '192.168.1.1', 'token_id': '162'})()
validate_token_node(token)  # Returns True

# Validation with node name
validate_token_node(token, "TEST_NODE")  # Returns True if token.name == "TEST_NODE"

# Invalid token (missing attributes)
invalid_token = type('Token', (), {})()
validate_token_node(invalid_token)  # Returns False
```

### TokenRateLimiter

The `TokenRateLimiter` class provides rate limiting for token processing operations.

#### Constructor

```python
TokenRateLimiter(max_tokens_per_second: int = 100)
```

**Parameters**:
- `max_tokens_per_second` (int): Maximum number of tokens to process per second (default: 100)

#### Methods

##### `is_allowed() -> bool`

**Description**: Check if processing a token is allowed under rate limits.

**Returns**:
- `bool`: True if allowed, False if rate limit exceeded

##### `get_wait_time() -> float`

**Description**: Get the time to wait before processing the next token.

**Returns**:
- `float`: Time in seconds to wait

## Global Utility Functions

### normalize_token(token: str) -> str

**Description**: Normalize a token string using the singleton validator.

**Parameters**:
- `token` (str): Raw token string to normalize

**Returns**:
- `str`: Normalized token string

### validate_token(token: str) -> bool

**Description**: Validate a token using the singleton validator.

**Parameters**:
- `token` (str): Token string to validate

**Returns**:
- `bool`: True if token is valid, False otherwise

### is_fbc_token(token: str) -> bool

**Description**: Check if a token is an FBC token using the singleton validator.

**Parameters**:
- `token` (str): Token string to check

**Returns**:
- `bool`: True if token is FBC type, False otherwise

### is_rpc_token(token: str) -> bool

**Description**: Check if a token is an RPC token using the singleton validator.

**Parameters**:
- `token` (str): Token string to check

**Returns**:
- `bool`: True if token is RPC type, False otherwise

### validate_token_node(token, node_name: str = None) -> bool

**Description**: Validate that a token's node information is valid.

**Parameters**:
- `token`: NodeToken object to validate
- `node_name` (str, optional): Node name to validate against

**Returns**:
- `bool`: True if node information is valid, False otherwise

### is_token_processing_allowed() -> bool

**Description**: Check if token processing is allowed under rate limits.

**Returns**:
- `bool`: True if allowed, False if rate limit exceeded

### get_token_processing_wait_time() -> float

**Description**: Get the time to wait before processing the next token.

**Returns**:
- `float`: Time in seconds to wait

## Singleton Instances

The module provides singleton instances for global use:

- `token_validator`: Instance of `TokenValidator` for token operations
- `token_rate_limiter`: Instance of `TokenRateLimiter` for rate limiting

## Usage Examples

### Basic Token Normalization

```python
from src.commander.utils.token_utils import normalize_token, is_fbc_token, is_rpc_token

# Normalize different token types
fbc_token = normalize_token("162")      # "162"
rpc_token = normalize_token("abc123")   # "abc123"
log_token = normalize_token("LOG001")   # "log001"

# Check token types
print(is_fbc_token("162"))      # True
print(is_rpc_token("abc123"))   # True
print(is_fbc_token("abc123"))   # False
```

### Token Validation

```python
from src.commander.utils.token_utils import validate_token, validate_token_node

# Validate token format
is_valid = validate_token("162")  # True
is_invalid = validate_token("16-2")  # False

# Validate token node information
class MockToken:
    def __init__(self, ip, token_id, name):
        self.ip_address = ip
        self.token_id = token_id
        self.name = name

token = MockToken("192.168.1.1", "162", "TEST_NODE")
is_valid_node = validate_token_node(token, "TEST_NODE")  # True
```

### Rate Limiting

```python
from src.commander.utils.token_utils import is_token_processing_allowed, get_token_processing_wait_time

# Check if processing is allowed
if is_token_processing_allowed():
    # Process token
    process_token()
else:
    # Wait before processing
    wait_time = get_token_processing_wait_time()
    time.sleep(wait_time)
```

## Error Handling

The module provides comprehensive error handling:

- **Type Errors**: Functions validate input types and raise appropriate errors
- **Value Errors**: Invalid token formats are handled gracefully
- **Attribute Errors**: Token validation checks for required attributes
- **Logging**: All errors are logged with appropriate severity levels

## Performance Considerations

- **Caching**: The `normalize_token` method uses LRU caching to improve performance
- **Rate Limiting**: Built-in rate limiting prevents excessive token processing
- **Regular Expressions**: Compiled patterns are used for efficient validation
- **String Operations**: Optimized string processing with minimal allocations

## Integration with NodeManager

The token utilities are designed to work seamlessly with the NodeManager:

```python
from src.commander.node_manager import NodeManager
from src.commander.utils.token_utils import normalize_token

# Create NodeManager instance
nm = NodeManager()

# Load configuration (uses token normalization internally)
nm.load_configuration("nodes.json")

# Access normalized tokens
node = nm.get_node("TEST_NODE")
if node:
    for token in node.tokens.values():
        print(f"Token: {token.token_id} (Type: {token.token_type})")
```

## Testing

The module includes comprehensive test coverage:

- Unit tests for all utility functions
- Integration tests with NodeManager
- Performance tests for caching effectiveness
- Error handling tests for edge cases

Run tests with:
```bash
python -m pytest tests/test_token_utils.py -v
```

## Version History

- **v1.0.0**: Initial implementation with basic token normalization
- **v1.1.0**: Added caching and rate limiting
- **v1.2.0**: Enhanced validation and error handling
- **v1.3.0**: Fixed circular import dependencies
- **v1.4.0**: Added comprehensive documentation and testing

## Future Enhancements

- **Custom Token Types**: Extensible system for adding new token types
- **Performance Metrics**: Built-in performance monitoring
- **Configuration Schema**: JSON schema validation for configuration files
- **Migration Tools**: Automated migration between token format versions