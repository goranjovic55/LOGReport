"""
Commander Presenter Utilities - Helper functions for the Commander presenter
"""
import os
import logging
from typing import List
from PyQt6.QtWidgets import QTreeWidgetItem, QTabWidget, QTextEdit
from PyQt6.QtCore import Qt

from ..models import NodeToken
from ..node_manager import NodeManager
from ..log_writer import LogWriter
from ..services.status_service import StatusService


class CommanderPresenterUtils:
    """Utility class for the Commander presenter"""
    
    def __init__(self, node_manager: NodeManager, log_writer: LogWriter):
        self.node_manager = node_manager
        self.log_writer = log_writer
    
    def copy_to_log(self, selected_items, session_tabs: QTabWidget, status_message_signal) -> None:
        """
        Copies current session content to selected token or log file.
        
        Args:
            selected_items: Selected items from the view
            session_tabs: Session tabs from the view
            status_message_signal: Signal to emit status messages
        """
        if not selected_items:
            status_message_signal.emit("No item selected! Select a token or log file on the left.", 3000)
            return
        item = selected_items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            status_message_signal.emit("Selected item has no data", 3000)
            return
            
        tab_index = session_tabs.currentIndex()
        session_type = session_tabs.tabText(tab_index)
        
        try:
            # Get session content
            if session_type == "Telnet":
                # This would need to be passed from the presenter
                # For now, we'll assume it's accessible through the view
                content = ""
            else:
                tab_widget = session_tabs.widget(tab_index)
                content_widget = tab_widget.layout().itemAt(0).widget()
                if isinstance(content_widget, QTextEdit):
                    content = content_widget.toPlainText()
                else:
                    return

            if not content:
                status_message_signal.emit("No content in current session", 3000)
                return

            # Handle based on item type
            if "log_path" in data:
                log_path = data["log_path"]
                # Write directly to the file
                with open(log_path, 'a') as f:
                    f.write(content + "\n")
                filename = os.path.basename(log_path)
                status_message_signal.emit(f"Content copied to {filename}", 3000)

            elif "token" in data:
                token_id = data["token"]
                node_name = data.get("node")
                token_type = data.get("token_type")
                if not node_name or not token_type:
                    status_message_signal.emit("Token item missing node or token_type", 3000)
                    return

                node = self.node_manager.get_node(node_name)
                if not node:
                    status_message_signal.emit(f"Node {node_name} not found", 3000)
                    return

                # Reconstruct the log path for display
                ip = node.ip_address.replace('.', '-')
                log_dir = os.path.join(self.node_manager.log_root, token_type, node_name)
                filename = f"{node_name}_{ip}_{token_id}.{token_type.lower()}"
                # Write using the log_writer
                self.log_writer.append_to_log(token_id, content, source=session_type)
                status_message_signal.emit(f"Content copied to {filename}", 3000)

            else:
                status_message_signal.emit("Unsupported item type", 3000)

        except Exception as e:
            status_message_signal.emit(f"Log write error: {str(e)}", 5000)
    
    def clear_node_log(self, selected_items, status_message_signal) -> None:
        """Clear the currently selected node's log file."""
        if not selected_items:
            status_message_signal.emit("No item selected! Select a token or log file on the left.", 3000)
            return
        item = selected_items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            status_message_signal.emit("Selected item has no data", 3000)
            return
            
        try:
            if "log_path" in data:
                log_path = data["log_path"]
                # Clear the file
                with open(log_path, 'w') as f:
                    f.write("")
                filename = os.path.basename(log_path)
                status_message_signal.emit(f"Cleared log file: {filename}", 3000)
            elif "token" in data:
                token_id = data["token"]
                # Clear using the log_writer
                self.log_writer.clear_log(token_id)
                status_message_signal.emit(f"Cleared log for token: {token_id}", 3000)
            else:
                status_message_signal.emit("Unsupported item type", 3000)
        except Exception as e:
            status_message_signal.emit(f"Error clearing log: {str(e)}", 5000)
    
    def open_log_file(self, item: QTreeWidgetItem, column: int, status_message_signal) -> bool:
        """
        Opens log file when double-clicked in tree view.
        
        Args:
            item: The item that was double-clicked
            column: The column that was clicked
            status_message_signal: Signal to emit status messages
            
        Returns:
            bool: True if file was opened successfully, False otherwise
        """
        if data := item.data(0, Qt.ItemDataRole.UserRole):
            # All log items stored their path in "log_path"
            if "log_path" in data:
                log_path = data["log_path"]
                
                # Use system default application to open the log file
                try:
                    os.startfile(log_path)  # Windows-specific
                    status_message_signal.emit(f"Opened log file: {os.path.basename(log_path)}", 3000)
                    return True
                except Exception as e:
                    status_message_signal.emit(f"Error opening file: {str(e)}", 5000)
                return True
        return False
    
    def handle_queue_processed(self, success_count, total_count, status_service: StatusService, status_message_signal):
        """
        Handle queue processing completion.
        
        Args:
            success_count: Number of successful commands
            total_count: Total number of commands
            status_service: Status service instance
            status_message_signal: Signal to emit status messages
        """
        if success_count == total_count:
            status_message_signal.emit(f"Successfully processed {success_count} commands", 3000)
        else:
            status_message_signal.emit(f"Processed {success_count}/{total_count} commands successfully", 5000)