"""
Error Reporter - Structured error reporting for the Commander application
"""
import logging
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from ..constants import ErrorSeverity

@dataclass
class StructuredError:
    """Structured error representation for consistent error reporting"""
    code: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    severity: ErrorSeverity = ErrorSeverity.ERROR
    timestamp: Optional[float] = None
    trace: Optional[str] = None

class ErrorReporter(ABC):
    """Abstract base class for error reporters"""
    
    @abstractmethod
    def report(self, error: StructuredError) -> None:
        """Report a structured error"""
        pass

class ConsoleErrorReporter(ErrorReporter):
    """Error reporter that outputs to console"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def report(self, error: StructuredError) -> None:
        """Report error to console"""
        log_method = self.logger.error
        if error.severity == ErrorSeverity.CRITICAL:
            log_method = self.logger.critical
        elif error.severity == ErrorSeverity.WARNING:
            log_method = self.logger.warning
        elif error.severity == ErrorSeverity.INFO:
            log_method = self.logger.info
            
        log_method(f"[{error.code}] {error.message}")
        if error.context:
            log_method(f"Context: {error.context}")
        if error.trace:
            log_method(f"Traceback: {error.trace}")

class FileErrorReporter(ErrorReporter):
    """Error reporter that outputs to a file"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.logger = logging.getLogger(__name__)
    
    def report(self, error: StructuredError) -> None:
        """Report error to file"""
        try:
            with open(self.filepath, 'a', encoding='utf-8') as f:
                f.write(f"[{error.timestamp}] [{error.severity.value}] [{error.code}] {error.message}\n")
                if error.context:
                    f.write(f"Context: {error.context}\n")
                if error.trace:
                    f.write(f"Traceback: {error.trace}\n")
                f.write("-" * 50 + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write error to file: {e}")

class CompositeErrorReporter(ErrorReporter):
    """Error reporter that delegates to multiple reporters"""
    
    def __init__(self, reporters: list):
        self.reporters = reporters
    
    def report(self, error: StructuredError) -> None:
        """Report error to all reporters"""
        for reporter in self.reporters:
            try:
                reporter.report(error)
            except Exception as e:
                # Log the failure but don't let it stop other reporters
                logging.getLogger(__name__).error(f"Error reporter failed: {e}")