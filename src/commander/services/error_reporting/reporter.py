"""
Error Reporter - Structured error reporting for the Commander application
"""
import logging
import traceback
import time
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from .interface import ErrorReporter, StructuredError
from ...constants import STATUS_MSG_SHORT, STATUS_MSG_MEDIUM, STATUS_MSG_LONG


class ErrorReporterImpl(QObject, ErrorReporter):
    """Concrete implementation of ErrorReporter with Qt signal support"""
    
    # Signal for error reporting to UI
    error_reported = pyqtSignal(str, int)  # message, duration
    
    def __init__(self):
        """Initialize the error reporter.")
        super().__init__()
        logging.debug("ErrorReporterImpl initialized")
    
    def report_error(self, error: StructuredError, duration: Optional[int] = None) -> None:
        """
        Report an error with structured information.
        
        Args:
            error: Structured error information
            duration: Duration to display message in milliseconds (None for default)
        """
        duration = duration or STATUS_MSG_MEDIUM
        
        # Format the error message
        if error.exception:
            error_msg = f"{error.message}: {str(error.exception)}"
        else:
            error_msg = error.message
        
        # Log the error based on severity
        if error.severity == "ERROR":
            logging.error(error_msg)
            # Log full traceback for exceptions
            if error.exception:
                logging.error(f"Exception traceback: {traceback.format_exc()}")
        elif error.severity == "WARNING":
            logging.warning(error_msg)
        else:  # INFO
            logging.info(error_msg)
        
        # Emit signal for UI updates
        self.error_reported.emit(error_msg, duration)
    
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
        # Create a structured error from the simple parameters
        structured_error = StructuredError(
            code="SIMPLE_ERROR",
            message=message,
            exception=exception,
            severity=severity,
            timestamp=time.time()
        )
        
        # Use the structured error reporting method
        self.report_error(structured_error, duration)
        
        return structured_error.ask_try_again()