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
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QTextCursor

# Enum for connection states
from enum import Enum

class ConnectionState(Enum):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    ERROR = 3

# Import our components
from .node_manager import NodeManager
from .session_manager import SessionManager, SessionType, SessionConfig
from .log_writer import LogWriter
from .commands.telnet_commands import CommandResolver, CommandHistory
from .icons import get_node_online_icon, get_node_offline_icon, get_token_icon

# Centralized Qt application initialization
from .qt_init import initialize_qt

class CommanderWindow(QMainWindow):
    class ConnectionBar(QWidget):
        """Connection bar widget moved inside CommanderWindow to avoid module-level GUI"""
        # Define a custom signal to communicate button clicks
        connection_requested = pyqtSignal(bool) # True for connect, False for disconnect

        def __init__(self, ip_address: str, port: int):
            super().__init__()
            self.layout = QHBoxLayout()
            self.address_label = QLabel(f"{ip_address}:{port}")
            self.status_icon = QLabel("○") # Default disconnected icon
            self.connect_btn = QPushButton("Connect")
            
            self.layout.addWidget(self.address_label)
            self.layout.addWidget(self.status_icon)
            self.layout.addWidget(self.connect_btn)
            self.layout.addStretch() # Push buttons to the right
            self.setLayout(self.layout)
            
            # Connect the button click to our internal handler
            self.connect_btn.clicked.connect(self._on_connect_button_clicked)
            
            # Initial status
            self.update_status(ConnectionState.DISCONNECTED)
        
        def update_status(self, state: ConnectionState):
            icons = {
                ConnectionState.DISCONNECTED: "○",
                ConnectionState.CONNECTING: "◑",
                ConnectionState.CONNECTED: "●",
                ConnectionState.ERROR: "⨯"
            }
            colors = {
                ConnectionState.DISCONNECTED: "#888",
                ConnectionState.CONNECTING: "orange",
                ConnectionState.CONNECTED: "lime",
                ConnectionState.ERROR: "red"
            }
            
            self.status_icon.setText(icons[state])
            self.status_icon.setStyleSheet(f"font-size: 16pt; color: {colors[state]};")
            
            # Only change button text based on connection state
            if state == ConnectionState.CONNECTED:
                self.connect_btn.setText("Disconnect")
            else:
                self.connect_btn.setText("Connect")
        
        def _on_connect_button_clicked(self):
            """Internal slot to handle the connect/disconnect button click.
            Emits connection_requested signal.
            """
            if self.connect_btn.text() == "Connect":
                self.connection_requested.emit(True) # Request a connection
            else:
                self.connection_requested.emit(False) # Request a disconnection
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Commander LogCreator v1.0")
        self.setMinimumSize(1200, 800)
        
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
            if os.path.exists(self.node_manager.config_path):
                if self.node_manager.load_configuration():
                    self.node_manager.scan_log_files()
                    self.populate_node_tree()
        except Exception as e:
            print(f"Error loading default configuration: {e}")
        
    def load_configuration(self):
        """Load node configuration from selected file"""
        from PyQt6.QtWidgets import QFileDialog
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
        
        left_layout.addWidget(self.node_tree, 1)  # Add stretch factor
        splitter.addWidget(left_pane)
        
        # Create buttons for the window
        self.execute_btn = QPushButton("Execute")
        self.copy_to_log_btn = QPushButton("Copy to Node Log")
        self.stop_btn = QPushButton("Stop Session")
        self.save_session_btn = QPushButton("Save Session")
        
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
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.save_session_btn)
        
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
        self.stop_btn.clicked.connect(self.stop_active_session)
        self.save_session_btn.clicked.connect(self.save_session)
    
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
        self.telnet_connection_bar = self.ConnectionBar(ip_address="", port=0) # Placeholder
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
        connection_bar = self.ConnectionBar(ip_address="", port=0) 
        
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
            
            # Add FBC files to FBC section
            added_fbc = False
            for token in node.tokens.values():
                if token.token_type == "FBC" and token.log_path and os.path.exists(token.log_path):
                    log_filename = os.path.basename(token.log_path)
                    log_item = QTreeWidgetItem([f"📝 {log_filename}"])
                    log_item.setData(0, Qt.ItemDataRole.UserRole,
                                   {"log_path": token.log_path, "node": node.name, "token": token.token_id})
                    log_item.setIcon(0, QIcon(":/icons/page.png"))
                    sections["FBC"].addChild(log_item)
                    added_fbc = True
            
            # Add RPC files to RPC section
            added_rpc = False
            for token in node.tokens.values():
                if token.token_type == "RPC" and token.log_path and os.path.exists(token.log_path):
                    log_filename = os.path.basename(token.log_path)
                    log_item = QTreeWidgetItem([f"📝 {log_filename}"])
                    log_item.setData(0, Qt.ItemDataRole.UserRole,
                                   {"log_path": token.log_path, "node": node.name, "token": token.token_id})
                    log_item.setIcon(0, QIcon(":/icons/page.png"))
                    sections["RPC"].addChild(log_item)
                    added_rpc = True
            
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
            
            # Add LOG files to LOG section
            added_log = False
            logs_dir = os.path.join(log_root, "LOG")
            # Only show the main node log file matching the pattern
            log_pattern = f"{node.name}_{node.ip_address.replace('.','-')}.log"
            log_path = os.path.join(logs_dir, log_pattern)
            if os.path.isfile(log_path):
                filename = os.path.basename(log_path)
                file_item = QTreeWidgetItem([f"📝 {filename}"])
                file_item.setData(0, Qt.ItemDataRole.UserRole,
                                {"log_path": log_path})
                file_item.setIcon(0, QIcon(":/icons/page.png"))
                sections["LOG"].addChild(file_item)
                added_log = True
            
            # Add FBC files to FBC section (from FBC/node_name folder)
            added_fbc = False
            fbc_dir = os.path.join(log_root, "FBC", node.name)
            if os.path.isdir(fbc_dir):
                for filename in os.listdir(fbc_dir):
                    if filename.endswith(".fbc") and filename.startswith(node.name + "_"):
                        file_path = os.path.join(fbc_dir, filename)
                        if os.path.isfile(file_path):
                            file_item = QTreeWidgetItem([f"📝 {filename}"])
                            file_item.setData(0, Qt.ItemDataRole.UserRole,
                                            {"log_path": file_path})
                            file_item.setIcon(0, QIcon(":/icons/page.png"))
                            sections["FBC"].addChild(file_item)
                            added_fbc = True
            
            # Add RPC files to RPC section (from RPC/node_name folder)
            added_rpc = False
            rpc_dir = os.path.join(log_root, "RPC", node.name)
            if os.path.isdir(rpc_dir):
                for filename in os.listdir(rpc_dir):
                    if filename.endswith(".rpc") and filename.startswith(node.name + "_"):
                        file_path = os.path.join(rpc_dir, filename)
                        if os.path.isfile(file_path):
                            file_item = QTreeWidgetItem([f"📝 {filename}"])
                            file_item.setData(0, Qt.ItemDataRole.UserRole,
                                            {"log_path": file_path})
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
            if added_log:
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
            # Check if log item
            if "log_path" in data:
                # Not handling log items further yet
                return
            
            # It's a token item
            token_id = data.get("token")
            node_name = data.get("node")
            if not node_name or not token_id:
                return
                
            token = self.node_manager.get_token(node_name, token_id)
            
            if not token:
                return
                
            self.current_token = token
            
            # Update ConnectionBar based on token type
            if token.token_type == "FBC": # Telnet
                self.session_tabs.setCurrentWidget(self.telnet_tab)
                self.telnet_connection_bar.address_label.setText(f"{token.ip_address}:{token.port}")
                self.telnet_connection_bar.update_status(ConnectionState.DISCONNECTED) # Reset status
            elif token.token_type == "VNC":
                self.session_tabs.setCurrentWidget(self.vnc_tab)
                if hasattr(self, 'vnc_connection_bar'):
                    self.vnc_connection_bar.address_label.setText(f"{token.ip_address}:{token.port}")
                    self.vnc_connection_bar.update_status(ConnectionState.DISCONNECTED)
            elif token.token_type == "FTP":
                self.session_tabs.setCurrentWidget(self.ftp_tab)
                if hasattr(self, 'ftp_connection_bar'):
                    self.ftp_connection_bar.address_label.setText(f"{token.ip_address}:{token.port}")
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
        # Extract IP and Port from the ConnectionBar's label
        ip_port_text = self.telnet_connection_bar.address_label.text()
        if ':' not in ip_port_text:
            self.status_bar.showMessage("Invalid IP:Port format in Connection Bar.")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
            return
        
        ip_address, port_str = ip_port_text.split(':')
        
        if not ip_address or not port_str:
            self.status_bar.showMessage("Please select a node/token with valid IP/Port.")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR) # Indicate error on bar
            return
            
        if connect:
            self.connect_telnet()
        else:
            self.disconnect_telnet()

    def connect_telnet(self):
        """Connects to specified telnet server"""
        # Get IP and Port from the ConnectionBar's address label
        ip_port_text = self.telnet_connection_bar.address_label.text()
        if ':' not in ip_port_text:
             # This case should ideally be caught by toggle_telnet_connection, but for safety:
            self.status_bar.showMessage("Missing IP or Port in Connection Bar for connection attempt.")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
            return
        ip_address, port_str = ip_port_text.split(':')
        
            
        try:
            port = int(port_str)
        except ValueError:
            self.status_bar.showMessage("Invalid port number.")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
            return
            
        # Configure telnet connection
        config = SessionConfig(
            host=ip_address,
            port=port,
            session_type=SessionType.TELNET,
            username="admin",
            password="password"
        )
        
        try:
            self.telnet_connection_bar.update_status(ConnectionState.CONNECTING)
            self.telnet_session = self.session_manager.create_session(config)
            if self.telnet_session and self.telnet_session.is_connected:
                self.telnet_connection_bar.update_status(ConnectionState.CONNECTED)
                self.telnet_output.clear()
                self.telnet_output.append(f"Connected to {ip_address}:{port}")
                self.cmd_input.setFocus()
            else:
                self.status_bar.showMessage("Connection failed.")
                self.telnet_connection_bar.update_status(ConnectionState.ERROR)
        except Exception as e:
            self.status_bar.showMessage(f"Error: {str(e)}")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
    
    def disconnect_telnet(self):
        """Disconnects from current telnet session"""
        try:
            self.session_manager.close_all_sessions()
            self.telnet_session = None
            self.telnet_connection_bar.update_status(ConnectionState.DISCONNECTED)
            self.telnet_output.append("\n>>> DISCONNECTED")
        except Exception as e:
            self.telnet_output.append(f"Error: {str(e)}")
            
    def execute_telnet_command(self):
        """Executes command in Telnet session"""
        if not self.telnet_session:
            self.status_bar.showMessage("Create a Telnet session first!")
            return
            
        command = self.cmd_input.toPlainText().strip()
        if not command:
            return
            
        self.command_history.add(command)
        
        # Display user command in output
        self.telnet_output.append(f"> {command}")
        self.telnet_output.moveCursor(QTextCursor.MoveOperation.End)
        
        try:
            # Resolve command with context if needed
            token_id = self.current_token.token_id if self.current_token else ""
            resolved_cmd = self.command_resolver.resolve(command, token_id)
            
            # Execute command
            response = self.telnet_session.send_command(resolved_cmd, timeout=5)
            
            # Display response
            self.telnet_output.append(response)
            
        except Exception as e:
            self.telnet_output.append(f"ERROR: {str(e)}")
            
        # Clear input field for next command
        self.cmd_input.clear()
        self.telnet_output.moveCursor(QTextCursor.MoveOperation.End)
            
    def copy_to_log(self):
        """Copies current session content to active token log"""
        if not self.current_token:
            self.status_bar.showMessage("No token selected! Select a token on the left.")
            return
            
        tab_index = self.session_tabs.currentIndex()
        session_type = self.session_tabs.tabText(tab_index)
        
        try:
            # Telnet tab has special output handling
            if session_type == "Telnet":
                content = self.telnet_output.toPlainText()
            else:
                # For VNC and FTP
                tab_widget = self.session_tabs.widget(tab_index)
                content_widget = tab_widget.layout().itemAt(0).widget()
                if isinstance(content_widget, QTextEdit):
                    content = content_widget.toPlainText()
                else:
                    return
                    
            # Don't copy empty sessions
            if not content:
                self.status_bar.showMessage("No content in current session")
                return
                    
            # Write to log
            self.log_writer.append_to_log(
                self.current_token.token_id,
                content,
                source=session_type
            )
            self.status_bar.showMessage(
                f"Content copied to {self.current_token.token_id} log"
            )
        except Exception as e:
            self.status_bar.showMessage(f"Log write error: {str(e)}")
    
    def stop_active_session(self):
        """Stops any active session on current tab"""
        tab_index = self.session_tabs.currentIndex()
        session_type = self.session_tabs.tabText(tab_index).upper()
        
        if session_type == "TELNET":
            self.disconnect_telnet()
        
        # TODO: Implement for other sessions
        self.status_bar.showMessage(f"{session_type} session stopped")
    
    def save_session(self):
        """Saves session state"""
        self.status_bar.showMessage("Session save functionality not yet implemented")
        return True
    
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
