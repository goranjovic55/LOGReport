"""
Session View Component
Stateless UI component for displaying session tabs
"""
from PyQt6.QtWidgets import QTabWidget, QTextEdit, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from ..widgets import ConnectionBar


class SessionView(QWidget):
    """View component for the session tabs UI"""
    
    # Signals for user interactions
    execute_clicked = pyqtSignal()
    copy_to_log_clicked = pyqtSignal()
    clear_terminal_clicked = pyqtSignal()
    clear_node_log_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        
    def _setup_ui(self):
        """Initialize the session tabs UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Session Tabs
        self.session_tabs = QTabWidget()
        
        # Create session tabs
        self.telnet_tab = self._create_telnet_tab()
        self.vnc_tab = self._create_session_tab("VNC")
        self.ftp_tab = self._create_session_tab("FTP")
        
        self.session_tabs.addTab(self.telnet_tab, "Telnet")
        self.session_tabs.addTab(self.vnc_tab, "VNC")
        self.session_tabs.addTab(self.ftp_tab, "FTP")
        
        layout.addWidget(self.session_tabs)
        
        # Command Buttons
        button_layout = QHBoxLayout()
        self.copy_to_log_btn = QPushButton("Copy to Node Log")
        self.clear_terminal_btn = QPushButton("Clear Terminal")
        self.clear_node_log_btn = QPushButton("Clear Node Log")
        
        button_layout.addWidget(self.copy_to_log_btn)
        button_layout.addWidget(self.clear_terminal_btn)
        button_layout.addWidget(self.clear_node_log_btn)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.copy_to_log_btn.clicked.connect(self.copy_to_log_clicked.emit)
        self.clear_terminal_btn.clicked.connect(self.clear_terminal_clicked.emit)
        self.clear_node_log_btn.clicked.connect(self.clear_node_log_clicked.emit)
        
    def _create_telnet_tab(self) -> QWidget:
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
        
        self.execute_btn = QPushButton("Execute")
        cmd_layout.addWidget(QLabel("Command:"))
        cmd_layout.addWidget(self.cmd_input, 3)
        cmd_layout.addWidget(self.execute_btn, 1)
        
        layout.addWidget(cmd_widget, 1)
        
        # Add execute button handler
        self.execute_btn.clicked.connect(self.execute_clicked.emit)
        
        # Connection Bar (Telnet)
        self.telnet_connection_bar = ConnectionBar(ip_address="", port=0)
        layout.addWidget(self.telnet_connection_bar)
        
        return tab
        
    def _create_session_tab(self, tab_type: str) -> QWidget:
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
        
    def set_current_widget(self, widget):
        """Set the current tab widget"""
        self.session_tabs.setCurrentWidget(widget)
        
    def get_current_index(self):
        """Get the current tab index"""
        return self.session_tabs.currentIndex()
        
    def get_tab_text(self, index):
        """Get the text of a tab"""
        return self.session_tabs.tabText(index)
        
    def get_widget(self, index):
        """Get the widget at an index"""
        return self.session_tabs.widget(index)