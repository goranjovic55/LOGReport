"""
Commander UI Factory - Creates UI components for the Commander window
"""
from PyQt6.QtWidgets import (
    QSplitter, QTreeWidget, QTreeWidgetItem, QTabWidget, QTextEdit, 
    QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ..ui.node_tree_view import NodeTreeView
from ..widgets import ConnectionBar


class CommanderUIFactory:
    """Factory for creating UI components for the Commander window"""
    
    def __init__(self):
        self.node_tree_view = None
        self.session_tabs = None
        self.telnet_tab = None
        self.vnc_tab = None
        self.ftp_tab = None
        self.telnet_output = None
        self.cmd_input = None
        self.execute_btn = None
        self.copy_to_log_btn = None
        self.clear_terminal_btn = None
        self.clear_node_log_btn = None
        self.telnet_connection_bar = None
        self.vnc_connection_bar = None
        self.ftp_connection_bar = None
        self.vnc_content_output = None
        self.ftp_content_output = None
    
    def create_main_layout(self) -> QWidget:
        """Create the main layout for the window."""
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
        
        return main_widget
    
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
        
        # Connection Bar (Telnet)
        self.telnet_connection_bar = ConnectionBar(ip_address="", port=0)
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