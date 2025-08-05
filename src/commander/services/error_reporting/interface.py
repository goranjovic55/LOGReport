"""
Error Reporting Interface - Abstract base classes and data structures for error handling
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any
import logging


@dataclass
class StructuredError:
    """Data class for structured error information"""
    code: str
    message: str
    context: Optional[dict] = None
    exception: Optional[Exception] = None
    severity: str = "ERROR"  # ERROR, WARNING, INFO
    timestamp: Optional[float] = None


class ErrorReporter(ABC):
    """Abstract base class for error reporting"""
    
    @abstractmethod
    def report_error(self, error: StructuredError, duration: Optional[int] = None) -> None:
        """
        Report an error with structured information.
        
        Args:
            error: Structured error information
            duration: Duration to display message in milliseconds (None for default)
        """
        pass
    
    @abstractmethod
    def report_simple_error(self, message: str, exception: Optional[Exception] = None, 
                           duration: Optional[int] = None, severity: str = "ERROR") -> None:
        """
        Report a simple error message.
        
        Args:
            message: Error message to display
            exception: Optional exception that occurred
            duration: Duration to display message in milliseconds (None for default)
            severity: Severity level (ERROR, WARNING, INFO)
        """
        pass