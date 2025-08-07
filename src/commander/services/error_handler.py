"""
Error Handler Service - Handles error reporting and logging
"""
import logging
import traceback
from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal
from .error_reporting.interface import StructuredError


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
    
    def report_error(self, message: str, exception: Optional[Exception] = None, duration: Optional[int] = None,
                    token_context: Optional[Dict[str, Any]] = None):
        """
        Report an error with standardized logging and status bar updates.
        
        Args:
            message: Error message to display
            exception: Optional exception that occurred
            duration: Duration to display message in milliseconds (None for default)
            token_context: Optional context about the token being processed
        """
        # Create structured error
        structured_error = StructuredError(
            code="GENERIC_ERROR",
            message=message,
            exception=exception,
            severity="ERROR",
            timestamp=time.time(),
            token_context=token_context
        )
        
        # Format error message with token context if available
        error_msg = self._format_error_message(structured_error)
        
        # Log the error
        if exception:
            logging.error(error_msg, exc_info=True)
        else:
            logging.error(error_msg)
        
        # Emit signal for UI updates
        self.error_reported.emit(error_msg, duration or self.STATUS_MSG_MEDIUM)
        return structured_error

    def _format_error_message(self, error: StructuredError) -> str:
        """Format error message with standardized structure"""
        base_msg = f"[{error.severity}] {error.message}"
        
        if error.exception:
            base_msg += f": {str(error.exception)}"
            
        if error.token_context:
            context_parts = []
            if "token_id" in error.token_context:
                context_parts.append(f"Token ID: {error.token_context['token_id']}")
            if "node_name" in error.token_context:
                context_parts.append(f"Node: {error.token_context['node_name']}")
            if "token_type" in error.token_context:
                context_parts.append(f"Type: {error.token_context['token_type']}")
                
            if context_parts:
                base_msg += " | " + ", ".join(context_parts)
                
        return base_msg
    
    def handle_connection_error(self, error: Exception):
        """
        Handle connection errors specifically.
        
        Args:
            error: Connection error that occurred
        """
        error_type = type(error).__name__
        if error_type in ["ConnectionRefusedError", "TimeoutError", "socket.timeout"]:
            return self.report_error("Connection error", error, self.STATUS_MSG_MEDIUM)
        else:
            return self.report_error("Unexpected connection error", error, self.STATUS_MSG_MEDIUM)
    
    def handle_circuit_breaker_triggered(self, token_context: Dict[str, Any]):
        """
        Handle circuit breaker activation with token-specific context.
        
        Args:
            token_context: Context about the token that triggered the circuit breaker
        """
        message = "Circuit breaker activated to prevent system overload"
        return self.report_error(message, None, self.STATUS_MSG_LONG, token_context)
    
    def handle_telnet_error(self, error: Exception):
        """
        Handle telnet-specific errors.
        
        Args:
            error: Telnet error that occurred
        """
        self.report_error("Telnet command failed", error, self.STATUS_MSG_MEDIUM)
        logging.error(f"Telnet command failed", exc_info=True)
        return self.report_error("Telnet command failed", error, self.STATUS_MSG_MEDIUM)
    
    def validate_telnet_client_reuse(self, client, token_context: Dict[str, Any]):
        """
        Validate Telnet client before reuse in error scenarios.
        
        Args:
            client: Telnet client to validate
            token_context: Context about the token being processed
            
        Returns:
            bool: True if client is valid for reuse, False otherwise
        """
        if not client:
            error = ValueError("Telnet client is None")
            self.report_error("Cannot reuse invalid Telnet client", error,
                             self.STATUS_MSG_SHORT, token_context)
            return False
            
        try:
            # Test basic connection
            client.write(b"\n")
            response = client.read_until(b">", 1)
            if b"error" in response.lower():
                error = ConnectionError("Client in error state")
                self.report_error("Telnet client in error state", error,
                                 self.STATUS_MSG_SHORT, token_context)
                return False
            return True
        except Exception as e:
            self.report_error("Telnet client validation failed", e,
                             self.STATUS_MSG_SHORT, token_context)
            return False
    
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