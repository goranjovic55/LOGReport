"""
Retry utilities with exponential backoff and circuit breaker patterns.
"""
import time
import random
import logging
from typing import Callable, Type, Any, Tuple, Optional
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker implementation to prevent cascading failures."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60, 
                 expected_exception: Type[Exception] = Exception):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Time in seconds before attempting to close circuit
            expected_exception: Exception type to monitor
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function through circuit breaker.
        
        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, 
                       max_delay: float = 60.0, backoff_factor: float = 2.0,
                       jitter: bool = True, exceptions: Tuple[Type[Exception], ...] = (Exception,)):
    """
    Decorator for retrying function calls with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Multiplier for delay after each retry
        jitter: Whether to add random jitter to delay
        exceptions: Exception types to retry on
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = base_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {str(e)}")
                        raise e
                    
                    # Calculate delay with optional jitter
                    if jitter:
                        delay_with_jitter = delay * (0.5 + random.random() * 0.5)
                    else:
                        delay_with_jitter = delay
                    
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                                 f"Retrying in {delay_with_jitter:.2f} seconds...")
                    
                    time.sleep(delay_with_jitter)
                    delay = min(delay * backoff_factor, max_delay)
            
            # This should never be reached due to the return in the try block
            # or the raise in the except block, but included for completeness
            raise Exception(f"Function {func.__name__} failed after {max_retries} retries")
        
        return wrapper
    return decorator