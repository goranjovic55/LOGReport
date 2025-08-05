"""
Constants Module - Shared constants across the Commander application
"""
from enum import Enum
from typing import Dict, Final

class ErrorSeverity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

STATUS_CODES: Final[Dict[str, int]] = {
    "SUCCESS": 200,
    "PROCESSING": 102,
    "ERROR": 500
}

# Status message durations (milliseconds)
STATUS_MSG_SHORT: Final[int] = 3000
STATUS_MSG_MEDIUM: Final[int] = 5000
STATUS_MSG_LONG: Final[int] = 10000

# Default timeout for operations (seconds)
DEFAULT_TIMEOUT: Final[int] = 30

# Token processing constants
MAX_TOKENS_PER_SECOND: Final[int] = 100