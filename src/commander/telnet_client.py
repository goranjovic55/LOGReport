import telnetlib
import time
import re
import socket
import logging

class TelnetClient:
    def __init__(self):
        self.connection = None
        self.timeout = 10
        self.prompt_pattern = re.compile(r'\d+[a-z]\%\s*$')
        self.mode = "INSERT"  # Default mode
        self.log = []
        
    def connect(self, host: str, port: int) -> tuple[bool, str]:
        """Establish telnet connection with timeout handling"""
        logging.debug(f"TelnetClient.connect: Connecting to {host}:{port}")
        try:
            self.connection = telnetlib.Telnet()
            self.connection.open(host, port, self.timeout)
            
            # Detailed socket state logging
            sock = self.connection.get_socket()
            if not sock:
                error_msg = "Connection failed - no socket"
                logging.error(f"TelnetClient.connect: {error_msg}")
                return (False, error_msg)
                
            logging.debug(f"TelnetClient.connect: Socket created: {sock}")
            logging.debug(f"TelnetClient.connect: Socket timeout: {sock.gettimeout()}")
            
            # Wait for initial connection and read any banner
            time.sleep(1.0)  # Increased for Windows compatibility
            
            # Combined read operation
            initial_response = self.connection.read_very_eager()
            logging.debug(f"TelnetClient.connect: Initial response (hex): {initial_response.hex()}")
            logging.debug(f"TelnetClient.connect: Initial response (text): {initial_response.decode('ascii', 'ignore')}")
            
            # Skip artifact clearing for now to isolate connection issue
            logging.debug("TelnetClient.connect: Skipping artifact clearing for debug")
            
            logging.info(f"TelnetClient.connect: Connected successfully to {host}:{port}")
            return (True, "Connected successfully")
        except socket.timeout as e:
            error_msg = f"Connection timed out: {str(e)}"
            logging.error(f"TelnetClient.connect: {error_msg}", exc_info=True)
            if self.connection:
                self.connection.close()
            return False, error_msg
        except ConnectionRefusedError as e:
            error_msg = f"Connection refused: {str(e)}"
            logging.error(f"TelnetClient.connect: {error_msg}", exc_info=True)
            return False, error_msg
        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            logging.error(f"TelnetClient.connect: {error_msg}", exc_info=True)
            return False, error_msg
            
    def disconnect(self):
        """Close telnet connection"""
        logging.debug("TelnetClient.disconnect: Disconnecting")
        if self.connection:
            self.connection.close()
            self.connection = None
            logging.info("TelnetClient.disconnect: Disconnected successfully")
            
    def send_command(self, command: str) -> str:
        """Send command and return filtered response with error handling"""
        if not self.connection:
            error_msg = "TelnetClient.send_command: Not connected to telnet server"
            logging.error(error_msg)
            raise ConnectionError(error_msg)

        logging.debug(f"TelnetClient.send_command: Sending command: {command}")
        try:
            # Clear input buffer and console artifacts
            logging.debug("TelnetClient.send_command: Clearing input buffer")
            self.connection.read_very_eager()
            self.connection.write(b'\x18')  # Ctrl+X
            time.sleep(0.1)
            self.connection.write(b'\x1A')  # Ctrl+Z
            time.sleep(0.1)
            cleared = self.connection.read_very_eager()
            logging.debug(f"TelnetClient.send_command: Cleared {len(cleared)} bytes from buffer")

            # Send command with proper termination
            cmd_bytes = command.encode('ascii') + b"\r\n"
            logging.debug(f"TelnetClient.send_command: Sending {len(cmd_bytes)} bytes: {cmd_bytes}")
            bytes_sent = self.connection.write(cmd_bytes)
            logging.debug(f"TelnetClient.send_command: Sent {bytes_sent} bytes")
            
            if bytes_sent != len(cmd_bytes):
                error_msg = f"TelnetClient.send_command: Only sent {bytes_sent}/{len(cmd_bytes)} bytes"
                logging.error(error_msg)
                raise ConnectionError(error_msg)
            
            # Get and process response
            response = self._read_response()
            logging.debug(f"TelnetClient.send_command: Received {len(response)} chars of raw response")
            
            processed = self._process_response(response)
            logging.debug(f"TelnetClient.send_command: Processed response length: {len(processed)}")
            return processed
            
        except socket.timeout as e:
            error = f"TelnetClient.send_command: Command timed out - {str(e)}"
            logging.error(error)
            raise ConnectionError(error) from e
        except ConnectionAbortedError as e:
            error = f"TelnetClient.send_command: Connection aborted by peer (WinError 10053) - {str(e)}"
            logging.error(error, exc_info=True)
            raise ConnectionError(error) from e
        except Exception as e:
            error = f"TelnetClient.send_command: Error - {str(e)}"
            logging.error(error, exc_info=True)
            raise ConnectionError(error) from e
        
    def _read_response(self):
        """Read telnet response with prompt detection"""
        logging.debug(f"TelnetClient._read_response: Reading response with prompt pattern: {self.prompt_pattern.pattern}")
        response = b""
        start_time = time.time()
        timeout_seconds = self.timeout
        last_data_time = time.time()
        
        while (time.time() - start_time) < timeout_seconds:
            chunk = self.connection.read_very_eager()
            if chunk:
                response += chunk
                last_data_time = time.time()
                decoded = response.decode('ascii', 'ignore')
                logging.debug(f"TelnetClient._read_response: Received {len(chunk)} bytes, total {len(response)}")
                
                if self.prompt_pattern.search(decoded):
                    logging.debug("TelnetClient._read_response: Detected prompt pattern")
                    break
                    
            # Use non-blocking wait instead of sleep
            self.connection.get_socket().settimeout(0.05)
            try:
                test_byte = self.connection.get_socket().recv(1)
                if test_byte == b'':
                    logging.debug("TelnetClient._read_response: Socket closed by remote")
                    break
            except socket.timeout:
                # Check if we've had no data for too long
                if (time.time() - last_data_time) > (timeout_seconds / 2):
                    logging.warning("TelnetClient._read_response: No data received for half of timeout period")
                    break
                continue
            except EOFError as e:
                logging.error(f"TelnetClient._read_response: EOFError - {str(e)}")
                break
            except Exception as e:
                logging.error(f"TelnetClient._read_response: Error reading socket - {str(e)}")
                break
                
        result = response.decode('ascii', 'ignore') if response else ""
        logging.debug(f"TelnetClient._read_response: Returning {len(result)} chars")
        return result

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
