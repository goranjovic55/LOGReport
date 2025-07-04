import telnetlib
import time
import re
import socket

class TelnetClient:
    def __init__(self):
        self.connection = None
        self.timeout = 10
        self.prompt_pattern = re.compile(r'\d+[a-z]\%\s*$')
        self.mode = "INSERT"  # Default mode
        self.log = []
        
    def connect(self, host: str, port: int) -> tuple[bool, str]:
        """Establish telnet connection with timeout handling"""
        try:
            self.connection = telnetlib.Telnet()
            self.connection.open(host, port, self.timeout)
            if not self.connection.get_socket():
                return (False, "Connection failed - no socket")
            # Wait for initial connection and read any banner
            time.sleep(1.0)  # Increased for Windows compatibility
            initial_data = self.connection.read_very_eager()

            # Clear console artifacts by sending Ctrl+X and Ctrl+Z sequences
            self.connection.write(b'\x18')  # Ctrl+X
            time.sleep(0.1)
            self.connection.write(b'\x1A')  # Ctrl+Z
            time.sleep(0.1)
            # Read any response to clear the buffer
            self.connection.read_very_eager()
            
            return (True, "Connected successfully")
        except socket.timeout as e:
            if self.connection:
                self.connection.close()
            return False, f"Connection timed out: {str(e)}"
        except ConnectionRefusedError:
            return False, "Connection refused"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
            
    def disconnect(self):
        """Close telnet connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            
    def send_command(self, command: str) -> str:
        """Send command and return filtered response with error handling"""
        if not self.connection:
            raise ConnectionError("Not connected to telnet server")

        try:
            # Clear input buffer and console artifacts
            self.connection.read_very_eager()
            self.connection.write(b'\x18')  # Ctrl+X
            time.sleep(0.1)
            self.connection.write(b'\x1A')  # Ctrl+Z
            time.sleep(0.1)
            self.connection.read_very_eager()

            # Send command with proper termination
            self.connection.write(command.encode('ascii') + b"\r\n")
            
            # Get and process response
            response = self._read_response()
            return self._process_response(response)
            
        except socket.timeout as e:
            return f"Error: Command timed out - {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"
        
    def _read_response(self):
        """Read telnet response with prompt detection"""
        response = b""
        start_time = time.time()
        timeout_seconds = self.timeout
        
        while (time.time() - start_time) < timeout_seconds:
            chunk = self.connection.read_very_eager()
            if chunk:
                response += chunk
                decoded = response.decode('ascii', 'ignore')
                if self.prompt_pattern.search(decoded):
                    break
            # Use non-blocking wait instead of sleep
            self.connection.get_socket().settimeout(0.05)
            try:
                # This will return immediately if no data
                if self.connection.get_socket().recv(1) == b'':
                    break
            except socket.timeout:
                continue
                
        print(f"[TelnetClient] Raw response:\n{response.decode('ascii', 'ignore')}")  # Debug raw response
        return response.decode('ascii', 'ignore') if response else ""

    def _process_response(self, response):
        # Detect mode changes
        if "Editor changed to INSERT mode" in response:
            self.mode = "INSERT"
        elif "Editor changed to REPLACE mode" in response:
            self.mode = "REPLACE"
            
        # Remove mode information
        clean = response.replace("Editor changed to INSERT mode", "") \
                        .replace("Editor changed to REPLACE mode", "")
        
        # Filter control characters
        filtered = self._filter_output(clean)
        print(f"[TelnetClient] Filtered response:\n{filtered}")  # Debug filtered output
        return filtered
        
    def _filter_output(self, text):
        """Specialized filtering for automation debugger output"""
        if not text:
            return ""
            
        # Remove ANSI codes
        filtered = re.sub(r'\x1b\[[0-9;]*[mK]', '', text)
        # Remove control characters but preserve newlines
        filtered = re.sub(r'[\x00-\x09\x0B-\x1F\x7F]', '', filtered)
        # Preserve tildes and terminal mode artifacts as they're part of the output
        # Remove only specific known artifacts while preserving content
        filtered = re.sub(r'texitoggleure', '', filtered)  # Specific artifact
        # Normalize whitespace but preserve newlines
        filtered = re.sub(r'[ \t]+', ' ', filtered)  # Replace multiple spaces/tabs with single space
        filtered = re.sub(r'\n\s+', '\n', filtered)  # Remove leading whitespace after newlines
        return filtered.strip()
        return filtered if filtered else ""
