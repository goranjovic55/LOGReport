import socket
from PyQt6.QtGui import QTextCursor
from .session_manager import SessionConfig, SessionType
from .widgets import ConnectionState

class TelnetHandlerMixin:
    """Telnet connection and command helpers."""

    def toggle_telnet_connection(self, connect: bool):
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
            self.connect_telnet(ip_address, port)
        else:
            self.disconnect_telnet()

    def connect_telnet(self, ip_address: str, port: int):
        config = SessionConfig(
            host=ip_address,
            port=port,
            session_type=SessionType.TELNET,
            username="",
            password="",
        )
        try:
            self.telnet_connection_bar.update_status(ConnectionState.CONNECTING)
            self.telnet_session = self.session_manager.create_session(config)
            if self.telnet_session and self.telnet_session.is_connected:
                self.telnet_output.clear()
                self.telnet_output.append(f"Connected to {ip_address}:{port}")
                self.telnet_connection_bar.update_status(ConnectionState.CONNECTED)
                self.cmd_input.setFocus()
                return True
            self.status_bar.showMessage("Connection failed")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
            return False
        except socket.timeout as e:
            self.status_bar.showMessage(f"Connection timed out: {e}")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
        except ConnectionRefusedError as e:
            self.status_bar.showMessage(f"Connection refused: {e}")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
        except Exception as e:
            self.status_bar.showMessage(f"Connection error: {e}")
            self.telnet_connection_bar.update_status(ConnectionState.ERROR)
            return False

    def disconnect_telnet(self):
        try:
            self.session_manager.close_all_sessions()
            self.telnet_session = None
            self.telnet_connection_bar.update_status(ConnectionState.DISCONNECTED)
            self.telnet_output.append("\n>>> DISCONNECTED")
        except Exception as e:
            self.telnet_output.append(f"Error: {e}")

    def execute_telnet_command(self):
        if not self.telnet_session:
            self.status_bar.showMessage("Create a Telnet session first!")
            return
        command = self.cmd_input.toPlainText().strip()
        if not command:
            return
        self.command_history.add(command)
        self.telnet_output.append(f"> {command}")
        self.telnet_output.moveCursor(QTextCursor.MoveOperation.End)
        try:
            token_id = self.current_token.token_id if self.current_token else ""
            resolved_cmd = self.command_resolver.resolve(command, token_id)
            response = self.telnet_session.send_command(resolved_cmd, timeout=5)
            self.telnet_output.append(response)
        except Exception as e:
            self.telnet_output.append(f"ERROR: {e}")
        self.cmd_input.clear()
        self.telnet_output.moveCursor(QTextCursor.MoveOperation.End)
