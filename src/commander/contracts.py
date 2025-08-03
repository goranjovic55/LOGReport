"""
Interface contracts for the Commander component following MVP pattern.
These interfaces define the contract between the View and Presenter layers.
"""

from abc import ABC, abstractmethod
from typing import Optional
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTreeWidgetItem, QTabWidget


class ICommanderView(ABC):
    """Interface for the Commander Window View component."""
    
    # Signals that the view can emit
    load_nodes_clicked = pyqtSignal()
    set_log_root_clicked = pyqtSignal()
    node_selected = pyqtSignal(object)  # QTreeWidgetItem
    node_double_clicked = pyqtSignal(object, int)  # QTreeWidgetItem, column
    context_menu_requested = pyqtSignal(object)  # QPoint
    
    @abstractmethod
    def show_context_menu(self, position) -> None:
        """
        Show context menu at the specified position.
        
        Args:
            position: Position where the context menu should be shown
        """
        pass
    
    @abstractmethod
    def populate_node_tree(self) -> None:
        """Populate the node tree with data from the model."""
        pass
    
    @abstractmethod
    def clear_terminal(self) -> None:
        """Clear the terminal display."""
        pass
    
    @abstractmethod
    def clear_node_log(self) -> None:
        """Clear the currently selected node's log file."""
        pass
    
    @abstractmethod
    def copy_to_log(self) -> None:
        """Copy current session content to selected token or log file."""
        pass


class ICommanderPresenter(ABC):
    """Interface for the Commander Window Presenter component."""
    
    @abstractmethod
    def load_configuration(self, file_path: str) -> bool:
        """
        Load node configuration from the specified file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            bool: True if configuration loaded successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def set_log_root_folder(self, folder_path: str) -> None:
        """
        Set the root folder for log files.
        
        Args:
            folder_path: Path to the log files root folder
        """
        pass
    
    @abstractmethod
    def show_context_menu(self, position) -> None:
        """
        Show context menu at the specified position.
        
        Args:
            position: Position where the context menu should be shown
        """
        pass
    
    @abstractmethod
    def populate_node_tree(self) -> None:
        """Populate the node tree with data from the model."""
        pass
    
    @abstractmethod
    def process_fieldbus_command(self, token_id: str, node_name: str) -> None:
        """
        Process a fieldbus command for the specified token.
        
        Args:
            token_id: ID of the token to process
            node_name: Name of the node containing the token
        """
        pass
    
    @abstractmethod
    def process_rpc_command(self, node_name: str, token_id: str, action_type: str) -> None:
        """
        Process an RPC command for the specified token.
        
        Args:
            node_name: Name of the node containing the token
            token_id: ID of the token to process
            action_type: Type of action to perform (e.g., 'print', 'clear')
        """
        pass
    
    @abstractmethod
    def on_node_selected(self, item: QTreeWidgetItem, current_token=None) -> None:
        """
        Handle node/token selection in the view.
        
        Args:
            item: Selected item from the view
            current_token: Current token if available
        """
        pass
    
    @abstractmethod
    def copy_to_log(self, selected_items, session_tabs: QTabWidget) -> None:
        """
        Copies current session content to selected token or log file.
        
        Args:
            selected_items: Selected items from the view
            session_tabs: Session tabs from the view
        """
        pass
    
    @abstractmethod
    def clear_terminal(self) -> None:
        """Clear the terminal display."""
        pass
    
    @abstractmethod
    def clear_node_log(self, selected_items) -> None:
        """Clear the currently selected node's log file."""
        pass
    
    @abstractmethod
    def open_log_file(self, item: QTreeWidgetItem, column: int) -> bool:
        """
        Opens log file when double-clicked in tree view.
        
        Args:
            item: The item that was double-clicked
            column: The column that was clicked
            
        Returns:
            bool: True if file was opened successfully, False otherwise
        """
        pass