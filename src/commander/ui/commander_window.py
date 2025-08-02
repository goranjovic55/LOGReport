from ..models import NodeToken
from ..services.fbc_command_service import FbcCommandService
from ..services.rpc_command_service import RpcCommandService
from ..services.context_menu_filter import ContextMenuFilterService
from ..services.context_menu_service import ContextMenuService
from ..services.commander_service import CommanderService
from ..services.telnet_service import TelnetService
from ..services.logging_service import LoggingService
from ..services.status_service import StatusService
from ..presenters.node_tree_presenter import NodeTreePresenter
from .node_tree_view import NodeTreeView
import sys
import os
import logging
import socket
import re
import glob
from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget, QHBoxLayout,
    QPushButton, QStatusBar, QLabel, QLineEdit, QGridLayout
)
from PyQt6.QtCore import Qt, QSize, QSettings
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QFont, QIcon, QTextCursor

# Enum for connection states
from ..widgets import ConnectionBar, ConnectionState

# Import our components
from ..node_manager import NodeManager
from ..session_manager import SessionManager, SessionType, SessionConfig
from ..log_writer import LogWriter
from ..commands.telnet_commands import CommandResolver, CommandHistory
from ..command_queue import CommandQueue
from ..icons import get_node_online_icon, get_node_offline_icon, get_token_icon

# Centralized Qt application initialization
from ..qt_init import initialize_qt

import time

