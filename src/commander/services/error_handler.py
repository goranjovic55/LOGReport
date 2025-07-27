"""
Error Handler Service - Handles error reporting and logging
"""
import logging
import traceback
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


class ErrorHandler(QObject):
    """Service for handling error reporting and logging"""
    
    # Signal for error reporting
    error_reported = pyqtSignal(str, int)  # message, duration
    
    # Status message durations in milliseconds
    STATUS_MSG_SHORT = 3000    # 3 seconds
    STATUS_MSG_MEDIUM = 5000   # 5 seconds
    STATUS_MSG_LONG = 10000    # 10 seconds
    
    def __init__(self):
        """Initialize the error handler service."""
        super().__init__()
        logging.debug("ErrorHandler initialized")
    
    def report_error(self, message: str, exception: Optional[Exception] = None, duration: Optional[int] = None):
        """
        Report an error with logging and status bar updates.
        
        Args:
            message: Error message to display
            exception: Optional exception that occurred
            duration: Duration to display message in milliseconds (None for default)
        """
        duration = duration or self.STATUS_MSG_MEDIUM
        error_msg = f"{message}: {str(exception)}" if exception else message
        logging.error(error_msg)
        
        # Log full traceback for exceptions
        if exception:
            logging.error(f"Exception traceback: {traceback.format_exc()}")
        
        self.error_reported.emit(error_msg, duration)
    
    def handle_connection_error(self, error: Exception):
        """
        Handle connection errors specifically.
        
        Args:
            error: Connection error that occurred
        """
        error_type = type(error).__name__
        if error_type in ["ConnectionRefusedError", "TimeoutError", "socket.timeout"]:
            self.report_error("Connection error", error, self.STATUS_MSG_MEDIUM)
        else:
            self.report_error("Unexpected connection error", error, self.STATUS_MSG_MEDIUM)
    
    def handle_telnet_error(self, error: Exception):
        """
        Handle telnet-specific errors.
        
        Args:
            error: Telnet error that occurred
        """
        self.report_error("Telnet command failed", error, self.STATUS_MSG_MEDIUM)
        logging.error(f"Telnet command failed", exc_info=True)
    
    def handle_file_error(self, error: Exception, file_path: str):
        """
        Handle file operation errors.
        
        Args:
            error: File error that occurred
            file_path: Path of file being accessed
        """
        self.report_error(f"File operation failed for {file_path}", error, self.STATUS_MSG_MEDIUM)
        logging.error(f"File operation failed for {file_path}", exc_info=True)
    
    def handle_validation_error(self, error: Exception, context: str):
        """
        Handle validation errors.
        
        Args:
            error: Validation error that occurred
            context: Context where validation failed
        """
        self.report_error(f"Validation failed in {context}", error, self.STATUS_MSG_SHORT)
        logging.error(f"Validation failed in {context}", exc_info=True)