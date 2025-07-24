"""
Node Tree Presenter - Handles presentation logic for the node tree within the commander window
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


class NodeTreePresenter(QObject):
    """Presenter for the Node Tree, handling presentation logic related to node tree operations"""
    
    # Signals for UI updates
    status_message_signal = pyqtSignal(str, int)  # message, duration
    node_tree_updated_signal = pyqtSignal()  # emitted when node tree is updated
    
    def __init__(self, view, node_manager: NodeManager, session_manager: SessionManager,
                 log_writer: LogWriter, command_queue: CommandQueue,
                 fbc_service: FbcCommandService, rpc_service: RpcCommandService):
        """
        Initialize the NodeTreePresenter.
        
        Args:
            view: The view component (UI) this presenter is associated with
            node_manager: Manager for node operations
            session_manager: Manager for session operations
            log_writer: Writer for log operations
            command_queue: Queue for command execution
            fbc_service: Service for FBC command operations
            rpc_service: Service for RPC command operations
        """
        super().__init__()
        self.view = view
        self.node_manager = node_manager
        self.session_manager = session_manager
        self.log_writer = log_writer
        self.command_queue = command_queue
        self.fbc_service = fbc_service
        self.rpc_service = rpc_service
        
        logging.debug("NodeTreePresenter initialized")
    
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