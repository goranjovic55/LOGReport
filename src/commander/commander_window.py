"""
Commander Main Window
Dual-pane interface for managing nodes and sessions
"""
import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QTreeWidget, QTreeWidgetItem, 
    QTabWidget, QTextEdit, QVBoxLayout, QWidget, QHBoxLayout,
    QPushButton, QStatusBar, QLabel, QLineEdit, QGridLayout
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QTextCursor

# Import our components
from .node_manager import NodeManager
from .session_manager import SessionManager, SessionType, SessionConfig
from .log_writer import LogWriter
from .commands.telnet_commands import CommandResolver, CommandHistory
from .icons import NODE_ONLINE_ICON, NODE_OFFLINE_ICON, TOKEN_ICON

class CommanderWindow(QMainWindow):
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
        
        # Load configuration
        self.load_configuration()
        
        # Setup UI
        self.init_ui()
        
    def load_configuration(self):
        """Load node configuration"""
        loaded = self.node_manager.load_configuration()
        if not loaded:
            print("Error loading node configuration")
            
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
        
        # Node Tree Widget
        self.node_tree = QTreeWidget()
        self.node_tree.setHeaderLabels(["Nodes"])
        self.node_tree.setColumnWidth(0, 300)
        self.node_tree.setFont(QFont("Consolas", 10))
        self.populate_node_tree()
        self.node_tree.itemClicked.connect(self.on_node_selected)
        
        left_layout.addWidget(self.node_tree)
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
        
        # Connection Settings Panel
        connection_widget = QWidget()
        connection_layout = QGridLayout(connection_widget)
        connection_layout.setColumnStretch(1, 3)  # Input fields take more space
        
        # Status indicator
        status_indicator = QWidget()
        status_layout = QHBoxLayout(status_indicator)
        self.status_icon = QLabel("○")
        self.status_icon.setStyleSheet("font-size: 16pt; color: #888;")
        self.status_label = QLabel("Not connected")
        self.status_label.setStyleSheet("color: #AAA;")
        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_label)
        
        # IP Address Input
        ip_label = QLabel("IP:")
        ip_label.setStyleSheet("color: #CCC;")
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.1.101")
        self.ip_input.setStyleSheet("background:#252525; color:#EEE; border:1px solid #444; padding:4px;")
        
        # Port Input
        port_label = QLabel("Port:")
        port_label.setStyleSheet("color: #CCC;")
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("2077")
        self.port_input.setStyleSheet("background:#252525; color:#EEE; border:1px solid #444; padding:4px;")
        self.port_input.setFixedWidth(80)
        
        # Action buttons
        self.connect_btn = QPushButton("Connect")
        self.disconnect_btn = QPushButton("Disconnect")
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.disconnect_btn)
        
        # Add to grid layout
        connection_layout.addWidget(status_indicator, 0, 0, 1, 2)  # Span 2 columns
        
        connection_layout.addWidget(ip_label, 1, 0)
        connection_layout.addWidget(self.ip_input, 1, 1)
        
        connection_layout.addWidget(port_label, 2, 0)
        connection_layout.addWidget(self.port_input, 2, 1)
        
        connection_layout.addWidget(btn_container, 1, 2, 2, 1)  # Span 2 rows
        
        layout.addWidget(connection_widget, 1)
        
        # Connect signals
        self.connect_btn.clicked.connect(self.connect_telnet)
        self.disconnect_btn.clicked.connect(self.disconnect_telnet)
        
        # Set initial disabled state
        self.disconnect_btn.setEnabled(False)
        
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
        
        # Connection Bar
        connection_widget = QWidget()
        connection_layout = QHBoxLayout(connection_widget)
        
        self.status_label = QLabel("Status: Not connected")
        self.ip_label = QLabel("IP: Not set")
        self.connect_btn = QPushButton("Connect")
        self.disconnect_btn = QPushButton("Disconnect")
        
        # Add to layout
        connection_layout.addWidget(self.status_label)
        connection_layout.addStretch()
        connection_layout.addWidget(self.ip_label)
        connection_layout.addWidget(self.connect_btn)
        connection_layout.addWidget(self.disconnect_btn)
        
        layout.addWidget(connection_widget, 1)
        
        return tab
        
    def populate_node_tree(self):
        """Populates tree view with nodes and tokens"""
        self.node_tree.clear()
        
        for node in self.node_manager.get_all_nodes():
            # Create node item
            node_item = QTreeWidgetItem([f"{node.name} ({node.ip_address})"])
            if node.status == "online":
                node_item.setIcon(0, NODE_ONLINE_ICON)
            else:
                node_item.setIcon(0, NODE_OFFLINE_ICON)
            
            # Add tokens
            for token in node.tokens.values():
                token_label = (
                    f"{token.token_id} {token.token_type} "
                    f"{token.ip_address}:{token.port}"
                )
                token_item = QTreeWidgetItem([token_label])
                token_item.setData(0, Qt.ItemDataRole.UserRole, 
                                {"node": node.name, "token": token.token_id})
                token_item.setIcon(0, TOKEN_ICON)
                node_item.addChild(token_item)
            
            self.node_tree.addTopLevelItem(node_item)
        
        # Expand all by default
        self.node_tree.expandAll()
    
    def on_node_selected(self, item: QTreeWidgetItem, column: int):
        """Handles node/token selection in left pane"""
        if data := item.data(0, Qt.ItemDataRole.UserRole):
            # It's a token item
            node_name = data["node"]
            token_id = data["token"]
            token = self.node_manager.get_token(node_name, token_id)
            
            if not token:
                return
                
            self.current_token = token
            
            # Update IP fields with token info
            self.ip_input.setText(token.ip_address)
            self.port_input.setText(str(token.port))
            
            # Auto-open log file
            try:
                log_path = self.log_writer.open_log(
                    node_name, token_id, token.token_type
                )
                self.status_bar.showMessage(f"Log ready: {os.path.basename(log_path)}")
            except OSError as e:
                self.status_bar.showMessage(f"Error opening log: {str(e)}")
    
    def connect_telnet(self):
        """Connects to specified telnet server"""
        ip_address = self.ip_input.text().strip()
        port_str = self.port_input.text().strip()
            
        if not ip_address or not port_str:
            self.status_label.setText("Missing IP or Port")
            return
            
        try:
            port = int(port_str)
        except ValueError:
            self.status_label.setText("Invalid port number")
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
            self.telnet_session = self.session_manager.create_session(config)
            if self.telnet_session and self.telnet_session.is_connected:
                self.status_icon.setText("●")
                self.status_icon.setStyleSheet("font-size: 16pt; color: lime;")
                self.status_label.setText("Connected")
                self.telnet_output.clear()
                self.telnet_output.append(f"Connected to {ip_address}:{port}")
                self.connect_btn.setEnabled(False)
                self.disconnect_btn.setEnabled(True)
                self.cmd_input.setFocus()
            else:
                self.status_label.setText("Connection failed")
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
    
    def disconnect_telnet(self):
        """Disconnects from current telnet session"""
        try:
            self.session_manager.close_all_sessions()
            self.telnet_session = None
            self.status_icon.setText("○")
            self.status_icon.setStyleSheet("font-size: 16pt; color: #888;")
            self.status_label.setText("Not connected")
            self.telnet_output.append("\n>>> DISCONNECTED")
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
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
                f"Content copied to {self.current_token.name} log"
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
        
    def closeEvent(self, event):
        """Cleanup on window close"""
        self.disconnect_telnet()
        self.log_writer.close_all_logs()
        super().closeEvent(event)


def run():
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    # Dark theme styling
    app.setStyle("Fusion")
    
    # Create main window instance
    window = CommanderWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run()
