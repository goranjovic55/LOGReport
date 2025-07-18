from .models import NodeToken
from .services.fbc_command_service import FbcCommandService
from .services.rpc_command_service import RpcCommandService
"""
Commander Main Window
Dual-pane interface for managing nodes and sessions
"""
import sys
import os
import logging
import glob
import re
import socket
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
from .widgets import ConnectionBar, ConnectionState

# Import our components
from .node_manager import NodeManager
from .session_manager import SessionManager, SessionType, SessionConfig
from .log_writer import LogWriter
from .commands.telnet_commands import CommandResolver, CommandHistory
from .command_queue import CommandQueue
from .icons import get_node_online_icon, get_node_offline_icon, get_token_icon

# Centralized Qt application initialization
from .qt_init import initialize_qt

import threading
import time

class CommanderWindow(QMainWindow):
    """Main Commander window."""
    
    # Status message durations in milliseconds
    STATUS_MSG_SHORT = 3000    # 3 seconds
    STATUS_MSG_MEDIUM = 5000   # 5 seconds
    STATUS_MSG_LONG = 10000    # 10 seconds
    
    # Compiled regex patterns for token extraction
    FBC_TOKEN_PATTERN = re.compile(r"^([\w-]+)_[\d\.-]+_([\w-]+)\.")
    RPC_TOKEN_PATTERN = re.compile(r"_([\d\w-]+)\.[^.]*$")  # Matches last _token.extension
    LIS_TOKEN_PATTERN = re.compile(r"^([\w-]+)_[\d-]+_([\d\w-]+)\.lis$")
    
    """Main Commander window."""
    
    # Signal for telnet command completion: (response, automatic)
    command_finished = pyqtSignal(str, bool)
    queue_processed = pyqtSignal(int, int)  # Success count, total
    
    # Signals for UI updates from background threads
    status_message_signal = pyqtSignal(str, int)
    set_cmd_input_text_signal = pyqtSignal(str)
    update_connection_status_signal = pyqtSignal(ConnectionState)
    switch_to_telnet_tab_signal = pyqtSignal()
    set_cmd_focus_signal = pyqtSignal()
        
        
    def show_context_menu(self, position):
        """Context menu handler for node tree items with detailed logging"""
        logging.debug("Context menu received show_context_menu request")
        logging.debug(f"Context menu shown at position: {position}")
        try:
            item = self.node_tree.itemAt(position)
            if not item:
                logging.debug("Context menu - no item at position")
                return
                
            # Ensure the item is selected to set current_token
            self.node_tree.setCurrentItem(item)
                
            logging.debug(f"Context menu found item: {item.text(0)}")
            data = item.data(0, Qt.ItemDataRole.UserRole)
            menu = QMenu(self.node_tree)
            added_actions = False

            # Handle token items
            if data and isinstance(data, dict):
                token_type = data.get("token_type", "UNKNOWN").upper()  # Handle all file types
                token_id = data.get("token", None)
                node_name = data.get("node", "Unknown")
                
                logging.debug(f"Context menu token type: '{token_type}', Token ID: {token_id}, Node: {node_name}")
                
                if token_id:
                    logging.debug(f"Context menu processing token item: type={token_type}, id={token_id}")
                    
                    if token_type == "FBC":
                        logging.debug("Context menu creating context menu for FBC item")
                        # Ensure token is string to prevent normalization issues
                        token_str = str(token_id)
                        action_text = f"Print FieldBus Structure (Token {token_str})"
                        action = QAction(action_text, self)
                        action.setProperty("context_item", item)  # Store context menu item reference
                        logging.debug(f"Creating FBC action: Token={token_str}, Node={node_name}")
                        # Capture token explicitly to avoid closure issues
                        action.triggered.connect(
                            lambda checked, t=token_str, n=node_name:
                                (logging.debug(f"FBC action triggered for token: {t}, node: {n}"),
                                 self.process_fieldbus_command(t, n))
                        )
                        logging.debug(f"Context menu created for FBC item | Token: {token_str} | Path: {data.get('log_path', '')}")
                        menu.addAction(action)
                        added_actions = True
                        
                    elif token_type == "RPC":
                        logging.debug("Context menu creating context menu for RPC item")
                        
                        # Extract numerical token part (last segment after underscore)
                        display_token = token_id.split('_')[-1] if '_' in token_id else token_id
                        
                        # Print Rupi Counters action
                        print_action = QAction(f"Print Rupi counters Token '{display_token}'", self)
                        print_action.triggered.connect(lambda: self.process_rpc_command(token_id, "print"))
                        menu.addAction(print_action)
                        
                        # Clear Rupi Counters action
                        clear_action = QAction(f"Clear Rupi counters '{display_token}'", self)
                        clear_action.triggered.connect(lambda: self.process_rpc_command(token_id, "clear"))
                        menu.addAction(clear_action)
                        added_actions = True
            
            # Handle FBC/RPC subgroup selection
            elif item.text(0) in ["FBC", "RPC"]:
                logging.debug(f"Context menu processing {item.text(0)} subgroup")
                # Get parent items with validation
                node_name = None  # Initialize at function scope
        
                try:
                    # The subgroup item's direct parent is the node item
                    node_item = item.parent()
                    if not node_item:
                        raise ValueError(f"{item.text(0)} subgroup has no parent node")
                    
                    # Extract node name safely
                    node_name = node_item.text(0).split(' ', 1)[0].strip()
                    if not node_name:
                        raise ValueError("Node item text is empty")
                    
                    logging.debug(f"Context menu valid structure detected:")
                    logging.debug(f"  Node: {node_name} ({node_item.text(0)})")
                    logging.debug(f"  Subgroup: {item.text(0)}")

                    # Create context menu action after validation
                    action_text = f"Print All {item.text(0)} Tokens for {node_name}"
                    action = QAction(action_text, self)
                    if item.text(0) == "FBC":
                        action.triggered.connect(lambda: self.process_all_fbc_subgroup_commands(item))
                    else:
                        action.triggered.connect(lambda: self.process_all_rpc_subgroup_commands(item))
                    menu.addAction(action)
                    
                    # Add new Print Tokens submenu
                    tokens_submenu = QMenu(f"Print {item.text(0)} Tokens", self)
                    added_tokens = False
                    
                    # Get node tokens
                    node = self.node_manager.get_node(node_name)
                    if node:
                        for token in node.tokens.values():
                            if token.token_type == item.text(0):
                                token_id = token.token_id
                                token_action = QAction(f"Token {token_id}", self)
                                token_action.triggered.connect(
                                    lambda checked, t=token_id, n=node_name, tt=item.text(0):
                                        self._print_tokens_sequentially(t, n, tt)
                                )
                                tokens_submenu.addAction(token_action)
                                added_tokens = True
                    
                    if added_tokens:
                        menu.addMenu(tokens_submenu)
                    
                    added_actions = True
                    
                except Exception as e:
                    logging.error(f"Context menu structure validation failed: {str(e)}")
                    return
                
                
            if added_actions:
                # Show menu at cursor position
                menu.exec(self.node_tree.viewport().mapToGlobal(position))
                logging.debug(f"Context menu displayed with {len(menu.actions())} actions")
            else:
                logging.debug("Context menu - no applicable actions for this item")
        except Exception as e:
            logging.error(f"Context menu error: {str(e)}")
            
    def process_fieldbus_node(self, node_name):
        """Process fieldbus structure commands for all FBC tokens in a node"""
        node = self.node_manager.get_node(node_name)
        if not node:
            self.statusBar().showMessage(f"Node {node_name} not found", self.STATUS_MSG_SHORT)
            return
            
        # Find all FBC tokens in the node
        fbc_tokens = [t for t in node.tokens.values() if t.token_type == "FBC"]
        if not fbc_tokens:
            self.statusBar().showMessage(f"No FBC tokens found in node {node_name}", self.STATUS_MSG_SHORT)
            return
            
        self.statusBar().showMessage(f"Processing {len(fbc_tokens)} FBC tokens in node {node_name}...", self.STATUS_MSG_LONG)
        
        for token in fbc_tokens:
            self.current_token = token
            self.process_fieldbus_command(token.token_id)
            
        self.statusBar().showMessage(f"Fieldbus commands executed for {len(fbc_tokens)} tokens", self.STATUS_MSG_SHORT)
            
    def _report_error(self, message: str, exception: Exception = None, duration: int = None):
        """Centralized error reporting with logging and status bar updates"""
        duration = duration or self.STATUS_MSG_MEDIUM
        error_msg = f"{message}: {str(exception)}" if exception else message
        logging.error(error_msg)
        self.status_message_signal.emit(error_msg, duration)
        logging.error(error_msg)
        
    def _print_tokens_sequentially(self, token_id, node_name, token_type):
        """Print token values sequentially for the given token"""
        try:
            if token_type == "FBC":
                self.fbc_service.queue_fieldbus_command(node_name, token_id)
            else:
                self.rpc_service.queue_rpc_command(node_name, token_id, "print")
        except Exception as e:
            self._report_error(f"Error processing {token_type} command", e)
        except ConnectionRefusedError as e:
            self._report_error("Connection refused", e)
        except TimeoutError as e:
            self._report_error("Connection timed out", e)

    def _handle_fbc_error(self, error_msg: str):
        """Handle FBC service errors by reporting them"""
        self._report_error("FBC Service Error", Exception(error_msg))

    def process_all_rpc_subgroup_commands(self, item):
        """Process all RPC commands using command queue"""
        try:
            # Get node name from item hierarchy
            section_item = item.parent()
            if not section_item:
                raise ValueError("RPC subgroup has no parent section")
            node_item = section_item.parent()
            if not node_item:
                raise ValueError(f"Section {section_item.text(0)} has no parent node")
            node_name = node_item.text(0).split(' ', 1)[0].strip()
            
            node = self.node_manager.get_node(node_name)
            if not node:
                self.status_message_signal.emit(f"Node {node_name} not found", self.STATUS_MSG_SHORT)
                return
                
            # Find all RPC tokens in the node
            rpc_tokens = [t for t in node.tokens.values() if t.token_type == "RPC"]
            if not rpc_tokens:
                self.status_message_signal.emit(f"No RPC tokens found in node {node_name}", self.STATUS_MSG_SHORT)
                return
                
            self.status_message_signal.emit(f"Processing {len(rpc_tokens)} RPC tokens in node {node_name}...", 0)
            
            # Queue commands for all RPC tokens
            for token in rpc_tokens:
                command_text = f"print from fbc rupi counters {token.token_id}0000"
                self.command_queue.add_command(command_text, token)
                
            self.status_message_signal.emit(f"Queued {len(rpc_tokens)} commands for node {node_name}", self.STATUS_MSG_SHORT)
            self.command_queue.start_processing()
            
        except Exception as e:
            self.status_message_signal.emit(f"Error processing RPC commands: {str(e)}", self.STATUS_MSG_MEDIUM)

    def process_fieldbus_command(self, token_id, node_name):
        """Process fieldbus command with optimized error handling"""
        try:
            # Get log path from current tree item if available
            current_item = self.node_tree.currentItem()
            log_path = None
            if current_item:
                item_data = current_item.data(0, Qt.ItemDataRole.UserRole)
                if item_data and "log_path" in item_data:
                    log_path = item_data["log_path"]
            
            # Pass log path to command queue via token
            token = self.fbc_service.get_token(node_name, token_id)
            if log_path and hasattr(token, 'log_path'):
                token.log_path = log_path
            
            self.fbc_service.queue_fieldbus_command(node_name, token_id)
        except (ConnectionRefusedError, TimeoutError) as e:
            self._report_error(f"{type(e).__name__} processing command", e)
        except Exception as e:
            self._report_error("Unexpected error processing command", e)
            
    def process_rpc_command(self, token_id, action_type):
        """Process RPC commands with token validation and auto-execute"""
        if action_type not in ["print", "clear"]:
            return
            
        try:
            if not token_id or not isinstance(token_id, str):
                raise ValueError("Invalid token ID")
                
            token_num = token_id.split('_')[-1]  # Extract token number after last underscore
            command_text = (
                f"print from fbc rupi counters {token_num}0000"
                if action_type == "print"
                else f"clear fbc rupi counters {token_num}0000"
            )
            
            # Log context menu command initiation
            logging.debug(f"Context menu command: {action_type} for token {token_id}")
            
            # Set command and switch to telnet tab
            self.cmd_input.setPlainText(command_text)
            self.session_tabs.setCurrentWidget(self.telnet_tab)
            self.cmd_input.setFocus()
            
            # Execute command immediately
            self.execute_telnet_command(automatic=True)
            
            action_name = "Print" if action_type == "print" else "Clear"
            self.statusBar().showMessage(
                f"{action_name} Rupi counters for token {token_num}", 3000)
        except ValueError as e:
            self._report_error("Invalid RPC command parameters", e)
        except AttributeError as e:
            self._report_error("UI component access error", e)
        except Exception as e:
            logging.error(f"Unexpected error in RPC command setup: {str(e)}")
            self._report_error("RPC command setup failed", e)
            
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Commander LogCreator v1.0")
        self.setMinimumSize(1200, 800)
        
        # Thread lock for telnet operations
        self.telnet_lock = threading.Lock()
        
        # Load application settings
        self.settings = QSettings("CommanderLogCreator", "Settings")

        # Core components needed for services
        self.node_manager = NodeManager()
        self.command_queue = CommandQueue()
        self.command_queue.command_completed.connect(self._handle_queued_command_result)

        # Initialize RPC Command Service
        self.rpc_service = RpcCommandService(self.node_manager, self.command_queue, self)
        self.rpc_service.set_command_text.connect(self.set_cmd_input_text_signal)
        self.rpc_service.switch_to_telnet_tab.connect(self.switch_to_telnet_tab_signal)
        self.rpc_service.focus_command_input.connect(self.set_cmd_focus_signal)
        self.rpc_service.status_message.connect(self.status_message_signal)
        self.rpc_service.report_error.connect(lambda msg: self._report_error("RPC Service Error", Exception(msg)))
        
        # Initialize FBC Command Service
        self.fbc_service = FbcCommandService(self.node_manager, self.command_queue, self)
        self.fbc_service.set_command_text.connect(self.set_cmd_input_text_signal)
        self.fbc_service.switch_to_telnet_tab.connect(self.switch_to_telnet_tab_signal)
        self.fbc_service.focus_command_input.connect(self.set_cmd_focus_signal)
        self.fbc_service.status_message.connect(self.status_message_signal)
        self.fbc_service.report_error.connect(lambda msg: self._report_error("FBC Service Error", Exception(msg)))
        
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
        
        # Core components
        self.session_manager = SessionManager()
        self.log_writer = LogWriter(self.node_manager)
        self.command_resolver = CommandResolver()
        self.command_history = CommandHistory()
        
        # FBC Command Service
        self.fbc_service = FbcCommandService(self.node_manager, self.command_queue, self)
        self.fbc_service.set_command_text.connect(self.set_cmd_input_text_signal)
        self.fbc_service.switch_to_telnet_tab.connect(self.switch_to_telnet_tab_signal)
        self.fbc_service.focus_command_input.connect(self.set_cmd_focus_signal)
        self.fbc_service.status_message.connect(self.status_message_signal)
        self.fbc_service.report_error.connect(lambda msg: self._report_error("FBC Service Error", Exception(msg)))
        
        # State tracking
        self.current_token = None
        self.telnet_session = None
        self.telnet_active = False
        
        # Setup UI first - we'll initialize with empty tree
        self.init_ui()
        
        # Connect signals after UI initialization
        self.command_finished.connect(self.on_telnet_command_finished)
        self.set_cmd_input_text_signal.connect(self.cmd_input.setPlainText)
        self.update_connection_status_signal.connect(self.telnet_connection_bar.update_status)
        self.switch_to_telnet_tab_signal.connect(lambda: self.session_tabs.setCurrentWidget(self.telnet_tab))
        self.set_cmd_focus_signal.connect(self.cmd_input.setFocus)
        self.status_message_signal.connect(self.statusBar().showMessage)
        
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
        # Removed incomplete import statement
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Node Configuration File", 
            "", 
            "JSON Files (*.json)"
        )
        if file_path:
            self.node_manager.set_config_path(file_path)
            if self.node_manager.load_configuration():
                self.node_manager.scan_log_files()
                self.populate_node_tree()
            else:
                logging.error("Error loading node configuration")
    
    def set_log_root_folder(self):
        """Set the root folder for log files"""
        from PyQt6.QtWidgets import QFileDialog
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Log Files Root Folder",
            ""
        )
        if folder_path:
            self.node_manager.set_log_root(folder_path)
            self.node_manager.scan_log_files()
            self.populate_node_tree()
            
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
        
        # Install event filter for node_tree
        self.node_tree = QTreeWidget()
        self.node_tree.installEventFilter(self)
        logging.debug("Node tree event filter installed")
        
        # Toolbar with buttons
        toolbar_layout = QHBoxLayout()
        self.load_nodes_btn = QPushButton("Load Nodes")
        self.load_nodes_btn.clicked.connect(self.load_configuration)
        self.set_log_root_btn = QPushButton("Set Log Root")
        self.set_log_root_btn.clicked.connect(self.set_log_root_folder)
        
        toolbar_layout.addWidget(self.load_nodes_btn)
        toolbar_layout.addWidget(self.set_log_root_btn)
        left_layout.addLayout(toolbar_layout)
        
        # Node Tree Widget
        self.node_tree = QTreeWidget()
        self.node_tree.setHeaderLabels(["Nodes"])
        self.node_tree.setColumnWidth(0, 300)
        self.node_tree.setFont(QFont("Consolas", 10))
        self.node_tree.itemClicked.connect(self.on_node_selected)
        self.node_tree.itemDoubleClicked.connect(self.open_log_file)
        self.node_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.node_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.node_tree.installEventFilter(self)
        logging.debug("Node tree context menu handling installed")

    # Removed event filter implementation
        
        left_layout.addWidget(self.node_tree, 1)  # Add stretch factor
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
        self.statusBar().showMessage("Welcome to Commander LogCreator")
        
        # Button connections
        self.copy_to_log_btn.clicked.connect(self.copy_to_log)
        self.clear_terminal_btn.clicked.connect(self.clear_terminal)
        self.clear_node_log_btn.clicked.connect(self.clear_node_log)
    
    def create_telnet_tab(self) -> QWidget:
        """Creates telnet tab with IP/port inputs and command execution"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Telnet console output
        self.telnet_output = QTextEdit()
        self.telnet_output.setFont(QFont("Consolas", 10))
        self.telnet_output.setReadOnly(False)
        self.telnet_output.setPlaceholderText("Telnet session output will appear here")
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
        self.node_tree.clear()
        self.node_tree.itemExpanded.connect(self._handle_item_expanded)
        
        for node in self.node_manager.get_all_nodes():
            node_item = self._create_node_item(node)
            if node_item:
                # Add placeholder child that will trigger loading when expanded
                placeholder = QTreeWidgetItem(["Click to load..."])
                placeholder.setData(0, Qt.ItemDataRole.UserRole, {"node": node.name, "type": "placeholder"})
                node_item.addChild(placeholder)
                self.node_tree.addTopLevelItem(node_item)
                logging.debug(f"Added node with placeholder: {node.name}")
        
    def _handle_item_expanded(self, item):
        """Handle lazy loading of node children when expanded"""
        logging.debug(f"Item expanded: {item.text(0)}")
        data = item.data(0, Qt.ItemDataRole.UserRole)
        # Check if expanded item is a node with placeholder child
        if data and data.get("type") == "node":
            # Find placeholder child (if exists)
            for i in range(item.childCount()):
                child = item.child(i)
                child_data = child.data(0, Qt.ItemDataRole.UserRole)
                if child_data and child_data.get("type") == "placeholder":
                    item.removeChild(child)
                    logging.debug(f"Removed placeholder for node: {item.text(0)}")
                    self._load_node_children(item)
                    break  # Only remove first placeholder found
        else:
            logging.debug("Expanded item is not a node or has no placeholder")
    
    def _load_node_children(self, node_item):
        """Load actual children for a node"""
        # Get node name from stored user data
        data = node_item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("type") != "node":
            logging.debug("_load_node_children: Item is not a node")
            return
            
        node_name = data["node_name"]
        logging.debug(f"_load_node_children: Loading children for node: {node_name}")
        node = self.node_manager.get_node(node_name)
        if not node:
            logging.debug(f"_load_node_children: Node {node_name} not found")
            return
            
        added_sections = False
        
        # Create sections for each token type
        sections = [
            ("FBC", self._add_section("FBC", node, "FBC", ['.fbc', '.log', '.txt'])),
            ("RPC", self._add_section("RPC", node, "RPC", ['.rpc', '.log', '.txt'])),
            ("LOG", self._add_section("LOG", node, "LOG", ['.log'])),
            ("LIS", self._add_section("LIS", node, "LIS", ['.lis']))
        ]
        
        logging.debug(f"_load_node_children: Processing sections for node: {node.name}")
        for section_type, section_data in sections:
            logging.debug(f"_load_node_children: Processing {section_type} section")
            logging.debug(f"_load_node_children: Section data: items={len(section_data['items'])}")
            
            # Always create the section item even if no files are found
            section = QTreeWidgetItem([section_type])
            section.setIcon(0, get_token_icon() if section_type in ("FBC", "RPC")
                           else QIcon(":/icons/page.png"))
            
            if section_data["items"]:
                logging.debug(f"_load_node_children: Adding {len(section_data['items'])} files to {section_type} section")
                for item in section_data["items"]:
                    section.addChild(item)
                logging.debug(f"_load_node_children: Added {section_type} section with {section_data['count']} items")
            else:
                # Add placeholder text if no files found
                placeholder = QTreeWidgetItem(["No files found"])
                placeholder.setIcon(0, QIcon(":/icons/warning.png"))
                section.addChild(placeholder)
                logging.debug(f"_load_node_children: No items found for {section_type} section")
            
            node_item.addChild(section)
            added_sections = True
            logging.debug(f"_load_node_children: Added {section_type} subsection to node tree")
        
        if not added_sections:
            no_files = QTreeWidgetItem(["No files found for this node"])
            no_files.setIcon(0, QIcon(":/icons/warning.png"))
            node_item.addChild(no_files)
            logging.debug(f"_load_node_children: No files found for node: {node_name}")
        
    def _create_node_item(self, node):
        """Create node tree item with status icon"""
        node_item = QTreeWidgetItem([f"{node.name} ({node.ip_address})"])
        node_item.setIcon(0, get_node_online_icon() if node.status == "online"
                         else get_node_offline_icon())
        # Store node name in user data for later retrieval
        node_item.setData(0, Qt.ItemDataRole.UserRole, {
            "type": "node",
            "node_name": node.name
        })
        
        # Check log root
        log_root = self.node_manager.log_root
        if not log_root or not os.path.isdir(log_root):
            no_folder = QTreeWidgetItem(["Please set log root folder"])
            no_folder.setIcon(0, QIcon(":/icons/warning.png"))
            node_item.addChild(no_folder)
            return node_item
            
        return node_item
        
    def _add_section(self, section_type, node, dir_name, extensions):
        """Add file items to section using glob patterns for efficiency"""
        # For LOG files, directory is <log_root>/LOG/<node.name>
        # For others, it's <log_root>/<dir_name>/<node.name>
        if section_type == "LOG":
            section_dir = os.path.join(self.node_manager.log_root, "LOG")
        else:
            section_dir = os.path.join(self.node_manager.log_root, dir_name, node.name)
            
        items = []
        
        if not os.path.isdir(section_dir):
            logging.debug(f"Directory not found: {section_dir}")
            return {"items": items, "count": 0}
            
        # Process files matching patterns
        for ext in extensions:
            if section_type == "LOG":
                pattern = os.path.join(section_dir, f"{node.name}_*.log")
                logging.debug(f"LOG SECTION DEBUG: Scanning directory: {section_dir}")
                logging.debug(f"LOG SECTION DEBUG: Using pattern: {pattern}")
            else:
                pattern = os.path.join(section_dir, f"{node.name}_*{ext}")
                
            logging.debug(f"Scanning for {section_type} files with pattern: {pattern}")
            files_found = glob.glob(pattern)
            logging.debug(f"Found {len(files_found)} files matching pattern")
            
            for file_path in files_found:
                filename = os.path.basename(file_path)
                token_id = self._extract_token_id(filename, node.name, section_type)
                
                logging.debug(f"LOG SECTION DEBUG: Processing file: {filename} | Extracted token: {token_id}")
                
                if not token_id and section_type != "LOG":
                    continue  # Skip invalid tokens except for LOG
                    
                file_item = self._create_file_item(
                    filename, file_path, node,
                    token_id, section_type
                )
                items.append(file_item)
                logging.debug(f"Found {section_type} file: {filename}")
                
        logging.debug(f"Total {section_type} files found: {len(items)}")
        if section_type == "LOG" and len(items) == 0:
            logging.warning("No LOG files found! Possible causes:")
            logging.warning(f"1. Directory doesn't exist: {section_dir}")
            logging.warning(f"2. Pattern mismatch: {pattern}")
            logging.warning(f"3. Token extraction failed for existing files")
        return {"items": items, "count": len(items)}
        
    def _extract_token_id(self, filename, node_name, section_type):
        """Extract token ID from filename based on section type"""
        if section_type == "LOG":
            # Use the filename without extension as token ID
            return os.path.splitext(filename)[0]
            
        try:
            if section_type == "FBC":
                match = self.FBC_TOKEN_PATTERN.match(filename)
                return match.group(2) if match and match.group(1) == node_name else None
            elif section_type == "RPC":
                match = self.RPC_TOKEN_PATTERN.search(filename)
                return match.group(1) if match else None
            elif section_type == "LIS":
                match = self.LIS_TOKEN_PATTERN.match(filename)
                return match.group(2) if match and match.group(1) == node_name else None
        except (IndexError, AttributeError):
            return None
            
        return None
        
    def _create_file_item(self, filename, file_path, node, token_id, token_type):
        """Create standardized file tree item"""
        file_item = QTreeWidgetItem([f"📝 {filename}"])
        file_extension = os.path.splitext(file_path)[1][1:].upper()
        resolved_type = file_extension if file_extension in {'FBC','RPC','LOG','LIS'} else token_type
        
        file_item.setData(0, Qt.ItemDataRole.UserRole, {
            "log_path": file_path,
            "token": token_id,
            "token_type": resolved_type,
            "node": node.name,
            "ip_address": node.ip_address
        })
        file_item.setIcon(0, QIcon(":/icons/page.png"))
        return file_item
    
    def on_node_selected(self, item: QTreeWidgetItem, column: int):
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
                    if self.telnet_session and self.telnet_session.is_connected:
                        self.telnet_connection_bar.update_status(ConnectionState.CONNECTED)
                    else:
                        self.telnet_connection_bar.update_status(ConnectionState.DISCONNECTED)
                elif token_type == "VNC":
                    self.session_tabs.setCurrentWidget(self.vnc_tab)
                    if hasattr(self, 'vnc_connection_bar'):
                        self.vnc_connection_bar.ip_edit.setText(token.ip_address)
                        self.vnc_connection_bar.port_edit.setText(str(token.port))
                        if self.vnc_session and self.vnc_session.is_connected:
                            self.vnc_connection_bar.update_status(ConnectionState.CONNECTED)
                        else:
                            self.vnc_connection_bar.update_status(ConnectionState.DISCONNECTED)
                elif token_type == "FTP":
                    self.session_tabs.setCurrentWidget(self.ftp_tab)
                    if hasattr(self, 'ftp_connection_bar'):
                        self.ftp_connection_bar.ip_edit.setText(token.ip_address)
                        self.ftp_connection_bar.port_edit.setText(str(token.port))
                        if self.ftp_session and self.ftp_session.is_connected:
                            self.ftp_connection_bar.update_status(ConnectionState.CONNECTED)
                        else:
                            self.ftp_connection_bar.update_status(ConnectionState.DISCONNECTED)
                
                # Auto-open log file
                try:
                    # Get actual path from tree item data
                    item_data = self.node_tree.currentItem().data(0, Qt.ItemDataRole.UserRole)
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
                    self.statusBar().showMessage(f"Log ready: {full_filename}")
                except OSError as e:
                    self.statusBar().showMessage(f"Error opening log: {str(e)}")

    def toggle_telnet_connection(self, connect: bool):
        """Toggles connection/disconnection for Telnet tab"""
        # Get IP and port directly from input fields
        ip_address, port_text = self.telnet_connection_bar.get_address()
        if not ip_address or not port_text:
            self.statusBar().showMessage("IP and port are required.")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
            return
        
        try:
            port = int(port_text)
        except ValueError:
            self.statusBar().showMessage(f"Invalid port number: {port_text}")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
            return
            
        if connect:
            # Save connection parameters to settings
            self.settings.setValue("telnet_ip", ip_address)
            self.settings.setValue("telnet_port", port_text)
            self.connect_telnet(ip_address, port)
        else:
            self.disconnect_telnet()

    def connect_telnet(self, ip_address: str, port: int):
        """Connects to specified telnet server using provided IP and port"""
        # Configure telnet connection using the parameters
        config = SessionConfig(
            host=ip_address,
            port=port,
            session_type=SessionType.TELNET,
            username="",   # No username by default
            password=""    # No password by default
        )
        
        try:
            self.telnet_connection_bar.update_status(ConnectionState.CONNECTING)
            self.telnet_session = self.session_manager.create_session(config)
            
            # Attempt connection and get detailed result
            if self.telnet_session and self.telnet_session.is_connected:
                # Clear output and update status
                self.telnet_output.clear()
                self.telnet_output.append(f"Connected to {ip_address}:{port}")
                self.telnet_connection_bar.update_status(ConnectionState.CONNECTED)
                self.cmd_input.setFocus()
                return True
            
            # Handle connection failure
            self.statusBar().showMessage("Connection failed")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
            return False
            
        except socket.timeout as e:
            self.statusBar().showMessage(f"Connection timed out: {str(e)}")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
        except ConnectionRefusedError as e:
            self.statusBar().showMessage(f"Connection refused: {str(e)}")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
        except Exception as e:
            self.statusBar().showMessage(f"Connection error: {str(e)}")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
            return False
    
    def disconnect_telnet(self):
        """Disconnects from current telnet session"""
        try:
            # Only close through session manager to avoid double disconnect
            self.session_manager.close_all_sessions()
            # Clear local reference AFTER session manager has closed sessions
            self.telnet_session = None
            # Force UI update to disconnected state
            self.telnet_connection_bar.update_status(ConnectionState.DISCONNECTED)
            self.telnet_output.append("\n>>> DISCONNECTED")
        except Exception as e:
            self.telnet_output.append(f"Error disconnecting: {str(e)}")
            # Still reset UI state even if disconnection failed
            self.telnet_connection_bar.update_status(ConnectionState.DISCONNECTED)
            
    def execute_telnet_command(self, automatic=False):
        """Executes command in Telnet session using background thread"""
        if not self.telnet_session:
            if not automatic:
                self.statusBar().showMessage("Create a Telnet session first!")
            return ""
        
        command = self.cmd_input.toPlainText().strip()
        if not command:
            return ""
            
        logging.debug(f"Executing telnet command: {command}")

        if not automatic:
            self.command_history.add(command)
            # Display user command in output
            self.telnet_output.append(f"> {command}")
            self.telnet_output.moveCursor(QTextCursor.MoveOperation.End)
            # Disable execute button during execution
            self.execute_btn.setEnabled(False)
        
        # Start command execution in background thread
        threading.Thread(
            target=self._run_telnet_command,
            args=(command, automatic),
            daemon=True
        ).start()
        
        return ""  # Response will be handled asynchronously

    def _run_telnet_command(self, command, automatic):
        """Runs telnet command in background thread with improved error handling"""
        with self.telnet_lock:
            try:
                token_id = self.current_token.token_id if self.current_token else ""
                resolved_cmd = self.command_resolver.resolve(command, token_id)
                response = self.telnet_session.send_command(resolved_cmd, timeout=5)
                self.telnet_connection_bar.update_status(ConnectionState.CONNECTED)
            except (ConnectionRefusedError, TimeoutError, socket.timeout) as e:
                response = f"ERROR: {type(e).__name__} - {str(e)}"
                self._handle_connection_error(e)
            except Exception as e:
                response = f"ERROR: {type(e).__name__} - {str(e)}"
                logging.error(f"Telnet command failed: {command}", exc_info=True)
            
            self.command_finished.emit(response, automatic)
            
    def _handle_connection_error(self, error):
        """Centralized connection error handling"""
        error_type = type(error).__name__
        if error_type in ["ConnectionRefusedError", "TimeoutError", "socket.timeout"]:
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
            self.status_message_signal.emit(f"Connection error: {str(error)}", self.STATUS_MSG_MEDIUM)

    def process_all_fbc_subgroup_commands(self, item):
        """Process all FBC commands using command queue"""
        try:
            # Get node name from item hierarchy
            section_item = item.parent()
            if not section_item:
                raise ValueError("FBC subgroup has no parent section")
            node_item = section_item.parent()
            if not node_item:
                raise ValueError(f"Section {section_item.text(0)} has no parent node")
            node_name = node_item.text(0).split(' ', 1)[0].strip()
            
            node = self.node_manager.get_node(node_name)
            if not node:
                self.status_message_signal.emit(f"Node {node_name} not found", self.STATUS_MSG_SHORT)
                return
                
            # Find all FBC tokens in the node
            fbc_tokens = [t for t in node.tokens.values() if t.token_type == "FBC"]
            if not fbc_tokens:
                self.status_message_signal.emit(f"No FBC tokens found in node {node_name}", self.STATUS_MSG_SHORT)
                return
                
            self.status_message_signal.emit(f"Processing {len(fbc_tokens)} FBC tokens in node {node_name}...", 0)
            
            # Queue commands for all FBC tokens
            for token in fbc_tokens:
                command_text = f"print from fbc io structure {token.token_id}0000"
                self.command_queue.add_command(command_text, token)
                
            self.status_message_signal.emit(f"Queued {len(fbc_tokens)} commands for node {node_name}", self.STATUS_MSG_SHORT)
            self.command_queue.start_processing()
            
        except Exception as e:
            self.status_message_signal.emit(f"Error processing FBC commands: {str(e)}", self.STATUS_MSG_MEDIUM)

    def _handle_queued_command_result(self, command: str, result: str, success: bool):
        """Handle completed commands from the queue"""
        if success:
            self.status_message_signal.emit(f"Command succeeded: {command}", 3000)
            logging.info(f"Command completed successfully: {command}\nResult: {result}")
        else:
            self.status_message_signal.emit(f"Command failed: {command} - {result}", 5000)
            logging.error(f"Command failed: {command}\nError: {result}")
    
    def _validate_node(self, item) -> bool:
        """Validate node structure before processing"""
        if not item or not item.parent():
            self.status_message_signal.emit("Invalid node structure", 3000)
            return False
        return True

    def _get_valid_tokens(self):
        """Retrieve and validate FBC tokens"""
        node = self.node_manager.get_selected_node()
        if not node:
            self.status_message_signal.emit("No node selected! Select a node first.", 3000)
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
        
        # Always display response in terminal for both manual and automatic commands
        self.telnet_output.append(response)
        self.telnet_output.moveCursor(QTextCursor.MoveOperation.End)
        
        if not automatic:
            # For manual commands: re-enable button and clear input
            self.execute_btn.setEnabled(True)
            self.cmd_input.clear()
            
            # Only write to log for manual commands when explicitly requested
            if self.current_token and response.strip():
                try:
                    logging.debug(f"Processing manual command for token {self.current_token.token_id}")
                    node = self.node_manager.get_node_by_token(self.current_token)
                    if node:
                        node_ip = node.ip_address.replace('.', '-') if node.ip_address else "unknown-ip"
                        log_path = self.log_writer.log_paths.get(self.current_token.token_id)
                        if not log_path:
                            logging.debug(f"Opening new log for token {self.current_token.token_id}")
                            log_path = self.log_writer.open_log(node.name, node_ip, self.current_token)
                            
                        self.log_writer.append_to_log(self.current_token.token_id, response, protocol=self.current_token.token_type)
                        logging.info(f"Successfully appended to log: {os.path.basename(log_path)}")
                        self.status_message_signal.emit(f"Command output appended to {os.path.basename(log_path)}", 3000)
                    else:
                        logging.warning(f"Node not found for token {self.current_token.token_id}")
                        self.status_message_signal.emit(f"Node not found for token {self.current_token.token_id}", 3000)
                except Exception as e:
                    logging.error(f"Failed to write to log: {str(e)}", exc_info=True)
                    self.status_message_signal.emit(f"Log write failed: {str(e)}", 5000)
        else:   # automatic commands
            if response.strip() and self.current_token:
                try:
                    # Check if token has a direct log path (from context menu)
                    log_path = getattr(self.current_token, 'log_path', None)
                    if log_path:
                        # Write directly to the specified log file
                        with open(log_path, 'a') as f:
                            f.write(response + "\n")
                        self.status_message_signal.emit(
                            f"Command output appended to {os.path.basename(log_path)}",
                            3000
                        )
                    else:
                        # Fall back to standard log writer
                        self.log_writer.append_to_log(
                            self.current_token.token_id,
                            response,
                            protocol=self.current_token.token_type
                        )
                        self.status_message_signal.emit(
                            "Command output logged",
                            3000
                        )
                except Exception as e:
                    logging.error(f"Log write error: {str(e)}")
                    self.status_message_signal.emit(f"Log write failed: {str(e)}", 5000)
            elif response.strip():
                self.status_message_signal.emit("Command executed successfully", 3000)
            else:
                self.status_message_signal.emit("Empty response received", 3000)
            
    def copy_to_log(self):
        """Copies current session content to selected token or log file"""
        selected_items = self.node_tree.selectedItems()
        if not selected_items:
            self.statusBar().showMessage("No item selected! Select a token or log file on the left.")
            return
        item = selected_items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            self.statusBar().showMessage("Selected item has no data")
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
                self.statusBar().showMessage("No content in current session")
                return

            # Handle based on item type
            if "log_path" in data:
                log_path = data["log_path"]
                # Write directly to the file
                with open(log_path, 'a') as f:
                    f.write(content + "\n")
                filename = os.path.basename(log_path)
                self.statusBar().showMessage(f"Content copied to {filename}")

            elif "token" in data:
                token_id = data["token"]
                node_name = data.get("node")
                token_type = data.get("token_type")
                if not node_name or not token_type:
                    self.statusBar().showMessage("Token item missing node or token_type")
                    return

                node = self.node_manager.get_node(node_name)
                if not node:
                    self.statusBar().showMessage(f"Node {node_name} not found")
                    return

                # Reconstruct the log path for display
                ip = node.ip_address.replace('.', '-')
                log_dir = os.path.join(self.node_manager.log_root, token_type, node_name)
                filename = f"{node_name}_{ip}_{token_id}.{token_type.lower()}"
                # Write using the log_writer
                self.log_writer.append_to_log(token_id, content, source=session_type)
                self.statusBar().showMessage(f"Content copied to {filename}")

            else:
                self.statusBar().showMessage("Unsupported item type")

        except Exception as e:
            self.statusBar().showMessage(f"Log write error: {str(e)}")
    
    def clear_terminal(self):
        """Clear the telnet output area"""
        self.telnet_output.clear()
        self.statusBar().showMessage("Terminal cleared", 3000)
    
    def clear_node_log(self):
        """Clear the currently selected node's log file"""
        selected_items = self.node_tree.selectedItems()
        if not selected_items:
            self.statusBar().showMessage("No item selected! Select a log file on the left.")
            return
        
        item = selected_items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or "log_path" not in data:
            self.statusBar().showMessage("Selected item is not a log file")
            return
            
        log_path = data["log_path"]
        try:
            # Open the file in write mode to truncate it
            with open(log_path, 'w') as f:
                f.truncate(0)
            self.statusBar().showMessage(f"Cleared log: {os.path.basename(log_path)}", 3000)
        except Exception as e:
            self.statusBar().showMessage(f"Error clearing log: {str(e)}")
    
    def open_log_file(self, item: QTreeWidgetItem, column: int):
        """Opens log file when double-clicked in tree view"""
        if data := item.data(0, Qt.ItemDataRole.UserRole):
            # All log items stored their path in "log_path"
            if "log_path" in data:
                log_path = data["log_path"]
                
                # Use system default application to open the log file
                try:
                    os.startfile(log_path)  # Windows-specific
                    self.statusBar().showMessage(f"Opened log file: {os.path.basename(log_path)}")
                except Exception as e:
                    self.statusBar().showMessage(f"Error opening file: {str(e)}")
                return True
        return False
        
    def closeEvent(self, event):
        """Cleanup on window close"""
        self.disconnect_telnet()
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
