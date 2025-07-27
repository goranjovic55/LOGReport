"""
Main Window for Commander
MVP pattern implementation that ties together all components
"""
import sys
import os
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QVBoxLayout, QWidget, QHBoxLayout,
    QStatusBar, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtCore import pyqtSignal

# Import our components
from .ui.node_tree_view import NodeTreeView
from .ui.session_view import SessionView
from .presenters.commander_presenter import CommanderPresenter
from .presenters.node_tree_presenter import NodeTreePresenter
from .presenters.session_presenter import SessionPresenter
from .node_manager import NodeManager
from .session_manager import SessionManager
from .log_writer import LogWriter
from .services.context_menu_service import ContextMenuService
from .services.status_service import StatusService
from .services.error_handler import ErrorHandler
from .widgets import ConnectionBar, ConnectionState
from .qt_init import initialize_qt


class CommanderMainWindow(QMainWindow):
    """Main Commander window following MVP pattern."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Commander LogCreator v1.0")
        self.setMinimumSize(1200, 800)
        
        # Initialize core services
        self.node_manager = NodeManager()
        self.session_manager = SessionManager()
        self.log_writer = LogWriter(self.node_manager)
        
        # Initialize UI services
        self.context_menu_service = ContextMenuService()
        self.status_service = StatusService()
        self.error_handler = ErrorHandler()
        
        # Initialize views
        self.node_tree_view = NodeTreeView()
        self.session_view = SessionView()
        
        # Initialize presenters
        self.commander_presenter = CommanderPresenter(
            self.node_manager, 
            self.session_manager, 
            self.log_writer,
            self.context_menu_service,
            self.status_service,
            self.error_handler
        )
        
        self.node_tree_presenter = NodeTreePresenter(
            self.node_tree_view,
            self.node_manager,
            self.log_writer,
            self.context_menu_service,
            self.status_service,
            self.error_handler
        )
        
        self.session_presenter = SessionPresenter(
            self.session_view,
            self.session_manager,
            self.log_writer,
            self.status_service,
            self.error_handler
        )
        
        # Connect signals
        self._connect_signals()
        
        # Setup UI
        self._setup_ui()
        
        # Load settings
        self._load_settings()
        
    def _connect_signals(self):
        """Connect all signals between views and presenters"""
        # Node tree view signals
        self.node_tree_view.load_nodes_clicked.connect(self.commander_presenter.load_configuration)
        self.node_tree_view.set_log_root_clicked.connect(self.commander_presenter.set_log_root_folder)
        self.node_tree_view.node_selected.connect(self.node_tree_presenter.on_node_selected)
        self.node_tree_view.node_double_clicked.connect(self.node_tree_presenter.on_node_double_clicked)
        self.node_tree_view.context_menu_requested.connect(self.node_tree_presenter.show_context_menu)
        
        # Session view signals
        self.session_view.execute_clicked.connect(self.session_presenter.execute_command)
        self.session_view.copy_to_log_clicked.connect(self.session_presenter.copy_to_log)
        self.session_view.clear_terminal_clicked.connect(self.session_presenter.clear_terminal)
        self.session_view.clear_node_log_clicked.connect(self.session_presenter.clear_node_log)
        
        # Status service signals
        self.status_service.status_message.connect(self.statusBar().showMessage)
        
        # Error handler signals
        self.error_handler.error_reported.connect(self.statusBar().showMessage)
        
    def _setup_ui(self):
        """Initialize the main UI components"""
        # Create main layout
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        
        # Create splitter for dual-pane layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Add node tree view to left pane
        splitter.addWidget(self.node_tree_view)
        
        # Add session view to right pane
        splitter.addWidget(self.session_view)
        
        # Set splitter sizes (30/70 ratio)
        splitter.setSizes([300, 700])
        self.setCentralWidget(main_widget)
        
        # Status Bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Welcome to Commander LogCreator")
        
        # Apply dark theme styling
        self.setStyleSheet("""
            QMainWindow, QWidget, QDialog {
                background-color: #2D2D30;
                color: #DCDCDC;
                font-family: Segoe UI;
            }
            QSplitter::handle {
                background-color: #555;
            }
        """)
        
    def _load_settings(self):
        """Load application settings"""
        self.settings = QSettings("CommanderLogCreator", "Settings")
        
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
                    self.node_tree_presenter.populate_node_tree()
        except Exception as e:
            logging.error(f"Error loading default configuration: {e}")
            
        # Load saved telnet connection
        telnet_ip = self.settings.value("telnet_ip", "")
        telnet_port = self.settings.value("telnet_port", "")
        if telnet_ip and telnet_port:
            # Set values in presenter
            self.session_presenter.set_telnet_connection(telnet_ip, telnet_port)
            
    def closeEvent(self, event):
        """Cleanup on window close"""
        # Save application state
        self.settings.setValue("config_path", self.node_manager.config_path)
        self.settings.setValue("log_root", self.node_manager.log_root)
        
        # Save telnet connection state
        telnet_ip, telnet_port = self.session_presenter.get_telnet_connection()
        self.settings.setValue("telnet_ip", telnet_ip)
        self.settings.setValue("telnet_port", telnet_port)
        
        super().closeEvent(event)


def run():
    # Initialize Qt application safely
    app = initialize_qt() or QApplication(sys.argv)
    
    # Apply dark theme styling
    app.setStyle("Fusion")
    
    # Create main window instance
    window = CommanderMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()