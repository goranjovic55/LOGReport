"""
Telnet Service - Handles Telnet connection management and command execution
"""
import logging
import socket
import time
from typing import Optional

from ..session_manager import SessionManager, SessionConfig, SessionType
from ..models import NodeToken
from ..widgets import ConnectionState
from ..commands.telnet_commands import CommandResolver
from ..services.threading_service import ThreadingService


class TelnetService:
    """Service for handling Telnet operations"""
    
    # Status message durations in milliseconds
    STATUS_MSG_SHORT = 3000    # 3 seconds
    STATUS_MSG_MEDIUM = 5000   # 5 seconds
    STATUS_MSG_LONG = 10000    # 10 seconds
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialize the Telnet service.
        
        Args:
            session_manager: Manager for session operations
        """
        self.session_manager = session_manager
        self.command_resolver = CommandResolver()
        self.threading_service = ThreadingService()
        self.telnet_lock = self.threading_service.create_lock()
        self.active_telnet_client = None
        self.telnet_session = None
        self.current_token = None
        
        # Signals for UI updates (to be connected by the UI)
        self.status_message_signal = None
        self.command_finished_signal = None
        self.update_connection_status_signal = None
        
        logging.debug("TelnetService initialized")
    
    def set_current_token(self, token: NodeToken):
        """
        Set the current token for command execution.
        
        Args:
            token: The token to set as current
        """
        self.current_token = token
        logging.debug(f"TelnetService: Current token set to {token.token_id if token else None}")
    
    def toggle_connection(self, connect: bool, ip_address: str, port: int, settings=None) -> bool:
        """
        Toggles connection/disconnection for Telnet.
        
        Args:
            connect: True to connect, False to disconnect
            ip_address: IP address to connect to
            port: Port to connect to
            settings: Optional settings object to save connection parameters
            
        Returns:
            bool: True if operation succeeded, False otherwise
        """
        if connect:
            # Save connection parameters to settings if provided
            if settings:
                settings.setValue("telnet_ip", ip_address)
                settings.setValue("telnet_port", str(port))
            return self.connect(ip_address, port)
        else:
            return self.disconnect()
    
    def connect(self, ip_address: str, port: int) -> bool:
        """
        Connects to specified telnet server using provided IP and port.
        
        Args:
            ip_address: IP address to connect to
            port: Port to connect to
            
        Returns:
            bool: True if connection succeeded, False otherwise
        """
        # Configure telnet connection using the parameters
        config = SessionConfig(
            host=ip_address,
            port=port,
            session_type=SessionType.DEBUGGER,  # Use DEBUGGER session type for manual connections
            username="",   # No username by default
            password=""    # No password by default
        )
        
        try:
            if self.update_connection_status_signal:
                self.update_connection_status_signal.emit(ConnectionState.CONNECTING)
                
            self.telnet_session = self.session_manager.create_session(config)
            
            # Attempt connection and get detailed result
            if self.telnet_session and self.telnet_session.is_connected:
                if self.status_message_signal:
                    self.status_message_signal.emit(f"Connected to {ip_address}:{port}", self.STATUS_MSG_SHORT)
                    
                if self.update_connection_status_signal:
                    self.update_connection_status_signal.emit(ConnectionState.CONNECTED)
                    
                # Store active client for reuse in context commands
                self.active_telnet_client = self.telnet_session
                return True
            
            # Handle connection failure
            if self.status_message_signal:
                self.status_message_signal.emit("Connection failed", self.STATUS_MSG_MEDIUM)
                
            if self.update_connection_status_signal:
                self.update_connection_status_signal.emit(ConnectionState.ERROR)
            return False
            
        except socket.timeout as e:
            if self.status_message_signal:
                self.status_message_signal.emit(f"Connection timed out: {str(e)}", self.STATUS_MSG_MEDIUM)
                
            if self.update_connection_status_signal:
                self.update_connection_status_signal.emit(ConnectionState.ERROR)
            return False
        except ConnectionRefusedError as e:
            if self.status_message_signal:
                self.status_message_signal.emit(f"Connection refused: {str(e)}", self.STATUS_MSG_MEDIUM)
                
            if self.update_connection_status_signal:
                self.update_connection_status_signal.emit(ConnectionState.ERROR)
            return False
        except Exception as e:
            if self.status_message_signal:
                self.status_message_signal.emit(f"Connection error: {str(e)}", self.STATUS_MSG_MEDIUM)
                
            if self.update_connection_status_signal:
                self.update_connection_status_signal.emit(ConnectionState.ERROR)
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnects from current telnet session.
        
        Returns:
            bool: True if disconnection succeeded, False otherwise
        """
        try:
            # Only close through session manager to avoid double disconnect
            self.session_manager.close_all_sessions()
            # Clear local reference AFTER session manager has closed sessions
            self.telnet_session = None
            # Clear active client reference
            self.active_telnet_client = None
            
            # Force UI update to disconnected state
            if self.update_connection_status_signal:
                self.update_connection_status_signal.emit(ConnectionState.DISCONNECTED)
                
            return True
            
        except Exception as e:
            logging.error(f"Error disconnecting: {str(e)}")
            # Still reset UI state even if disconnection failed
            if self.update_connection_status_signal:
                self.update_connection_status_signal.emit(ConnectionState.DISCONNECTED)
            return False
    
    def execute_command(self, command: str, automatic=False) -> str:
        """
        Executes command in Telnet session using background thread.
        
        Args:
            command: Command to execute
            automatic: Whether command was triggered automatically
            
        Returns:
            str: Empty string (response will be handled asynchronously)
        """
        # Prioritize active manual connection if available
        if hasattr(self, 'active_telnet_client') and self.active_telnet_client and self.active_telnet_client.is_connected:
            self.telnet_session = self.active_telnet_client
            
        if not self.telnet_session:
            if not automatic and self.status_message_signal:
                self.status_message_signal.emit("Create a Telnet session first!", self.STATUS_MSG_MEDIUM)
            logging.debug("Telnet session not available for command execution")
            return ""
        
        command = command.strip()
        if not command:
            logging.debug("Empty command received in execute_command")
            return ""
        logging.debug(f"Executing telnet command: {command} (automatic={automatic})")
            
        logging.debug(f"Executing telnet command: {command}")
        logging.debug(f"DEBUG: Automatic={automatic}, Current token: {self.current_token.token_id if self.current_token else 'None'}")

        if not automatic:
            # Display user command in output
            if self.command_finished_signal:
                self.command_finished_signal.emit(f"> {command}\n", automatic)
            
        # Start command execution in background thread
        self.threading_service.start_thread(
            target=self._run_command,
            args=(command, automatic),
            daemon=True
        )
        
        return ""  # Response will be handled asynchronously

    def _run_command(self, command, automatic):
        """
        Runs telnet command in background thread with improved error handling.
        
        Args:
            command: Command to execute
            automatic: Whether command was triggered automatically
        """
        with self.telnet_lock:
            try:
                token_id = self.current_token.token_id if self.current_token else ""
                resolved_cmd = self.command_resolver.resolve(command, token_id)
                response = self.telnet_session.send_command(resolved_cmd, timeout=5)
                
                if self.update_connection_status_signal:
                    self.update_connection_status_signal.emit(ConnectionState.CONNECTED)
                    
            except (ConnectionRefusedError, TimeoutError, socket.timeout) as e:
                response = f"ERROR: {type(e).__name__} - {str(e)}"
                self._handle_connection_error(e)
            except Exception as e:
                response = f"ERROR: {type(e).__name__} - {str(e)}"
                logging.error(f"Telnet command failed: {command}", exc_info=True)
            
            logging.debug(f"Emitting command_finished signal for command: {command}")
            if self.command_finished_signal:
                self.command_finished_signal.emit(response, automatic)
    
    def _handle_connection_error(self, error):
        """
        Centralized connection error handling.
        
        Args:
            error: The error that occurred
        """
        error_type = type(error).__name__
        if error_type in ["ConnectionRefusedError", "TimeoutError", "socket.timeout"]:
            if self.update_connection_status_signal:
                self.update_connection_status_signal.emit(ConnectionState.ERROR)
                
            if self.status_message_signal:
                self.status_message_signal.emit(f"Connection error: {str(error)}", self.STATUS_MSG_MEDIUM)