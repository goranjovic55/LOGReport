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
        
    def connect(self, host, port):
        """Establish connection to telnet server using provided host and port without fallback"""
        try:
            self.connection = telnetlib.Telnet(host, port, self.timeout)
            # Clear initial response
            time.sleep(0.5)
            self.connection.read_very_eager()
            return True
        except Exception as e:
            return False  # Return False instead of raising exception
            
    def disconnect(self):
        """Close telnet connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            
    def send_command(self, command):
        """Send command and return filtered response"""
        if not self.connection:
            raise ConnectionError("Not connected to telnet server")
            
        # Clear input buffer before sending command
        self.connection.read_very_eager()
        
        # Send command with CR LF termination
        self.connection.write(command.encode('ascii') + b"\r\n")
        
        # Get response using prompt detection
        response = self._read_response()
        return self._process_response(response)
        
    def _read_response(self):
        """Read telnet response with prompt detection"""
        response = b""
        start_time = time.time()
        
        while (time.time() - start_time) < self.timeout:
            chunk = self.connection.read_very_eager()
            if chunk:
                response += chunk
                decoded = response.decode('ascii', 'ignore')
                if self.prompt_pattern.search(decoded):
                    break
            else:
                time.sleep(0.05)
                
        return response.decode('ascii', 'ignore') if response else ""

    def _process_response(self, response):
        """Process response and extract clean output"""
        # Detect mode changes
        if "Editor changed to INSERT mode" in response:
            self.mode = "INSERT"
        elif "Editor changed to REPLACE mode" in response:
            self.mode = "REPLACE"
            
        # Remove mode information
        clean = response.replace("Editor changed to INSERT mode", "") \
                        .replace("Editor changed to REPLACE mode", "")
        
        # Filter control characters
        return self._filter_output(clean)
        
    def _filter_output(self, text):
        """Specialized filtering for automation debugger output"""
        # Remove ANSI codes
        filtered = re.sub(r'\x1b\[[0-9;]*[mK]', '', text)
        # Remove control characters
        filtered = re.sub(r'[\x00-\x1F\x7F]', '', text)
        # Remove artifacts from terminal modes
        filtered = re.sub(r'\w+\d+~\d+~texitoggleure', '', text)
        # Remove stray tildes and newlines
        filtered = re.sub(r'~+', ' ', text)
        # Collapse spaces
        filtered = re.sub(r'\s{2,}', ' ', text).strip()
        return filtered
