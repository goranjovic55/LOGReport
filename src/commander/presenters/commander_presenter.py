"""
Commander Presenter - Handles presentation logic for the commander window
"""
import logging
import os
from typing import Optional, List
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QTabWidget, QTextEdit, 
    QVBoxLayout, QWidget, QPushButton, QFileDialog
)
from PyQt6.QtCore import Qt

from ..models import NodeToken
from ..node_manager import NodeManager
from ..session_manager import SessionManager
from ..log_writer import LogWriter
from ..command_queue import CommandQueue
from ..services.fbc_command_service import FbcCommandService
from ..services.rpc_command_service import RpcCommandService
from ..services.context_menu_service import ContextMenuService
from ..services.context_menu_filter import ContextMenuFilterService
from ..widgets import ConnectionBar, ConnectionState
from ..services.status_service import StatusService
from ..ui.commander_ui_factory import CommanderUIFactory
from .commander_presenter_utils import CommanderPresenterUtils


class CommanderPresenter(QObject):
    """Presenter for the Commander window, handling presentation logic"""
    
    # Signals for UI updates
    status_message_signal = pyqtSignal(str, int)  # message, duration
    set_cmd_input_text_signal = pyqtSignal(str)
    update_connection_status_signal = pyqtSignal(ConnectionState)
    switch_to_telnet_tab_signal = pyqtSignal()
    set_cmd_focus_signal = pyqtSignal()
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
        
        # UI factory for creating UI components
        self.ui_factory = CommanderUIFactory()
        
        # Create main layout to initialize UI components
        self.main_widget = self.ui_factory.create_main_layout()
        
        # Expose UI components
        self.node_tree_view = self.ui_factory.node_tree_view
        self.session_tabs = self.ui_factory.session_tabs
        self.telnet_tab = self.ui_factory.telnet_tab
        self.vnc_tab = self.ui_factory.vnc_tab
        self.ftp_tab = self.ui_factory.ftp_tab
        self.telnet_output = self.ui_factory.telnet_output
        self.cmd_input = self.ui_factory.cmd_input
        self.execute_btn = self.ui_factory.execute_btn
        self.copy_to_log_btn = self.ui_factory.copy_to_log_btn
        self.clear_terminal_btn = self.ui_factory.clear_terminal_btn
        self.clear_node_log_btn = self.ui_factory.clear_node_log_btn
        self.telnet_connection_bar = self.ui_factory.telnet_connection_bar
        
        # Utility class for helper functions
        self.utils = CommanderPresenterUtils(node_manager, log_writer)
        
        logging.debug("CommanderPresenter initialized")
    
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
    
    def load_configuration(self) -> None:
        """Load node configuration from selected file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "Select Node Configuration File",
            "",
            "JSON Files (*.json)"
        )
        if file_path:
            try:
                if self.node_manager.load_configuration(file_path):
                    self.node_manager.scan_log_files()
                    # Update the view
                    self.populate_node_tree()
                    self.status_message_signal.emit("Configuration loaded successfully", 3000)
                else:
                    self.status_message_signal.emit("Failed to load configuration", 5000)
            except Exception as e:
                self._report_error("Failed to load configuration", e)
    
    def set_log_root_folder(self) -> None:
        """Set the root folder for log files."""
        folder_path = QFileDialog.getExistingDirectory(
            self.view,
            "Select Log Files Root Folder",
            ""
        )
        if folder_path:
            try:
                self.node_manager.set_log_root(folder_path)
                # Rescan log files after setting new root
                self.node_manager.scan_log_files()
                # Update the view
                self.populate_node_tree()
                self.status_message_signal.emit("Log root folder set successfully", 3000)
            except Exception as e:
                self._report_error("Failed to set log root folder", e)
    
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
    
    def on_node_selected(self, item, current_token) -> None:
        """
        Handle node/token selection in the view.
        
        Args:
            item: Selected item from the view
            current_token: Current token if available
        """
        # This method handles the logic when a node is selected in the view
        # The actual UI update is handled by the view
        pass  # Implementation would depend on specific logic needed
    
    def copy_to_log(self, selected_items, session_tabs: QTabWidget) -> None:
        """
        Copies current session content to selected token or log file.
        
        Args:
            selected_items: Selected items from the view
            session_tabs: Session tabs from the view
        """
        self.utils.copy_to_log(selected_items, session_tabs, self.status_message_signal)
    
    def clear_terminal(self) -> None:
        """Clear the terminal display."""
        # Assuming telnet_output is accessible through the view
        self.view.telnet_output.clear()
    
    def clear_node_log(self, selected_items) -> None:
        """Clear the currently selected node's log file."""
        self.utils.clear_node_log(selected_items, self.status_message_signal)
    
    def open_log_file(self, item: QTreeWidgetItem, column: int) -> bool:
        """
        Opens log file when double-clicked in tree view.
        
        Args:
            item: The item that was double-clicked
            column: The column that was clicked
            
        Returns:
            bool: True if file was opened successfully, False otherwise
        """
        return self.utils.open_log_file(item, column, self.status_message_signal)
    
    def create_main_layout(self) -> QWidget:
        """Create the main layout for the window."""
        return self.main_widget
    
    
    def handle_queue_processed(self, success_count, total_count, status_service):
        """
        Handle queue processing completion.
        
        Args:
            success_count: Number of successful commands
            total_count: Total number of commands
            status_service: Status service instance
        """
        self.utils.handle_queue_processed(success_count, total_count, status_service, self.status_message_signal)