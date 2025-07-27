"""
Status Service - Handles unified messaging and status updates
"""
import logging
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


class StatusService(QObject):
    """Service for handling unified status messaging"""
    
    # Signal for status updates
    status_updated = pyqtSignal(str, int)  # message, duration
    
    # Status message durations in milliseconds
    STATUS_MSG_SHORT = 3000    # 3 seconds
    STATUS_MSG_MEDIUM = 5000   # 5 seconds
    STATUS_MSG_LONG = 10000    # 10 seconds
    
    def __init__(self):
        """Initialize the status service."""
        super().__init__()
        logging.debug("StatusService initialized")
    
    def show_status(self, message: str, duration: Optional[int] = None):
        """
        Show a status message.
        
        Args:
            message: Message to display
            duration: Duration to display message in milliseconds (None for default)
        """
        if duration is None:
            duration = self.STATUS_MSG_SHORT
        self.status_updated.emit(message, duration)
    
    def show_error(self, message: str, exception: Optional[Exception] = None, duration: Optional[int] = None):
        """
        Show an error message.
        
        Args:
            message: Error message to display
            exception: Optional exception that occurred
            duration: Duration to display message in milliseconds (None for default)
        """
        error_msg = f"{message}: {str(exception)}" if exception else message
        logging.error(error_msg)
        if duration is None:
            duration = self.STATUS_MSG_MEDIUM
        self.status_updated.emit(error_msg, duration)
    
    def show_success(self, message: str, duration: Optional[int] = None):
        """
        Show a success message.
        
        Args:
            message: Success message to display
            duration: Duration to display message in milliseconds (None for default)
        """
        if duration is None:
            duration = self.STATUS_MSG_SHORT
        self.status_updated.emit(message, duration)
    
    def show_info(self, message: str, duration: Optional[int] = None):
        """
        Show an info message.
        
        Args:
            message: Info message to display
            duration: Duration to display message in milliseconds (None for default)
        """
        if duration is None:
            duration = self.STATUS_MSG_SHORT
        self.status_updated.emit(message, duration)