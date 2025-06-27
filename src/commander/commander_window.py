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
from .context_menu import ContextMenuMixin
from .telnet_handlers import TelnetHandlerMixin
from .log_ops import LogOperationsMixin
from .node_tree import NodeTreeMixin

class CommanderWindow(QMainWindow, ContextMenuMixin, TelnetHandlerMixin, LogOperationsMixin, NodeTreeMixin):
    """Main Commander window."""
        
            
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