class CommanderWindow(QMainWindow):
    """Main Commander window."""
    
    
    # Compiled regex patterns for token extraction
    FBC_TOKEN_PATTERN = re.compile(r"^([\w-]+)_[\d\.-]+_([\w-]+)\.")
    RPC_TOKEN_PATTERN = re.compile(r"_([\d\w-]+)\.[^.]*$")  # Matches last _token.extension
    LIS_TOKEN_PATTERN = re.compile(r"^([\w-]+)_[\d-]+_([\d\w-]+)\.lis$")
    
    # Node tree presenter instance
    node_tree_presenter = None
    
    """Main Commander window."""
    
    # Signal for telnet command completion: (response, automatic)
    command_finished = pyqtSignal(str, bool)
    queue_processed = pyqtSignal(int, int)  # Success count, total
    
    set_cmd_input_text_signal = pyqtSignal(str)
    update_connection_status_signal = pyqtSignal(ConnectionState)
    switch_to_telnet_tab_signal = pyqtSignal()
    set_cmd_focus_signal = pyqtSignal()
        
            
    def process_fieldbus_command(self, token_id, node_name):
        """Process fieldbus command with optimized error handling"""
        self.commander_service.process_fieldbus_command(token_id, node_name)
            
    def process_rpc_command(self, node_name, token_id, action_type):
        """Process RPC commands with token validation and auto-execute"""
        self.commander_service.process_rpc_command(node_name, token_id, action_type)
        
    def on_queue_processed(self, success_count, total_count):
        """Handle queue processing completion"""
        if success_count == total_count:
            self.status_service.show_success(f"Successfully processed {success_count} commands")
        else:
            self.status_service.show_status(f"Processed {success_count}/{total_count} commands successfully", StatusService.STATUS_MSG_MEDIUM)
            
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Commander LogCreator v1.0")
        self.setMinimumSize(1200, 800)
        
        # Configure logging to handle Unicode characters
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            encoding='utf-8'
        )
        
        # Load application settings
        self.settings = QSettings("CommanderLogCreator", "Settings")
        
        # Core components needed for services
        self.node_manager = NodeManager()
        self.session_manager = SessionManager()
        self.command_queue = CommandQueue(self.session_manager, parent=self)
        
        # Initialize Status Service
        self.status_service = StatusService()
        self.status_service.status_updated.connect(self.statusBar().showMessage)
        
        # Initialize context menu filter service
        self.context_menu_filter = ContextMenuFilterService()
        
        # Initialize context menu service
        self.context_menu_service = ContextMenuService(self.node_manager, self.context_menu_filter)
        
        # Direct connection for logging command responses
        self.command_queue.command_completed.connect(self._log_command_result)
        
        # Core components
        self.log_writer = LogWriter(self.node_manager)
        
        # Initialize Logging Service in commander_service instead
        # self.logging_service = LoggingService(self.node_manager, self.log_writer)
        
        # Initialize FBC Command Service
        self.fbc_service = FbcCommandService(self.node_manager, self.command_queue, self.log_writer, self)
        
        # Initialize RPC Command Service
        self.rpc_service = RpcCommandService(self.node_manager, self.command_queue, self)
        
        # Initialize Commander Service
        self.commander_service = CommanderService(
            self.node_manager,
            self.session_manager,
            self.command_queue,
            self.log_writer,
            self.fbc_service,
            self.rpc_service
        )
        self.commander_service.set_cmd_input_text.connect(self.set_cmd_input_text_signal)
        self.commander_service.switch_to_telnet_tab.connect(self.switch_to_telnet_tab_signal)
        self.commander_service.focus_command_input.connect(self.set_cmd_focus_signal)
        self.commander_service.status_message.connect(self.status_service.status_updated)
        self.commander_service.report_error.connect(lambda msg: self.logging_service.report_error("Commander Service Error", Exception(msg)))
        self.commander_service.command_finished.connect(self.on_telnet_command_finished)
        self.commander_service.queue_processed.connect(self.on_queue_processed)
        
        # Initialize Telnet Service
        self.telnet_service = TelnetService(self.session_manager)
        self.telnet_service.status_message_signal = self.status_service.status_updated
        self.telnet_service.command_finished_signal = self.command_finished
        self.telnet_service.update_connection_status_signal = self.update_connection_status_signal
        
        # Dark theme with grey/neutral accents
        self.setStyleSheet("""
            QMainWindow, QWidget, QDialog {
                background-color: #2D2D30;
                color: #DCDCDC;
                font-family: Segoe UI;
            }
            QSplitter::handle {
                background-color: #555;
            }
            QTreeWidget {
                background-color: #252526;
                color: #DCDCDC;
                border: 1px solid #444;
                border-radius: 3px;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:selected {
                background-color: #555;
                color: white;
            }
            QTabWidget::pane {
                border: none;
            }
            QTabBar::tab {
                background: #333;
                color: #AAA;
                padding: 8px 12px;
                border: 1px solid #444;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #3A3A3A;
                color: #FFF;
                border-color: #555;
            }
            QPushButton {
                background-color: #555;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #666;
            }
            QPushButton:pressed {
                background-color: #444;
            }
            QPushButton:disabled {
                background-color: #333;
                color: #777;
            }
            QStatusBar {
                background-color: #333;
                color: #DDD;
                padding: 3px;
            }
            QTextEdit, QPlainTextEdit {
                background-color: #1E1E1E;
                color: #EEE;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 5px;
                font-family: Consolas;
            }
            QLabel {
                color: #CCC;
            }
            QLineEdit {
                background-color: #252525;
                color: white;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 3px;
            }
            #commandInput {
                border: 1px solid #666;
                background-color: #222;
            }
        """)
        
        self.command_resolver = CommandResolver()
        self.command_history = CommandHistory()
        
        # State tracking
        self.current_token = None
        
        # Setup UI first - we'll initialize with empty tree
        self.init_ui()
        
        # Initialize NodeTreePresenter after UI is set up
        self.node_tree_presenter = NodeTreePresenter(
            self.node_tree_view,
            self.node_manager,
            self.session_manager,
            self.log_writer,
            self.command_queue,
            self.fbc_service,
            self.rpc_service,
            self.context_menu_service
        )
        
        # Set presenter in context menu service
        self.context_menu_service.set_presenter(self.node_tree_presenter)
        
        # Connect presenter signals
        self.node_tree_presenter.status_message_signal.connect(self.status_service.status_updated)
        self.node_tree_presenter.node_tree_updated_signal.connect(self.on_node_tree_updated)
        
        # Connect signals after UI initialization
        self.command_finished.connect(self.on_telnet_command_finished)
        self.set_cmd_input_text_signal.connect(self.cmd_input.setPlainText)
        self.update_connection_status_signal.connect(self.telnet_connection_bar.update_status)
        self.switch_to_telnet_tab_signal.connect(lambda: self.session_tabs.setCurrentWidget(self.telnet_tab))
        self.set_cmd_focus_signal.connect(self.cmd_input.setFocus)
        
        # Connect telnet service signals
        self.telnet_service.status_message_signal = self.status_service.status_updated
        self.telnet_service.command_finished_signal = self.command_finished
        self.telnet_service.update_connection_status_signal = self.update_connection_status_signal
        
        # Try loading default configuration if available
        try:
            # Load saved configuration path if exists
            saved_config = self.settings.value("config_path", "")
            if saved_config and os.path.exists(saved_config):
                self.node_manager.set_config_path(saved_config)
            
            # Load saved log root if exists
            saved_log_root = self.settings.value("log_root", "")
            if saved_log_root and os.path.isdir(saved_log_root):
                self.node_manager.set_log_root(saved_log_root)
            
            if os.path.exists(self.node_manager.config_path):
                if self.node_manager.load_configuration():
                    self.node_manager.scan_log_files()
                    self.populate_node_tree()
        except Exception as e:
            logging.error(f"Error loading default configuration: {e}")
            
        # Load saved telnet connection
        telnet_ip = self.settings.value("telnet_ip", "")
        telnet_port = self.settings.value("telnet_port", "")
        if telnet_ip and telnet_port:
            self.telnet_connection_bar.ip_edit.setText(telnet_ip)
            self.telnet_connection_bar.port_edit.setText(telnet_port)
        
    def load_configuration(self):
        """Load node configuration from selected file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Node Configuration File",
            "",
            "JSON Files (*.json)"
        )
        if file_path:
            self.node_tree_presenter.load_configuration(file_path)
    
    def set_log_root_folder(self):
        """Set the root folder for log files"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Log Files Root Folder",
            ""
        )
        if folder_path:
            self.node_tree_presenter.set_log_root_folder(folder_path)
            
    # Removed duplicate context menu handler
        
    def init_ui(self):
        """Initialize the main UI components"""
        # Create main layout
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        
        # Create splitter for dual-pane layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left Pane - Node Tree (30%)
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)
        
        # Create node tree view
        self.node_tree_view = NodeTreeView()
        
        # Connect view signals to window methods
        self.node_tree_view.load_nodes_clicked.connect(self.load_configuration)
        self.node_tree_view.set_log_root_clicked.connect(self.set_log_root_folder)
        self.node_tree_view.node_selected.connect(self.on_node_selected)
        self.node_tree_view.node_double_clicked.connect(self._on_node_double_clicked)
        self.node_tree_view.context_menu_requested.connect(self.show_context_menu)
        
        # Add node tree view to the left layout
        left_layout.addWidget(self.node_tree_view, 1)  # Add stretch factor
        splitter.addWidget(left_pane)
        
        # Create buttons for the window
        self.execute_btn = QPushButton("Execute")
        self.copy_to_log_btn = QPushButton("Copy to Node Log")
        self.clear_terminal_btn = QPushButton("Clear Terminal")
        self.clear_node_log_btn = QPushButton("Clear Node Log")
        
        # Right Pane - Session Area (70%)
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)
        
        # Session Tabs
        self.session_tabs = QTabWidget()
        
        # Create session tabs
        self.telnet_tab = self.create_telnet_tab()
        self.vnc_tab = self.create_session_tab("VNC")
        self.ftp_tab = self.create_session_tab("FTP")
        
        self.session_tabs.addTab(self.telnet_tab, "Telnet")
        self.session_tabs.addTab(self.vnc_tab, "VNC")
        self.session_tabs.addTab(self.ftp_tab, "FTP")
        
        right_layout.addWidget(self.session_tabs)
        
        # Command Buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.copy_to_log_btn)
        button_layout.addWidget(self.clear_terminal_btn)
        button_layout.addWidget(self.clear_node_log_btn)
        
        right_layout.addLayout(button_layout)
        splitter.addWidget(right_pane)
        
        # Set splitter sizes (30/70 ratio)
        splitter.setSizes([300, 700])
        self.setCentralWidget(main_widget)
        
        # Status Bar
        self.setStatusBar(QStatusBar())
        self.status_service.show_status("Welcome to Commander LogCreator")
        
        # Button connections
        self.copy_to_log_btn.clicked.connect(self.copy_to_log)
        self.clear_terminal_btn.clicked.connect(self.clear_terminal)
        self.clear_node_log_btn.clicked.connect(self.clear_node_log)
    
    def show_context_menu(self, position):
        """
        Show context menu for the selected item in the node tree.
        
        Args:
            position: Position where the context menu should be shown
        """
        # Delegate to presenter
        self.node_tree_presenter.show_context_menu(position)
    
    def create_telnet_tab(self) -> QWidget:
        """Creates telnet tab with IP/port inputs and command execution"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Telnet console output
        self.telnet_output = QTextEdit()
        self.telnet_output.setFont(QFont("Consolas", 10))
        self.telnet_output.setReadOnly(False)
        self.telnet_output.setPlaceholderText("Telnet session output will appear here")
        self.status_service.show_info("Telnet session output will appear here")
        self.telnet_output.setStyleSheet("font-family: Consolas; background:#1A1A1A; color: #DDD;")
        layout.addWidget(self.telnet_output, 5)
        
        # Command input panel
        cmd_widget = QWidget()
        cmd_layout = QHBoxLayout(cmd_widget)
        
        self.cmd_input = QTextEdit()
        self.cmd_input.setFont(QFont("Consolas", 10))
        self.cmd_input.setMaximumHeight(60)
        self.cmd_input.setPlaceholderText("Enter telnet command...")
        self.cmd_input.setStyleSheet("background:#252525; color:#EEE; border:1px solid #444;")
        
        cmd_layout.addWidget(QLabel("Command:"))
        cmd_layout.addWidget(self.cmd_input, 3)
        cmd_layout.addWidget(self.execute_btn, 1)
        
        layout.addWidget(cmd_widget, 1)
        
        # Add execute button handler
        self.execute_btn.clicked.connect(self.execute_telnet_command)
        
        # Connection Bar (Telnet)
        self.telnet_connection_bar = ConnectionBar(ip_address="", port=0)
        self.telnet_connection_bar.connection_requested.connect(self.toggle_telnet_connection)
        layout.addWidget(self.telnet_connection_bar)
        
        return tab
        
    def create_session_tab(self, tab_type: str) -> QWidget:
        """Creates placeholder session tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Session content area
        content = QTextEdit()
        content.setFont(QFont("Consolas", 10))
        content.setPlaceholderText(f"{tab_type} session will appear here")
        content.setStyleSheet("background:#1A1A1A; color:#DDD;")
        layout.addWidget(content, 5)
        
        # Connection Bar (VNC/FTP uses a generic one for now)
        # Note: IP/Port will be updated dynamically later
        connection_bar = ConnectionBar(ip_address="", port=0)
        
        # Store a reference to the connection bar for potential dynamic updates
        # For now, let's keep it simple and assume they will be updated via item selection
        if tab_type == "VNC":
            self.vnc_connection_bar = connection_bar
            self.vnc_content_output = content # For VNC content capture
        elif tab_type == "FTP":
            self.ftp_connection_bar = connection_bar
            self.ftp_content_output = content # For FTP content capture

        layout.addWidget(connection_bar)        
        return tab
        
    def populate_node_tree(self):
        """Lazy-loading tree population - only loads top-level nodes initially"""
        # Delegate to presenter
        self.node_tree_presenter.populate_node_tree()
        
    def _handle_item_expanded(self, item):
        """Handle lazy loading of node children when expanded - now handled by presenter"""
        pass
        
    def _on_node_double_clicked(self, item):
        """Wrapper method to handle node double-click events"""
        self.open_log_file(item, 0)  # column is not used but required by method signature
        
    def on_node_selected(self, item: QTreeWidgetItem):
        """Handles node/token selection in left pane"""
        if data := item.data(0, Qt.ItemDataRole.UserRole):
            logging.debug(f"Selected item data: {data}")
            logging.debug(f"Node selected: {item.text(0)}")
            # Check if we have token and node information in the data
            token_id = data.get("token")
            node_name = data.get("node")
            
            # If we have both token and node, set current token
            if node_name and token_id:
                # Derive token_type from actual file extension
                log_path = data.get("log_path", "")
                file_extension = os.path.splitext(log_path)[1][1:].upper() if log_path else "UNKNOWN"
                token_type = file_extension if file_extension in {'FBC','RPC','LOG','LIS'} else 'UNKNOWN'
                logging.debug(f"Creating token from file: {log_path} | Type: {token_type}")
                
                # Create token instance using file-derived type
                token = NodeToken(
                    token_id=token_id,
                    token_type=token_type,
                    name=node_name,
                    ip_address=data.get("ip_address", "0.0.0.0")
                )
                self.current_token = token
                
                # Update ConnectionBar based on token type
                if token_type == "FBC": # Telnet
                    self.session_tabs.setCurrentWidget(self.telnet_tab)
                    
                    # Update status based on actual connection state
                    # Check if telnet service is connected
                    if self.telnet_service and hasattr(self.telnet_service, 'telnet_session') and self.telnet_service.telnet_session and self.telnet_service.telnet_session.is_connected:
                        self.telnet_connection_bar.update_status(ConnectionState.CONNECTED)
                    else:
                        self.telnet_connection_bar.update_status(ConnectionState.DISCONNECTED)
                elif token_type == "VNC":
                    self.session_tabs.setCurrentWidget(self.vnc_tab)
                    if hasattr(self, 'vnc_connection_bar'):
                        self.vnc_connection_bar.ip_edit.setText(token.ip_address)
                        self.vnc_connection_bar.port_edit.setText(str(token.port))
                        if hasattr(self, 'vnc_connection_bar') and self.vnc_connection_bar.ip_edit.text() and self.vnc_connection_bar.port_edit.text():
                            self.vnc_connection_bar.update_status(ConnectionState.CONNECTED)
                        else:
                            self.vnc_connection_bar.update_status(ConnectionState.DISCONNECTED)
                elif token_type == "FTP":
                    self.session_tabs.setCurrentWidget(self.ftp_tab)
                    if hasattr(self, 'ftp_connection_bar'):
                        self.ftp_connection_bar.ip_edit.setText(token.ip_address)
                        self.ftp_connection_bar.port_edit.setText(str(token.port))
                        if hasattr(self, 'ftp_connection_bar') and self.ftp_connection_bar.ip_edit.text() and self.ftp_connection_bar.port_edit.text():
                            self.ftp_connection_bar.update_status(ConnectionState.CONNECTED)
                        else:
                            self.ftp_connection_bar.update_status(ConnectionState.DISCONNECTED)
                
                # Auto-open log file
                try:
                    # Get actual path from tree item data
                    item_data = self.node_tree_view.currentItem().data(0, Qt.ItemDataRole.UserRole)
                    actual_log_path = item_data.get("log_path")
                    if not actual_log_path:
                        raise FileNotFoundError("No log path in selected item")
                    
                    # Use the actual token created from file-derived type
                    self.log_writer.open_log(
                        node_name,
                        data.get("ip_address", "unknown-ip").replace('.', '-'),
                        token,
                        actual_log_path
                    )
                    logging.debug(f"Displaying log: {os.path.basename(actual_log_path)}")
                    # Display exact filename with extension
                    full_filename = os.path.basename(actual_log_path)
                    self.status_service.show_status(f"Log ready: {full_filename}")
                except OSError as e:
                    self.status_service.show_error(f"Error opening log: {str(e)}")

    def toggle_telnet_connection(self, connect: bool):
        """Toggles connection/disconnection for Telnet tab"""
        # Get IP and port directly from input fields
        ip_address, port_text = self.telnet_connection_bar.get_address()
        if not ip_address or not port_text:
            self.status_service.show_error("IP and port are required.")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
            return
        
        try:
            port = int(port_text)
        except ValueError:
            self.status_service.show_error(f"Invalid port number: {port_text}")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
            return
            
        # Delegate to telnet service
        self.telnet_service.toggle_connection(connect, ip_address, port, self.settings)

    
    def execute_telnet_command(self, automatic=False):
        """Executes command in Telnet session using background thread"""
        command = self.cmd_input.toPlainText().strip()
        if not command:
            logging.debug("Empty command received in execute_telnet_command")
            return ""
            
        if not automatic:
            self.command_history.add(command)
            # Display user command in output
            self.telnet_output.append(f"> {command}")
            self.telnet_output.moveCursor(QTextCursor.MoveOperation.End)
            # Disable execute button during execution
            self.execute_btn.setEnabled(False)
        
        # Delegate to telnet service
        self.telnet_service.set_current_token(self.current_token)
        return self.telnet_service.execute_command(command, automatic)

            


    def _log_command_result(self, command: str, result: str, success: bool, token=None):
        """Log command results to the appropriate log file"""
        self.commander_service.logging_service.log_command_result(command, result, success, token)
    
    def _validate_node(self, item) -> bool:
        """Validate node structure before processing"""
        if not item or not item.parent():
            self.status_service.show_error("Invalid node structure")
            return False
        return True

    def _get_valid_tokens(self):
        """Retrieve and validate FBC tokens"""
        node = self.node_manager.get_selected_node()
        if not node:
            self.status_service.show_error("No node selected! Select a node first.")
            return []
            
        logging.debug(f"Selected node: {node.name} ({node.ip_address})")
        return [t for t in node.tokens.values()
                if t.token_type == "FBC" and self.command_queue.validate_token()(t)]
    
    def on_telnet_command_finished(self, response, automatic):
        """
        Handles the completion of a telnet command run in a background thread.
        :param response: The command response text.
        :param automatic: True if the command was triggered automatically (e.g., from context menu).
        """
        logging.info(f"Telnet command finished (automatic={automatic}), response length: {len(response)}")
        logging.debug(f"Command response first 100 chars: {response[:100]}")
        if len(response) > 100:
            logging.debug(f"Command response last 100 chars: {response[-100:]}")
        
        # For automatic commands, show command + response
        if automatic:
            self.telnet_output.append(f"{response}\n")
        else:
            self.telnet_output.append(response)
        self.telnet_output.moveCursor(QTextCursor.MoveOperation.End)
        
        # Delegate logging to LoggingService
        self.commander_service.logging_service.log_telnet_command_finished(
            response, automatic, self.current_token, self.node_manager,
            self.status_message_signal, self.log_writer, self.cmd_input, self.execute_btn
        )
            
    def copy_to_log(self):
        """Copies current session content to selected token or log file"""
        selected_items = self.node_tree_view.selectedItems()
        if not selected_items:
            self.status_service.show_error("No item selected! Select a token or log file on the left.")
            return
        item = selected_items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            self.status_service.show_error("Selected item has no data")
            return
        
        tab_index = self.session_tabs.currentIndex()
        session_type = self.session_tabs.tabText(tab_index)
        
        try:
            # Get session content
            if session_type == "Telnet":
                content = self.telnet_output.toPlainText()
            else:
                tab_widget = self.session_tabs.widget(tab_index)
                content_widget = tab_widget.layout().itemAt(0).widget()
                if isinstance(content_widget, QTextEdit):
                    content = content_widget.toPlainText()
                else:
                    return

            if not content:
                self.status_service.show_error("No content in current session")
                return

            # Handle based on item type
            if "log_path" in data:
                log_path = data["log_path"]
                # Write directly to the file
                with open(log_path, 'a') as f:
                    f.write(content + "\n")
                filename = os.path.basename(log_path)
                self.status_service.show_success(f"Content copied to {filename}")

            elif "token" in data:
                token_id = data["token"]
                node_name = data.get("node")
                token_type = data.get("token_type")
                if not node_name or not token_type:
                    self.status_service.show_error("Token item missing node or token_type")
                    return

                node = self.node_manager.get_node(node_name)
                if not node:
                    self.status_service.show_error(f"Node {node_name} not found")
                    return

                # Reconstruct the log path for display
                ip = node.ip_address.replace('.', '-')
                log_dir = os.path.join(self.node_manager.log_root, token_type, node_name)
                filename = f"{node_name}_{ip}_{token_id}.{token_type.lower()}"
                # Write using the log_writer
                self.log_writer.append_to_log(token_id, content, source=session_type)
                self.status_service.show_success(f"Content copied to {filename}")

            else:
                self.status_service.show_error("Unsupported item type")

        except Exception as e:
            self.status_service.show_error(f"Log write error: {str(e)}")
    
    def clear_terminal(self):
        """Clear the telnet output area"""
        self.telnet_output.clear()
        self.status_service.show_status("Terminal cleared", StatusService.STATUS_MSG_SHORT)
    
    def clear_node_log(self):
        """Clear the currently selected node's log file"""
        selected_items = self.node_tree_view.selectedItems()
        if not selected_items:
            self.status_service.show_error("No item selected! Select a log file on the left.")
            return
        
        item = selected_items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or "log_path" not in data:
            self.status_service.show_error("Selected item is not a log file")
            return
            
        log_path = data["log_path"]
        try:
            # Open the file in write mode to truncate it
            with open(log_path, 'w') as f:
                f.truncate(0)
            self.status_service.show_success(f"Cleared log: {os.path.basename(log_path)}")
        except Exception as e:
            self.status_service.show_error(f"Error clearing log: {str(e)}")
    
    def open_log_file(self, item: QTreeWidgetItem, column: int):
        """Opens log file when double-clicked in tree view"""
        if data := item.data(0, Qt.ItemDataRole.UserRole):
            # All log items stored their path in "log_path"
            if "log_path" in data:
                log_path = data["log_path"]
                
                # Use system default application to open the log file
                try:
                    os.startfile(log_path)  # Windows-specific
                    self.status_service.show_status(f"Opened log file: {os.path.basename(log_path)}")
                except Exception as e:
                    self.status_service.show_error(f"Error opening file: {str(e)}")
                return True
        return False
        
    def on_node_tree_updated(self):
        """Handle node tree updates from presenter"""
        # Item expanded signal is now connected through the presenter
        pass
        
    def closeEvent(self, event):
        """Cleanup on window close"""
        self.telnet_service.disconnect()
        self.log_writer.close_all_logs()
        
        # Save application state
        self.settings.setValue("config_path", self.node_manager.config_path)
        self.settings.setValue("log_root", self.node_manager.log_root)
        
        # Save telnet connection state
        if hasattr(self, 'telnet_connection_bar'):
            self.settings.setValue("telnet_ip", self.telnet_connection_bar.ip_edit.text())
            self.settings.setValue("telnet_port", self.telnet_connection_bar.port_edit.text())

        super().closeEvent(event)


def run():
    # Initialize Qt application safely
    app = initialize_qt() or QApplication(sys.argv)
    
    # Apply dark theme styling
    app.setStyle("Fusion")
    
    # Create main window instance
    window = CommanderWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    run()