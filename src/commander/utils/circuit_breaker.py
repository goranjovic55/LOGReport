"""
Circuit Breaker Pattern Implementation
"""
import logging
import time
from enum import Enum
from typing import Callable, Any, Optional
from threading import Lock
from ..constants import ErrorSeverity


class CircuitState(Enum):
    """Enumeration of circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker implementation for protecting external service calls"""
    
    def __init__(self, 
                 failure_threshold: int = 3,
                 timeout: int = 60,
                 expected_exception: type = Exception):
        """
        Initialize the circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Timeout in seconds before attempting to close circuit
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.lock = Lock()
        
        logging.debug(f"CircuitBreaker initialized with threshold={failure_threshold}, timeout={timeout}")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function call
            
        Raises:
            Exception: If the circuit is open or the function fails
        """
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise Exception("Circuit breaker is OPEN")
            
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure(e)
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit"""
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time >= self.timeout
    
    def _on_success(self):
        """Handle successful function execution"""
        with self.lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                logging.info("Circuit breaker CLOSED after successful call")
    
    def _on_failure(self, exception: Exception):
        """Handle function execution failure"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logging.warning(f"Circuit breaker OPENED after {self.failure_count} failures")
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logging.warning("Circuit breaker OPENED after failure in HALF_OPEN state")
    
    def get_state(self) -> CircuitState:
        """Get the current state of the circuit breaker"""
        return self.state
    
    def get_failure_count(self) -> int:
        """Get the current failure count"""
        return self.failure_count
    
    def reset(self):
        """Reset the circuit breaker to CLOSED state"""
        with self.lock:
            self.failure_count = 0
            self.last_failure_time = None
            self.state = CircuitState.CLOSED
            logging.debug("Circuit breaker manually reset to CLOSED")