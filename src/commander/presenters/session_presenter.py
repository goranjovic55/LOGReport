"""
Session Presenter - Handles presentation logic for session management
"""
import logging
from PyQt6.QtCore import QObject, pyqtSignal

from ..session_manager import SessionManager, SessionConfig, SessionType
from ..widgets import ConnectionState


class SessionPresenter(QObject):
    """Presenter for session management, handling presentation logic for sessions"""
    
    # Signals for UI updates
    update_connection_status_signal = pyqtSignal(ConnectionState)
    status_message_signal = pyqtSignal(str, int)  # message, duration
    set_cmd_focus_signal = pyqtSignal()
    
    # Status message durations in milliseconds
    STATUS_MSG_SHORT = 3000    # 3 seconds
    STATUS_MSG_MEDIUM = 5000   # 5 seconds
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialize the SessionPresenter.
        
        Args:
            session_manager: Manager for session operations
        """
        super().__init__()
        self.session_manager = session_manager
        self.active_telnet_client = None
        self.telnet_session = None
        
        logging.debug("SessionPresenter initialized")
    
    def toggle_telnet_connection(self, connect: bool, ip_address: str, port_text: str):
        """Toggles connection/disconnection for Telnet tab"""
        if not ip_address or not port_text:
            self.status_message_signal.emit("IP and port are required.", self.STATUS_MSG_SHORT)
            self.update_connection_status_signal.emit(ConnectionState.ERROR)
            return
            
        try:
            port = int(port_text)
        except ValueError:
            self.status_message_signal.emit(f"Invalid port number: {port_text}", self.STATUS_MSG_SHORT)
            self.update_connection_status_signal.emit(ConnectionState.ERROR)
            return
            
        if connect:
            self.connect_telnet(ip_address, port)
        else:
            self.disconnect_telnet()
    
    def connect_telnet(self, ip_address: str, port: int):
        """Connects to specified telnet server using provided IP and port"""
        # Configure telnet connection using the parameters
        config = SessionConfig(
            host=ip_address,
            port=port,
            session_type=SessionType.DEBUGGER,  # Use DEBUGGER session type for manual connections
            username="",   # No username by default
            password=""    # No password by default
        )
        
        try:
            self.update_connection_status_signal.emit(ConnectionState.CONNECTING)
            self.telnet_session = self.session_manager.create_session(config)
            
            # Attempt connection and get detailed result
            if self.telnet_session and self.telnet_session.is_connected:
                self.update_connection_status_signal.emit(ConnectionState.CONNECTED)
                self.set_cmd_focus_signal.emit()
                # Store active client for reuse in context commands
                self.active_telnet_client = self.telnet_session
                return True
            
            # Handle connection failure
            self.status_message_signal.emit("Connection failed", self.STATUS_MSG_SHORT)
            self.update_connection_status_signal.emit(ConnectionState.ERROR)
            return False
            
        except Exception as e:
            self.status_message_signal.emit(f"Connection error: {str(e)}", self.STATUS_MSG_MEDIUM)
            self.update_connection_status_signal.emit(ConnectionState.ERROR)
            return False
    
    def disconnect_telnet(self):
        """Disconnects from current telnet session"""
        try:
            # Only close through session manager to avoid double disconnect
            self.session_manager.close_all_sessions()
            # Clear local reference AFTER session manager has closed sessions
            self.telnet_session = None
            # Clear active client reference
            self.active_telnet_client = None
            # Force UI update to disconnected state
            self.update_connection_status_signal.emit(ConnectionState.DISCONNECTED)
        except Exception as e:
            # Still reset UI state even if disconnection failed
            self.update_connection_status_signal.emit(ConnectionState.DISCONNECTED)
    
    def set_telnet_session(self, session):
        """Set the telnet session"""
        self.telnet_session = session
    
    def get_telnet_session(self):
        """Get the telnet session"""
        return self.telnet_session
    
    def set_active_telnet_client(self, client):
        """Set the active telnet client"""
        self.active_telnet_client = client
    
    def get_active_telnet_client(self):
        """Get the active telnet client"""
        return self.active_telnet_client