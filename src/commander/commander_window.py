"""
Commander Main Window
Dual-pane interface for managing nodes and sessions
"""
import sys
import os
import glob
from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QTreeWidget, QTreeWidgetItem, 
    QTabWidget, QTextEdit, QVBoxLayout, QWidget, QHBoxLayout,
    QPushButton, QStatusBar, QLabel, QLineEdit, QGridLayout
)
from PyQt6.QtCore import Qt, QSize, QSettings
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
from .icons import get_node_online_icon, get_node_offline_icon, get_token_icon

# Centralized Qt application initialization
from .qt_init import initialize_qt

class CommanderWindow(QMainWindow):
    """Main Commander window."""
        
    def generate_fieldbus_command(self, item_data):
        """Generates and sends the fieldbus structure command for FBC tokens"""
        token_id = item_data["token"]
        command_text = f"print from fieldbus io structure {token_id}0000"
        
        # Set command in telnet input
        self.cmd_input.setPlainText(command_text)
        
        # Navigate to telnet tab if needed
        self.session_tabs.setCurrentWidget(self.telnet_tab)
        
        # Focus command input
        self.cmd_input.setFocus()
        
        self.status_bar.showMessage(f"Command set: {command_text} - Press Execute to run")

    def determine_token_type(self, token_id):
        """Simple helper to determine token type based on token ID"""
        # For now, all log files are FBC - this can be extended later
        return "FBC"
        
    def show_context_menu(self, position):
        """Context menu handler for node tree items with detailed logging"""
        print("[Context Menu] Received show_context_menu request")
        try:
            item = self.node_tree.itemAt(position)
            if not item:
                print("[Context Menu] No item at position")
                return
                
            print(f"[Context Menu] Found item: {item.text(0)}")
            data = item.data(0, Qt.ItemDataRole.UserRole)
            menu = QMenu(self.node_tree)
            added_actions = False

            # Check if this is a top-level node with FBC children
            if not data and item.parent() is None:
                print("[Context Menu] Processing top-level node")
                node_name = item.text(0).split(' ')[0]  # Extract node name from text
                print(f"[Context Menu] Checking node '{node_name}' for FBC children")
                # Check if node has FBC children
                for i in range(item.childCount()):
                    child = item.child(i)
                    print(f"[Context Menu] Checking child: {child.text(0)}")
                    if child.text(0) == "FBC" and child.childCount() > 0:
                        print(f"[Context Menu] Found {child.childCount()} FBC tokens in node '{node_name}'")
                        # Add "Print Fieldbus Structure" for the node
                        action_text = f"Print FieldBus Structure for {node_name}"
                        action = QAction(action_text, self)
                        action.triggered.connect(lambda: self.process_fieldbus_node(node_name))
                        menu.addAction(action)
                        added_actions = True
                        break
            # Handle token items
            elif data and isinstance(data, dict):
                token_type = data.get("token_type", "").upper()  # Normalize to uppercase
                token_id = data.get("token", None)
                node_name = data.get("node", "Unknown")
                
                print(f"[Context Menu] Token type: '{token_type}', Token ID: {token_id}, Node: {node_name}")
                
                if token_id:
                    print(f"[Context Menu] Processing token item: type={token_type}, id={token_id}")
                    
                    if token_type == "FBC":
                        print("[Context Menu] Creating context menu for FBC item")
                        action_text = f"Print FieldBus Structure (Token {token_id})"
                        action = QAction(action_text, self)
                        action.triggered.connect(lambda: self.process_fieldbus_command(token_id))
                        menu.addAction(action)
                        added_actions = True
                        
                    elif token_type == "RPC":
                        print("[Context Menu] Creating context menu for RPC item")
                        
                        # Print Rupi Counters action
                        print_action = QAction(f"Print Rupi Counters (Token {token_id})", self)
                        print_action.triggered.connect(lambda: self.process_rpc_command(token_id, "print"))
                        menu.addAction(print_action)
                        
                        # Clear Rupi Counters action
                        clear_action = QAction(f"Clear Rupi Counters (Token {token_id})", self)
                        clear_action.triggered.connect(lambda: self.process_rpc_command(token_id, "clear"))
                        menu.addAction(clear_action)
                        added_actions = True
            
            if added_actions:
                # Show menu at cursor position
                menu.exec(self.node_tree.viewport().mapToGlobal(position))
                print(f"[Context Menu] Displayed menu with {menu.actions().count()} actions")
            else:
                print(f"[Context Menu] No applicable actions for this item")
        except Exception as e:
            print(f"[Context Menu] Error: {str(e)}")
            
    def process_fieldbus_node(self, node_name):
        """Process fieldbus structure commands for all FBC tokens in a node"""
        node = self.node_manager.get_node(node_name)
        if not node:
            self.status_bar.showMessage(f"Node {node_name} not found", 3000)
            return
            
        # Find all FBC tokens in the node
        fbc_tokens = [t for t in node.tokens.values() if t.token_type == "FBC"]
        if not fbc_tokens:
            self.status_bar.showMessage(f"No FBC tokens found in node {node_name}", 3000)
            return
            
        self.status_bar.showMessage(f"Processing {len(fbc_tokens)} FBC tokens in node {node_name}...", 0)
        
        for token in fbc_tokens:
            self.current_token = token
            self.process_fieldbus_command(token.token_id)
            
        self.status_bar.showMessage(f"Fieldbus commands executed for {len(fbc_tokens)} tokens", 3000)
            
    def process_fieldbus_command(self, token_id):
        """Process fieldbus structure command and automatically execute and log"""
        command_text = f"print from fieldbus io structure {token_id}0000"
        
        try:
            # Set command in telnet input
            self.cmd_input.setPlainText(command_text)
            
            # Navigate to telnet tab
            self.session_tabs.setCurrentWidget(self.telnet_tab)
            
            # Focus command input
            self.cmd_input.setFocus()
            
            # Show status message
            self.status_bar.showMessage(f"Executing: {command_text}...", 3000)
            
            # Execute command immediately
            if self.telnet_session and self.telnet_session.is_connected:
                # Execute command and capture output
                output = self.execute_telnet_command(automatic=True)
                
                # Write output to log file
                if self.current_token and self.current_token.log_path:
                    # Normalize path and check existence
                    normalized_path = os.path.normpath(self.current_token.log_path)
                    if not os.path.exists(normalized_path):
                        raise FileNotFoundError(f"Log file not found: {normalized_path}")
                    
                    with open(normalized_path, 'a') as f:
                        f.write(output + '\n')
                    self.status_bar.showMessage(f"Command output written to log", 3000)
                else:
                    self.status_bar.showMessage(f"Log path not found for token {token_id}", 3000)
        except FileNotFoundError as e:
            self.status_bar.showMessage(f"File not found: {str(e)}", 3000)
            print(f"File not found: {e}")
        except Exception as e:
            self.status_bar.showMessage(f"Error: {str(e)}", 3000)
            print(f"Error processing fieldbus command: {e}")
            
    def process_rpc_command(self, token_id, action_type):
        """Process RPC commands (print/clear Rupi counters)"""
        if action_type == "print":
            command_text = f"print from rpc counters {token_id}0000"
        elif action_type == "clear":
            command_text = f"clear rpc counters {token_id}0000"
        else:
            return
            
        try:
            # Set command in telnet input
            self.cmd_input.setPlainText(command_text)
            
            # Navigate to telnet tab
            self.session_tabs.setCurrentWidget(self.telnet_tab)
            
            # Focus command input
            self.cmd_input.setFocus()
            
            # Show status message
            action_name = "Print" if action_type == "print" else "Clear"
            self.status_bar.showMessage(
                f"{action_name} Rupi counters command set for token {token_id}",
                3000
            )
        except Exception as e:
            print(f"Error processing RPC command: {e}")
            
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Commander LogCreator v1.0")
        self.setMinimumSize(1200, 800)
        
        # Load application settings
        self.settings = QSettings("CommanderLogCreator", "Settings")
        
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
        self.node_manager = NodeManager()
        self.session_manager = SessionManager()
        self.log_writer = LogWriter()
        self.command_resolver = CommandResolver()
        self.command_history = CommandHistory()
        
        # State tracking
        self.current_token = None
        self.telnet_session = None
        self.telnet_active = False
        
        # Setup UI first - we'll initialize with empty tree
        self.init_ui()
        
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
            print(f"Error loading default configuration: {e}")
            
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
                print("Error loading node configuration")
    
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
        
    def generate_fieldbus_command(self, item_data):
        """Generates and sends the fieldbus structure command for FBC tokens"""
        token_id = item_data["token"]
        command_text = f"print from fieldbus io structure {token_id}0000"
        
        # Set command in telnet input
        self.cmd_input.setPlainText(command_text)
        
        # Navigate to telnet tab if needed
        self.session_tabs.setCurrentWidget(self.telnet_tab)
        
        # Focus command input
        self.cmd_input.setFocus()
        
        self.status_bar.showMessage(f"Command set: {command_text} - Press Execute to run")
        
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
        print("Node tree event filter installed")
        
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
        print("Node tree context menu handling installed")

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
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Welcome to Commander LogCreator")
        
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
        """Populates tree view with nodes and sections for FBC, RPC, LOG, LIS with relevant files"""
        self.node_tree.clear()
        
        for node in self.node_manager.get_all_nodes():
            # Create node item
            node_item = QTreeWidgetItem([f"{node.name} ({node.ip_address})"])
            if node.status == "online":
                node_item.setIcon(0, get_node_online_icon())
            else:
                node_item.setIcon(0, get_node_offline_icon())
            
            # Ensure log_root is set
            log_root = self.node_manager.log_root
            if not log_root or not os.path.isdir(log_root):
                # Add placeholder if log root not set
                no_folder = QTreeWidgetItem(["Please set log root folder"])
                no_folder.setIcon(0, QIcon(":/icons/warning.png"))
                node_item.addChild(no_folder)
                self.node_tree.addTopLevelItem(node_item)
                continue
            
            # Create top-level sections
            sections = {
                "FBC": QTreeWidgetItem(["FBC"]),
                "RPC": QTreeWidgetItem(["RPC"]),
                "LOG": QTreeWidgetItem(["LOG"]),
                "LIS": QTreeWidgetItem(["LIS"])
            }
            
            # Set icons for sections
            sections["FBC"].setIcon(0, get_token_icon())
            sections["RPC"].setIcon(0, get_token_icon())
            sections["LOG"].setIcon(0, QIcon(":/icons/page.png"))
            sections["LIS"].setIcon(0, QIcon(":/icons/page.png"))
            
            # Add LOG files to LOG section (single implementation)
            added_log = False
            log_dir = os.path.join(log_root, "LOG")
            log_pattern = f"{node.name}_{node.ip_address.replace('.','-')}.log"
            log_files = glob.glob(os.path.join(log_dir, log_pattern))
            for log_path in log_files:
                if os.path.isfile(log_path):
                    log_filename = os.path.basename(log_path)
                    log_item = QTreeWidgetItem([f"📝 {log_filename}"])
                    log_item.setData(0, Qt.ItemDataRole.UserRole,
                                   {"log_path": log_path})
                    log_item.setIcon(0, QIcon(":/icons/page.png"))
                    sections["LOG"].addChild(log_item)
                    added_log = True
            
            # Add FBC files to FBC section (from FBC/node_name folder)
            added_fbc = False
            fbc_dir = os.path.join(log_root, "FBC", node.name)
            if os.path.isdir(fbc_dir):
                for filename in os.listdir(fbc_dir):
                    if filename.lower().endswith((".fbc", ".log", ".txt")) and filename.startswith(node.name + "_"):
                        file_path = os.path.join(fbc_dir, filename)
                        if os.path.isfile(file_path):
                            # Extract token from filename: AP01m_192-168-0-11_162.fbc -> token is the number part (162)
                            # Pattern: {node.name}_{ip}_{token}.fbc
                            parts = filename.split('_')
                            token_id = parts[-1].split('.')[0]  # Get 162 from AP01m_192-168-0-11_162.fbc
                            file_item = QTreeWidgetItem([f"📝 {filename}"])
                            file_item.setData(0, Qt.ItemDataRole.UserRole,
                                            {"log_path": file_path,
                                             "token": token_id,
                                             "token_type": "FBC",
                                             "node": node.name})
                            file_item.setIcon(0, QIcon(":/icons/page.png"))
                            sections["FBC"].addChild(file_item)
                            added_fbc = True
            
            # Add RPC files to RPC section (from RPC/node_name folder)
            added_rpc = False
            rpc_dir = os.path.join(log_root, "RPC", node.name)
            if os.path.isdir(rpc_dir):
                for filename in os.listdir(rpc_dir):
                    if filename.lower().endswith((".rpc", ".log", ".txt")) and filename.startswith(node.name + "_"):
                        file_path = os.path.join(rpc_dir, filename)
                        if os.path.isfile(file_path):
                            # Extract token ID from filename: AP01r_192-168-0-12_363.rpc -> token ID = 363
                            token_id = filename.rsplit('_', 1)[-1].split('.')[0]
                            
                            file_item = QTreeWidgetItem([f"📝 {filename}"])
                            file_item.setData(0, Qt.ItemDataRole.UserRole,
                                            {"log_path": file_path,
                                             "node": node.name,
                                             "token": token_id,
                                             "token_type": "RPC"})
                            file_item.setIcon(0, QIcon(":/icons/page.png"))
                            sections["RPC"].addChild(file_item)
                            added_rpc = True
            
            # Add LIS files to LIS section (from LIS/node_name folder)
            added_lis = False
            lis_dir = os.path.join(log_root, "LIS", node.name)
            if os.path.isdir(lis_dir):
                for filename in os.listdir(lis_dir):
                    if filename.endswith(".lis") and filename.startswith(node.name + "_"):
                        file_path = os.path.join(lis_dir, filename)
                        if os.path.isfile(file_path):
                            file_item = QTreeWidgetItem([f"📝 {filename}"])
                            file_item.setData(0, Qt.ItemDataRole.UserRole,
                                            {"log_path": file_path})
                            file_item.setIcon(0, QIcon(":/icons/page.png"))
                            sections["LIS"].addChild(file_item)
                            added_lis = True
            
            # Add only non-empty sections to the node
            if added_fbc:
                node_item.addChild(sections["FBC"])
            if added_rpc:
                node_item.addChild(sections["RPC"])
                node_item.addChild(sections["LOG"])
            if added_lis:
                node_item.addChild(sections["LIS"])
            
            # Add warning if no data found
            if not (added_fbc or added_rpc or added_log or added_lis):
                no_files = QTreeWidgetItem(["No files found for this node"])
                no_files.setIcon(0, QIcon(":/icons/warning.png"))
                node_item.addChild(no_files)
            
            self.node_tree.addTopLevelItem(node_item)
        
        # Expand all by default
        self.node_tree.expandAll()
    
    def on_node_selected(self, item: QTreeWidgetItem, column: int):
        """Handles node/token selection in left pane"""
        if data := item.data(0, Qt.ItemDataRole.UserRole):
            # Check if we have token and node information in the data
            token_id = data.get("token")
            node_name = data.get("node")
            
            # If we have both token and node, set current token
            if node_name and token_id:
                token = self.node_manager.get_token(node_name, token_id)
                
                if not token:
                    return
                    
                self.current_token = token
                
                # Update ConnectionBar based on token type
                if token.token_type == "FBC": # Telnet
                    self.session_tabs.setCurrentWidget(self.telnet_tab)
                    
                    # Update status only if not already connected to this token
                    if (self.telnet_session and self.telnet_session.is_connected and
                        self.telnet_session.config.host == token.ip_address and
                        self.telnet_session.config.port == token.port):
                        # Already connected to this token - keep status
                        pass
                    else:
                        self.telnet_connection_bar.update_status(ConnectionState.DISCONNECTED)
                elif token.token_type == "VNC":
                    self.session_tabs.setCurrentWidget(self.vnc_tab)
                    if hasattr(self, 'vnc_connection_bar'):
                        self.vnc_connection_bar.ip_edit.setText(token.ip_address)
                        self.vnc_connection_bar.port_edit.setText(str(token.port))
                        self.vnc_connection_bar.update_status(ConnectionState.DISCONNECTED)
                elif token.token_type == "FTP":
                    self.session_tabs.setCurrentWidget(self.ftp_tab)
                    if hasattr(self, 'ftp_connection_bar'):
                        self.ftp_connection_bar.ip_edit.setText(token.ip_address)
                        self.ftp_connection_bar.port_edit.setText(str(token.port))
                        self.ftp_connection_bar.update_status(ConnectionState.DISCONNECTED)
                
                # Auto-open log file
                try:
                    log_path = self.log_writer.open_log(
                        node_name, token_id, token.token_type
                    )
                    self.status_bar.showMessage(f"Log ready: {os.path.basename(log_path)}")
                except OSError as e:
                    self.status_bar.showMessage(f"Error opening log: {str(e)}")

    def toggle_telnet_connection(self, connect: bool):
        """Toggles connection/disconnection for Telnet tab"""
        # Get IP and port directly from input fields
        ip_address, port_text = self.telnet_connection_bar.get_address()
        if not ip_address or not port_text:
            self.status_bar.showMessage("IP and port are required.")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
            return
        
        try:
            port = int(port_text)
        except ValueError:
            self.status_bar.showMessage(f"Invalid port number: {port_text}")
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
            self.status_bar.showMessage("Connection failed")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
            return False
            
        except socket.timeout as e:
            self.status_bar.showMessage(f"Connection timed out: {str(e)}")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
        except ConnectionRefusedError as e:
            self.status_bar.showMessage(f"Connection refused: {str(e)}")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
        except Exception as e:
            self.status_bar.showMessage(f"Connection error: {str(e)}")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
            return False
    
    def disconnect_telnet(self):
        """Disconnects from current telnet session"""
        try:
            self.session_manager.close_all_sessions()
            self.telnet_session = None
            self.telnet_connection_bar.update_status(ConnectionState.DISCONNECTED)
            self.telnet_output.append("\n>>> DISCONNECTED")
        except Exception as e:
            self.telnet_output.append(f"Error: {str(e)}")
            
    def execute_telnet_command(self, automatic=False):
        """Executes command in Telnet session"""
        if not self.telnet_session:
            if not automatic:
                self.status_bar.showMessage("Create a Telnet session first!")
            return ""

        command = self.cmd_input.toPlainText().strip()
        if not command:
            return ""

        if not automatic:
            self.command_history.add(command)
        
        # Display user command in output
        if not automatic:
            self.telnet_output.append(f"> {command}")
            self.telnet_output.moveCursor(QTextCursor.MoveOperation.End)
        
        try:
            # Resolve command with context if needed
            token_id = self.current_token.token_id if self.current_token else ""
            resolved_cmd = self.command_resolver.resolve(command, token_id)
            
            # Execute command
            response = self.telnet_session.send_command(resolved_cmd, timeout=5)
            
            # Display response
            if not automatic:
                self.telnet_output.append(response)
            
            # Update connection status to CONNECTED after successful command execution
            self.telnet_connection_bar.update_status(ConnectionState.CONNECTED)
            
        except Exception as e:
            error_msg = f"ERROR: {str(e)}"
            if not automatic:
                self.telnet_output.append(error_msg)
            return error_msg
            
        # Clear input field for next command
        if not automatic:
            self.cmd_input.clear()
            self.telnet_output.moveCursor(QTextCursor.MoveOperation.End)
            
        return response
            
    def copy_to_log(self):
        """Copies current session content to selected token or log file"""
        selected_items = self.node_tree.selectedItems()
        if not selected_items:
            self.status_bar.showMessage("No item selected! Select a token or log file on the left.")
            return
        item = selected_items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            self.status_bar.showMessage("Selected item has no data")
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
                self.status_bar.showMessage("No content in current session")
                return

            # Handle based on item type
            if "log_path" in data:
                log_path = data["log_path"]
                # Write directly to the file
                with open(log_path, 'a') as f:
                    f.write(content + "\n")
                filename = os.path.basename(log_path)
                self.status_bar.showMessage(f"Content copied to {filename}")

            elif "token" in data:
                token_id = data["token"]
                node_name = data.get("node")
                token_type = data.get("token_type")
                if not node_name or not token_type:
                    self.status_bar.showMessage("Token item missing node or token_type")
                    return

                node = self.node_manager.get_node(node_name)
                if not node:
                    self.status_bar.showMessage(f"Node {node_name} not found")
                    return

                # Reconstruct the log path for display
                ip = node.ip_address.replace('.', '-')
                log_dir = os.path.join(self.node_manager.log_root, token_type, node_name)
                filename = f"{node_name}_{ip}_{token_id}.{token_type.lower()}"
                # Write using the log_writer
                self.log_writer.append_to_log(token_id, content, source=session_type)
                self.status_bar.showMessage(f"Content copied to {filename}")

            else:
                self.status_bar.showMessage("Unsupported item type")

        except Exception as e:
            self.status_bar.showMessage(f"Log write error: {str(e)}")
    
    def clear_terminal(self):
        """Clear the telnet output area"""
        self.telnet_output.clear()
        self.status_bar.showMessage("Terminal cleared", 3000)
    
    def clear_node_log(self):
        """Clear the currently selected node's log file"""
        selected_items = self.node_tree.selectedItems()
        if not selected_items:
            self.status_bar.showMessage("No item selected! Select a log file on the left.")
            return
        
        item = selected_items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or "log_path" not in data:
            self.status_bar.showMessage("Selected item is not a log file")
            return
            
        log_path = data["log_path"]
        try:
            # Open the file in write mode to truncate it
            with open(log_path, 'w') as f:
                f.truncate(0)
            self.status_bar.showMessage(f"Cleared log: {os.path.basename(log_path)}", 3000)
        except Exception as e:
            self.status_bar.showMessage(f"Error clearing log: {str(e)}")
    
    def open_log_file(self, item: QTreeWidgetItem, column: int):
        """Opens log file when double-clicked in tree view"""
        if data := item.data(0, Qt.ItemDataRole.UserRole):
            # All log items stored their path in "log_path"
            if "log_path" in data:
                log_path = data["log_path"]
                
                # Use system default application to open the log file
                try:
                    os.startfile(log_path)  # Windows-specific
                    self.status_bar.showMessage(f"Opened log file: {os.path.basename(log_path)}")
                except Exception as e:
                    self.status_bar.showMessage(f"Error opening file: {str(e)}")
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
