"""
Commander Window - Main UI view for the Commander application
"""
from PyQt6.QtWidgets import QMainWindow, QStatusBar
from PyQt6.QtCore import QSettings, pyqtSignal

from ..services.context_menu_service import ContextMenuService
from ..services.context_menu_filter import ContextMenuFilterService
from ..services.fbc_command_service import FbcCommandService
from ..services.rpc_command_service import RpcCommandService
from ..services.commander_service import CommanderService
from ..services.telnet_service import TelnetService
from ..services.status_service import StatusService
from ..presenters.commander_presenter import CommanderPresenter
from ..presenters.node_tree_presenter import NodeTreePresenter

import sys
import os
import logging

# Import our components
from ..node_manager import NodeManager
from ..session_manager import SessionManager
from ..log_writer import LogWriter
from ..command_queue import CommandQueue

# Centralized Qt application initialization
from ..qt_init import initialize_qt


class CommanderWindow(QMainWindow):
    """Main Commander window view."""
    
    # Signal for status messages
    status_message_signal = pyqtSignal(str, int)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Commander LogCreator v1.0")
        self.setMinimumSize(1200, 800)
        
        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            encoding='utf-8'
        )
        
        # Load application settings
        self.settings = QSettings("CommanderLogCreator", "Settings")
        
        # Core components
        self.node_manager = NodeManager()
        self.session_manager = SessionManager()
        self.command_queue = CommandQueue(self.session_manager, parent=self)
        self.log_writer = LogWriter(self.node_manager)
        self.current_token = None
        
        # Initialize all components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all services and presenters"""
        # Initialize Status Service
        self.status_service = StatusService()
        self.status_service.status_updated.connect(self.statusBar().showMessage)
        
        # Initialize context menu filter service
        self.context_menu_filter = ContextMenuFilterService()
        
        # Initialize FBC and RPC services
        self.fbc_service = FbcCommandService(self.node_manager, self.command_queue, self.log_writer, self)
        self.rpc_service = RpcCommandService(self.node_manager, self.command_queue, self)
        
        # Initialize services through commander service
        self.commander_service = CommanderService(
            self.node_manager,
            self.session_manager,
            self.command_queue,
            self.log_writer,
            self.fbc_service,
            self.rpc_service
        )
        
        # Initialize Telnet Service
        self.telnet_service = TelnetService(self.session_manager)
        
        # Initialize context menu service
        self.context_menu_service = ContextMenuService(self.node_manager, self.context_menu_filter)
        
        # Initialize presenters
        self.commander_presenter = CommanderPresenter(
            self,
            self.node_manager,
            self.session_manager,
            self.log_writer,
            self.command_queue,
            self.fbc_service,
            self.rpc_service,
            self.context_menu_service
        )
        
        # Setup UI first
        self.init_ui()
        
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
        
        # Connect all signals
        self._connect_signals()
        
        # Load configurations
        self._load_configurations()
    
    def _connect_signals(self):
        """Connect all signals"""
        # Connect commander service signals to presenter
        self.commander_service.set_cmd_input_text.connect(self.set_cmd_input_text_signal)
        self.commander_service.switch_to_telnet_tab.connect(self.switch_to_telnet_tab_signal)
        self.commander_service.focus_command_input.connect(self.set_cmd_focus_signal)
        self.commander_service.status_message.connect(self.status_service.status_updated)
        self.commander_service.report_error.connect(lambda msg: self.status_service.show_error("Commander Service Error: " + msg))
        self.commander_service.command_finished.connect(self.on_telnet_command_finished)
        self.commander_service.queue_processed.connect(self.on_queue_processed)
        
        # Connect presenter signals
        self.commander_presenter.status_message_signal.connect(self.status_service.status_updated)
        self.commander_presenter.set_cmd_input_text_signal.connect(self.set_cmd_input_text_signal)
        self.commander_presenter.update_connection_status_signal.connect(self.update_connection_status_signal)
        self.commander_presenter.switch_to_telnet_tab_signal.connect(lambda: self.session_tabs.setCurrentWidget(self.telnet_tab))
        self.commander_presenter.set_cmd_focus_signal.connect(self.cmd_input.setFocus)
        
        # Connect node tree presenter signals
        self.node_tree_presenter.status_message_signal.connect(self.status_service.status_updated)
        self.node_tree_presenter.node_tree_updated_signal.connect(self.on_node_tree_updated)
        
        # Connect view signals to window methods
        self.command_finished.connect(self.on_telnet_command_finished)
        self.set_cmd_input_text_signal.connect(self.cmd_input.setPlainText)
        self.update_connection_status_signal.connect(self.telnet_connection_bar.update_status)
        self.switch_to_telnet_tab_signal.connect(lambda: self.session_tabs.setCurrentWidget(self.telnet_tab))
        self.set_cmd_focus_signal.connect(self.cmd_input.setFocus)
        self.status_message_signal.connect(self.status_service.status_updated)
        
        # Connect telnet service signals
        self.telnet_service.status_message_signal = self.status_service.status_updated
        self.telnet_service.command_finished_signal = self.command_finished
        self.telnet_service.update_connection_status_signal = self.update_connection_status_signal
        
        # Connect UI component signals
        self._connect_ui_signals()
    
    def _connect_ui_signals(self):
        """Connect UI component signals"""
        # Node tree view signals
        self.node_tree_view.load_nodes_clicked.connect(self.load_configuration)
        self.node_tree_view.set_log_root_clicked.connect(self.set_log_root_folder)
        self.node_tree_view.node_selected.connect(self.on_node_selected)
        self.node_tree_view.node_double_clicked.connect(self._on_node_double_clicked)
        self.node_tree_view.context_menu_requested.connect(self.show_context_menu)
        
        # Button signals
        self.execute_btn.clicked.connect(self.execute_telnet_command)
        self.telnet_connection_bar.connection_requested.connect(self.toggle_telnet_connection)
        self.copy_to_log_btn.clicked.connect(self.copy_to_log)
        self.clear_terminal_btn.clicked.connect(self.clear_terminal)
        self.clear_node_log_btn.clicked.connect(self.clear_node_log)
    
    def _load_configurations(self):
        """Load all configurations"""
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
    
    def init_ui(self):
        """Initialize the main UI components"""
        # Create main layout using presenter
        main_widget = self.commander_presenter.create_main_layout()
        self.setCentralWidget(main_widget)
        
        # Get references to UI components from presenter
        self.node_tree_view = self.commander_presenter.node_tree_view
        self.session_tabs = self.commander_presenter.session_tabs
        self.telnet_tab = self.commander_presenter.telnet_tab
        self.vnc_tab = self.commander_presenter.vnc_tab
        self.ftp_tab = self.commander_presenter.ftp_tab
        self.telnet_output = self.commander_presenter.telnet_output
        self.cmd_input = self.commander_presenter.cmd_input
        self.execute_btn = self.commander_presenter.execute_btn
        self.copy_to_log_btn = self.commander_presenter.copy_to_log_btn
        self.clear_terminal_btn = self.commander_presenter.clear_terminal_btn
        self.clear_node_log_btn = self.commander_presenter.clear_node_log_btn
        self.telnet_connection_bar = self.commander_presenter.telnet_connection_bar
        
        # Status Bar
        self.setStatusBar(QStatusBar())
        self.status_service.show_status("Welcome to Commander LogCreator")
    
    # Signal definitions (to be connected by presenter)
    set_cmd_input_text_signal = pyqtSignal(str)
    update_connection_status_signal = pyqtSignal(object)  # ConnectionState
    switch_to_telnet_tab_signal = pyqtSignal()
    set_cmd_focus_signal = pyqtSignal()
    command_finished = pyqtSignal(str, bool)
    queue_processed = pyqtSignal(int, int)  # Success count, total
    
    # Delegated methods to presenter
    def load_configuration(self):
        """Load node configuration from selected file"""
        self.commander_presenter.load_configuration()
    
    def set_log_root_folder(self):
        """Set the root folder for log files"""
        self.commander_presenter.set_log_root_folder()
    
    def show_context_menu(self, position):
        """Show context menu for the selected item in the node tree"""
        self.node_tree_presenter.show_context_menu(position)
    
    def populate_node_tree(self):
        """Lazy-loading tree population - only loads top-level nodes initially"""
        self.node_tree_presenter.populate_node_tree()
    
    def _on_node_double_clicked(self, item):
        """Wrapper method to handle node double-click events"""
        self.commander_presenter.open_log_file(item, 0)
    
    def on_node_selected(self, item):
        """Handles node/token selection in left pane"""
        self.commander_presenter.on_node_selected(item, self.current_token)
    
    def toggle_telnet_connection(self, connect: bool):
        """Toggles connection/disconnection for Telnet tab"""
        self.telnet_service.toggle_connection(connect, self.telnet_connection_bar.get_address()[0], 
                                              self.telnet_connection_bar.get_address()[1], self.settings)
    
    def execute_telnet_command(self, automatic=False):
        """Executes command in Telnet session using background thread"""
        self.telnet_service.set_current_token(self.current_token)
        return self.telnet_service.execute_command(self.cmd_input.toPlainText().strip(), automatic)
    
    def on_telnet_command_finished(self, response, automatic):
        """Handles the completion of a telnet command run in a background thread"""
        # For automatic commands, show command + response
        if automatic:
            self.telnet_output.append(f"{response}\n")
        else:
            self.telnet_output.append(response)
        from PyQt6.QtGui import QTextCursor
        self.telnet_output.moveCursor(QTextCursor.MoveOperation.End)
        
        # Delegate logging to commander service
        self.commander_service.log_telnet_command_finished(
            response, automatic, self.current_token, self.node_manager,
            self.status_service.status_updated, self.log_writer,
            self.cmd_input, self.execute_btn
        )
    
    def copy_to_log(self):
        """Copies current session content to selected token or log file"""
        self.commander_presenter.copy_to_log(self.node_tree_view.selectedItems(), self.session_tabs)
    
    def clear_terminal(self):
        """Clear the telnet output area"""
        self.commander_presenter.clear_terminal()
    
    def clear_node_log(self):
        """Clear the currently selected node's log file"""
        self.commander_presenter.clear_node_log(self.node_tree_view.selectedItems())
    
    def open_log_file(self, item, column: int):
        """Opens log file when double-clicked in tree view"""
        return self.commander_presenter.open_log_file(item, column)
    
    def process_fieldbus_command(self, token_id, node_name):
        """Process fieldbus command with optimized error handling"""
        self.commander_service.process_fieldbus_command(token_id, node_name)
    
    def process_rpc_command(self, node_name, token_id, action_type):
        """Process RPC commands with token validation and auto-execute"""
        self.commander_service.process_rpc_command(node_name, token_id, action_type)
    
    def on_node_tree_updated(self):
        """Handle node tree updates from presenter"""
        pass
    
    def on_queue_processed(self, success_count, total_count):
        """Handle queue processing completion"""
        self.commander_presenter.handle_queue_processed(success_count, total_count, self.status_service)
    
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