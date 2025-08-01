"""
Commander Presenter - Handles presentation logic for the commander window
"""
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
    
    def load_configuration(self, file_path: str) -> bool:
        """
        Load node configuration from the specified file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            bool: True if configuration loaded successfully, False otherwise
        """
        try:
            return self.node_manager.load_configuration(file_path)
        except Exception as e:
            self._report_error("Failed to load configuration", e)
            return False
    
    def set_log_root_folder(self, folder_path: str) -> None:
        """
        Set the root folder for log files.
        
        Args:
            folder_path: Path to the log files root folder
        """
        self.node_manager.set_log_root(folder_path)
        # Rescan log files after setting new root
        self.node_manager.scan_log_files()
        # Update the view
        self.populate_node_tree()
    
    def show_context_menu(self, position) -> None:
        """
        Show context menu at the specified position.
        
        Args:
            position: Position where the context menu should be shown
        """
        # This method should delegate to the view to show the context menu
        # The actual implementation is in the view, but the presenter handles the logic
        if hasattr(self.view, 'show_context_menu'):
            self.view.show_context_menu(position)
    
    def populate_node_tree(self) -> None:
        """Populate the node tree with data from the model."""
        # This method should delegate to the view to populate the node tree
        # The actual implementation is in the view, but the presenter handles the logic
        if hasattr(self.view, 'populate_node_tree'):
            self.view.populate_node_tree()
    
    def process_fieldbus_command(self, token_id: str, node_name: str) -> None:
        """
        Process a fieldbus command for the specified token.
        
        Args:
            token_id: ID of the token to process
            node_name: Name of the node containing the token
        """
        # Delegate to FBC service
        self.fbc_service.queue_fieldbus_command(token_id, node_name)
    
    def process_rpc_command(self, node_name: str, token_id: str, action_type: str) -> None:
        """
        Process an RPC command for the specified token.
        
        Args:
            node_name: Name of the node containing the token
            token_id: ID of the token to process
            action_type: Type of action to perform (e.g., 'print', 'clear')
        """
        # Delegate to RPC service
        self.rpc_service.queue_rpc_command(node_name, token_id, action_type)
    
    def on_node_selected(self, item) -> None:
        """
        Handle node/token selection in the view.
        
        Args:
            item: Selected item from the view
        """
        # This method handles the logic when a node is selected in the view
        # The actual UI update is handled by the view
        pass  # Implementation would depend on specific logic needed