import re
import logging

logger = logging.getLogger(__name__)

# Define regex patterns for actual error responses
ERROR_PATTERNS = [
    # General error patterns
    re.compile(r'\berror\b', re.IGNORECASE),
    re.compile(r'\bfailure\b', re.IGNORECASE),
    re.compile(r'\bexception\b', re.IGNORECASE),
    re.compile(r'\btimeout\b', re.IGNORECASE),
    re.compile(r'\bnot found\b', re.IGNORECASE),
    re.compile(r'\bnot supported\b', re.IGNORECASE),
    re.compile(r'\binvalid\b', re.IGNORECASE),
    re.compile(r'\bunknown\b', re.IGNORECASE),
    
    # Specific error message patterns
    re.compile(r'command not found', re.IGNORECASE),
    re.compile(r'syntax error', re.IGNORECASE),
    re.compile(r'permission denied', re.IGNORECASE),
    re.compile(r'access denied', re.IGNORECASE),
    re.compile(r'connection refused', re.IGNORECASE),
    re.compile(r'connection failed', re.IGNORECASE),
    re.compile(r'connection timeout', re.IGNORECASE),
    re.compile(r'network error', re.IGNORECASE),
    re.compile(r'authentication failed', re.IGNORECASE),
    re.compile(r'login failed', re.IGNORECASE),
    
    # Error codes
    re.compile(r'error\s*\d+', re.IGNORECASE),
    re.compile(r'err\s*\d+', re.IGNORECASE),
]

# Define patterns for valid responses that should NOT be considered errors
VALID_RESPONSE_PATTERNS = [
    # The specific case mentioned in the issue
    re.compile(r'int from fbc rupi counters \d+', re.IGNORECASE),
    
    # Other valid response patterns
    re.compile(r'\bok\b', re.IGNORECASE),
    re.compile(r'\bsuccess\b', re.IGNORECASE),
    re.compile(r'\bcompleted\b', re.IGNORECASE),
    re.compile(r'\bdone\b', re.IGNORECASE),
    re.compile(r'\bfinished\b', re.IGNORECASE),
]

def is_error_response(response: str) -> bool:
    """
    Determine if a response is an actual error or a valid response.
    
    Args:
        response (str): The response string to check
        
    Returns:
        bool: True if the response is an error, False otherwise
    """
    if not response:
        return False
        
    # First check if it's a valid response that should not be considered an error
    for pattern in VALID_RESPONSE_PATTERNS:
        if pattern.search(response):
            logger.debug(f"Response identified as valid: {response[:100]}...")
            return False
    
    # Then check if it matches any error patterns
    for pattern in ERROR_PATTERNS:
        if pattern.search(response):
            logger.debug(f"Response identified as error: {response[:100]}...")
            return True
            
    # If no patterns match, it's not an error
    logger.debug(f"Response identified as non-error: {response[:100]}...")
    return False