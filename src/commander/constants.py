"""
Constants Module - Shared constants for the Commander application
"""
from enum import Enum
import re
from typing import Dict, Final

class ErrorSeverity(Enum):
    """Error severity levels"""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"

# Status message durations in milliseconds
STATUS_MSG_SHORT: Final[int] = 3000    # 3 seconds
STATUS_MSG_MEDIUM: Final[int] = 5000   # 5 seconds
STATUS_MSG_LONG: Final[int] = 10000    # 10 seconds

# Default timeout for network operations in seconds
DEFAULT_TIMEOUT: Final[int] = 30

# Token processing constants
MAX_TOKENS_PER_SECOND: Final[int] = 100
TOKEN_PATTERN: Final[re.Pattern] = re.compile(r'^[a-zA-Z0-9]+$')

# HTTP status codes mapping
STATUS_CODES: Final[Dict[str, int]] = {
    "OK": 200,
    "CREATED": 201,
    "ACCEPTED": 202,
    "NO_CONTENT": 204,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "METHOD_NOT_ALLOWED": 405,
    "REQUEST_TIMEOUT": 408,
    "INTERNAL_SERVER_ERROR": 500,
    "NOT_IMPLEMENTED": 501,
    "BAD_GATEWAY": 502,
    "SERVICE_UNAVAILABLE": 503,
    "GATEWAY_TIMEOUT": 504
}