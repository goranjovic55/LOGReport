"""
Session Manager
Handles Telnet, VNC, and FTP session connections
"""
import telnetlib
import socket
import time
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class SessionType(Enum):
    TELNET = "TELNET"
    VNC = "VNC"
    FTP = "FTP"

@dataclass
class SessionConfig:
    host: str
    port: int
    session_type: SessionType
    username: str = ""
    password: str = ""
    timeout: int = 15

class BaseSession:
    """Abstract base class for session connections"""
    def __init__(self, config: SessionConfig):
        self.config = config
        self.connection = None
        self.is_connected = False
        
    def connect(self):
        raise NotImplementedError("Subclasses must implement connect()")
    
    def disconnect(self):
        if self.is_connected:
            self._disconnect_impl()
        self.connection = None
        self.is_connected = False
    
    def _disconnect_impl(self):
        """Implementation-specific disconnect logic"""
        raise NotImplementedError("Subclasses must implement _disconnect_impl()")
    
    def send_command(self, command: str) -> str:
        raise NotImplementedError("Subclasses must implement send_command()")
    
    def get_current_state(self) -> str:
        """Returns a string representation of connection state"""
        return f"{self.config.session_type.name} - {'Connected' if self.is_connected else 'Disconnected'}"

class TelnetSession(BaseSession):
    def __init__(self, config: SessionConfig):
        super().__init__(config)
        self.buffer = b""
        
    def connect(self) -> bool:
        try:
            # Establish connection with increased timeout
            self.connection = telnetlib.Telnet(
                self.config.host,
                self.config.port,
                self.config.timeout
            )
            
            # Wait for initial connection and read any banner
            time.sleep(1.0)  # Increased for Windows compatibility
            
            # Clear any initial response
            self.connection.read_very_eager()
            
            # Clear console artifacts by sending Ctrl+X and Ctrl+Z sequences
            self.connection.write(b'\x18')  # Ctrl+X
            time.sleep(0.1)
            self.connection.write(b'\x1A')  # Ctrl+Z
            time.sleep(0.1)
            # Read any response to clear the buffer
            self.connection.read_very_eager()
            
            self.is_connected = True
            return True
            
        except socket.timeout:
            print("Telnet connection timed out")
            return False
        except ConnectionRefusedError:
            print("Telnet connection refused")
            return False
        except Exception as e:
            print(f"Telnet connection failed: {str(e)}")
            return False
    
    def _disconnect_impl(self):
        if self.connection:
            self.connection.write(b"exit\n")
            self.connection.sock.settimeout(2)
            self.connection.read_all()
            self.connection.close()
    
    def send_command(self, command: str, timeout: float = 5.0) -> str:
        if not self.is_connected:
            raise ConnectionError("Not connected to Telnet session")
        
        # Clean console using Ctrl+X and Ctrl+Z to avoid artefacts before each command
        self.connection.write(b'\x18')  # Ctrl+X
        time.sleep(0.1)
        self.connection.write(b'\x1A')  # Ctrl+Z
        time.sleep(0.1)
        # Clear any response from the cleanup
        self.connection.read_very_eager()
        
        # Send command with CR LF termination
        self.connection.write(command.encode('ascii') + b"\r\n")
        time.sleep(0.1)  # Allow command processing
        
        # Read until we see the prompt again
        output = b""
        prompt_pattern = b'[$>#] '
        while True:
            try:
                chunk = self.connection.read_until(prompt_pattern, timeout=timeout)
                if not chunk:
                    break
                    
                output += chunk
                
                # If we got the prompt marker, we're done
                if output.splitlines()[-1].strip().endswith(prompt_pattern.strip()):
                    break
            except EOFError:
                break
            except socket.timeout:
                break
                
        # Remove the command echo and prompt
        decoded_output = output.decode('ascii', 'ignore')
        clean_output = decoded_output.replace(f"{command}\r\n", "").strip()
        return clean_output.rsplit('\n', 1)[0] if clean_output else ""

# Placeholders for other session types
class VNCSession(BaseSession):
    def connect(self):
        # Will be implemented in Phase 2
        self.is_connected = True
        return True
    
    def _disconnect_impl(self):
        pass
    
    def send_command(self, command: str) -> str:
        # In VNC we don't send commands directly
        return "VNC commands sent as keyboard sequences"

class FTPSession(BaseSession):
    def connect(self):
        # Will be implemented in Phase 2
        self.is_connected = True
        return True
    
    def _disconnect_impl(self):
        pass
    
    def send_command(self, command: str) -> str:
        # FTP commands are handled directly via protocol
        return "FTP commands not supported in this way"

class SessionManager:
    """Creates and manages active sessions"""
    session_types = {
        SessionType.TELNET: TelnetSession,
        SessionType.VNC: VNCSession,
        SessionType.FTP: FTPSession
    }
    
    def __init__(self):
        self.active_sessions = {}
        self.session_counter = 0
        
    def create_session(self, config: SessionConfig, auto_connect=True) -> Optional[BaseSession]:
        """Creates a new session, optionally connecting immediately"""
        session_class = self.session_types.get(config.session_type)
        if not session_class:
            raise ValueError(f"Unsupported session type: {config.session_type}")
        
        session = session_class(config)
        session_key = f"{config.session_type.name}_{self.session_counter}"
        self.session_counter += 1
        
        if auto_connect:
            if session.connect():
                self.active_sessions[session_key] = session
                return session
            return None
        
        # Not auto-connect - just store it
        self.active_sessions[session_key] = session
        return session
    
    def get_session(self, session_key: str) -> Optional[BaseSession]:
        """Retrieves an active session"""
        return self.active_sessions.get(session_key)
    
    def close_session(self, session_key: str):
        """Closes a specific session"""
        if session := self.active_sessions.get(session_key):
            session.disconnect()
            del self.active_sessions[session_key]
    
    def close_all_sessions(self):
        """Closes all active sessions"""
        for session in list(self.active_sessions.values()):
            session.disconnect()
        self.active_sessions = {}
        
    def get_all_sessions(self) -> dict:
        """Returns all active sessions"""
        return self.active_sessions.copy()
