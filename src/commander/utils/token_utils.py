"""
Token Utilities - Provides optimized token handling and normalization functions
"""
import re
import logging
from functools import lru_cache
from typing import Optional, Pattern, Union
from ..constants import TOKEN_PATTERN


class TokenValidator:
    """Validates and normalizes token identifiers"""
    
    def __init__(self):
        """Initialize the token validator"""
        logging.debug("TokenValidator initialized")
    
    @lru_cache(maxsize=128)
    def normalize_token(self, token: str) -> str:
        """
        Normalize a token string with caching for performance.
        Special handling for FBC tokens to maintain compatibility with existing behavior.
        
        Args:
            token: Raw token string to normalize
            
        Returns:
            str: Normalized token string
        """
        if not isinstance(token, str):
            raise TypeError("Token must be a string")
        
        # Remove any whitespace
        token = token.strip()
        
        # Check if this is an FBC token and apply special normalization
        if self.is_fbc_token(token):
            # For FBC tokens: pad numeric IDs with zeros, convert alphanumeric to uppercase
            if token.isdigit():
                token = token.zfill(3)
            else:
                token = token.upper()
            return token
        
        # For non-FBC tokens: convert to lowercase and remove non-alphanumeric
        token = token.lower()
        token = re.sub(r'[^a-z0-9]', '', token)
        
        # For numeric tokens, pad with leading zeros to make it 3 digits
        if token.isdigit() and len(token) < 3:
            token = token.zfill(3)
        
        return token
    
    def validate_token(self, token: str) -> bool:
        """
        Validate a token against the standard pattern.
        
        Args:
            token: Token string to validate
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        if not isinstance(token, str):
            return False
            
        return bool(TOKEN_PATTERN.match(token))
    
    def is_fbc_token(self, token: str) -> bool:
        """
        Check if a token is an FBC token (3 digits followed by optional lowercase letter).
        
        Args:
            token: Token string to check
            
        Returns:
            bool: True if token is FBC type, False otherwise
        """
        if not self.validate_token(token):
            return False
            
        # FBC tokens are 3 digits followed by optional lowercase letter
        return bool(re.match(r'^\d{3}[a-z]?$', token))
    
    def is_rpc_token(self, token: str) -> bool:
        """
        Check if a token is an RPC token (alphanumeric).
        
        Args:
            token: Token string to check
            
        Returns:
            bool: True if token is RPC type, False otherwise
        """
        if not self.validate_token(token):
            return False
            
        # RPC tokens are alphanumeric
        return bool(re.match(r'^[a-z0-9]+$', token)) and not self.is_fbc_token(token)

    def validate_token_node(self, token, node_name: str = None) -> bool:
        """
        Validate that a token's node information is valid.
        
        Args:
            token: NodeToken to validate
            node_name: Optional node name to validate against
            
        Returns:
            bool: True if node information is valid, False otherwise
        """
        # Validate token has required attributes
        if not hasattr(token, 'ip_address') or not hasattr(token, 'token_id'):
            logging.error(f"Token missing required attributes: {token}")
            return False
            
        # Validate IP address format
        if not token.ip_address or not isinstance(token.ip_address, str):
            logging.error(f"Invalid IP address for token {token.token_id}: {token.ip_address}")
            return False
            
        # Validate node name if provided
        if node_name and hasattr(token, 'name') and token.name != node_name:
            logging.error(f"Token node name mismatch: expected {node_name}, got {token.name}")
            return False
            
        return True


class TokenRateLimiter:
    """Rate limiter for token processing operations"""
    
    def __init__(self, max_tokens_per_second: int = 100):
        """
        Initialize the rate limiter.
        
        Args:
            max_tokens_per_second: Maximum number of tokens to process per second
        """
        self.max_tokens_per_second = max_tokens_per_second
        self.token_count = 0
        self.last_reset_time = None
        logging.debug(f"TokenRateLimiter initialized with max_tokens_per_second={max_tokens_per_second}")
    
    def is_allowed(self) -> bool:
        """
        Check if processing a token is allowed under rate limits.
        
        Returns:
            bool: True if allowed, False if rate limit exceeded
        """
        import time
        
        current_time = time.time()
        
        # Reset counter every second
        if self.last_reset_time is None or current_time - self.last_reset_time >= 1.0:
            self.token_count = 0
            self.last_reset_time = current_time
        
        # Check if we're under the limit
        if self.token_count < self.max_tokens_per_second:
            self.token_count += 1
            return True
        
        return False
    
    def get_wait_time(self) -> float:
        """
        Get the time to wait before processing the next token.
        
        Returns:
            float: Time in seconds to wait
        """
        if self.last_reset_time is None:
            return 0.0
            
        import time
        current_time = time.time()
        time_since_reset = current_time - self.last_reset_time
        
        if time_since_reset < 1.0:
            return 1.0 - time_since_reset
        return 0.0


# Create singleton instances for global use
token_validator = TokenValidator()
token_rate_limiter = TokenRateLimiter()


def normalize_token(token: str) -> str:
    """
    Normalize a token string using the singleton validator.
    
    Args:
        token: Raw token string to normalize
        
    Returns:
        str: Normalized token string
    """
    return token_validator.normalize_token(token)


def validate_token(token: str) -> bool:
    """
    Validate a token using the singleton validator.
    
    Args:
        token: Token string to validate
        
    Returns:
        bool: True if token is valid, False otherwise
    """
    return token_validator.validate_token(token)


def is_fbc_token(token: str) -> bool:
    """
    Check if a token is an FBC token using the singleton validator.
    
    Args:
        token: Token string to check
        
    Returns:
        bool: True if token is FBC type, False otherwise
    """
    return token_validator.is_fbc_token(token)


def is_rpc_token(token: str) -> bool:
    """
    Check if a token is an RPC token using the singleton validator.
    
    Args:
        token: Token string to check
        
    Returns:
        bool: True if token is RPC type, False otherwise
    """
    return token_validator.is_rpc_token(token)


def validate_token_node(token, node_name: str = None) -> bool:
    """
    Validate that a token's node information is valid.
    
    Args:
        token: NodeToken to validate
        node_name: Optional node name to validate against
        
    Returns:
        bool: True if node information is valid, False otherwise
    """
    return token_validator.validate_token_node(token, node_name)


def is_token_processing_allowed() -> bool:
    """
    Check if token processing is allowed under rate limits.
    
    Returns:
        bool: True if allowed, False if rate limit exceeded
    """
    return token_rate_limiter.is_allowed()


def get_token_processing_wait_time() -> float:
    """
    Get the time to wait before processing the next token.
    
    Returns:
        float: Time in seconds to wait
    """
    return token_rate_limiter.get_wait_time()