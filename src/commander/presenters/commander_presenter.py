"""
Commander Presenter - Handles presentation logic for the commander window
"""
from abc import ABC, abstractmethod
import logging
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal

from ..models import NodeToken
from ..node_manager import NodeManager
from ..session_manager import SessionManager
from ..log_writer import LogWriter
from ..command_queue import CommandQueue
from ..services.fbc_command_service import FbcCommandService
from ..services.rpc_command_service import RpcCommandService
from ..services.context_menu_service import ContextMenuService
from ..services.context_menu_filter import ContextMenuFilterService


class CommanderPresenter(QObject):
    """Presenter for the Commander window, handling presentation logic"""
    
    # Signals for UI updates
    status_message_signal = pyqtSignal(str, int)  # message, duration
    command_finished_signal = pyqtSignal(str, bool)  # response, automatic
    queue_processed_signal = pyqtSignal(int, int)  # success_count, total_count
    
    def __init__(self, view, node_manager: NodeManager, session_manager: SessionManager,
                 log_writer: LogWriter, command_queue: CommandQueue,
                 fbc_service: FbcCommandService, rpc_service: RpcCommandService,
                 context_menu_service: ContextMenuService):
        """
        Initialize the CommanderPresenter.
        
        Args:
            view: The view component (UI) this presenter is associated with
            node_manager: Manager for node operations
            session_manager: Manager for session operations
            log_writer: Writer for log operations
            command_queue: Queue for command execution
            fbc_service: Service for FBC command operations
            rpc_service: Service for RPC command operations
            context_menu_service: Service for context menu operations
        """
        super().__init__()
        self.view = view
        self.node_manager = node_manager
        self.session_manager = session_manager
        self.log_writer = log_writer
        self.command_queue = command_queue
        self.fbc_service = fbc_service
        self.rpc_service = rpc_service
        self.context_menu_service = context_menu_service
        
        # Connect signals
        self.command_queue.command_completed.connect(self._on_command_completed)
        self.command_queue.progress_updated.connect(self._on_queue_progress)
        
        logging.debug("CommanderPresenter initialized")
    
    def _on_command_completed(self, command: str, result: str, success: bool):
        """
        Handle completion of a queued command.
        
        Args:
            command: The command that was executed
            result: The result of the command execution
            success: Whether the command executed successfully
        """
        logging.debug(f"Command completed: {command}, success: {success}")
        # This method can be extended to handle command completion logic
    
    def _on_queue_progress(self, current: int, total: int):
        """
        Handle progress updates from the command queue.
        
        Args:
            current: Number of completed commands
            total: Total number of commands in queue
        """
        logging.debug(f"Queue progress: {current}/{total}")
        # This method can be extended to handle progress updates
    
    def _report_error(self, message: str, exception: Optional[Exception] = None, duration: int = 5000):
        """
        Report an error to the UI.
        
        Args:
            message: Error message to display
            exception: Optional exception that occurred
            duration: Duration to display the message in milliseconds
        """
        error_msg = f"{message}: {str(exception)}" if exception else message
        logging.error(error_msg)
        self.status_message_signal.emit(error_msg, duration)