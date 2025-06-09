"""
Simple Telnet Test Server
Simulates a network device for Commander testing
"""
import socket
import threading
import time

class TelnetTestServer:
    def __init__(self, host='0.0.0.0', port=2077):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.active = False
        self.command_responses = {
            b'\r\n': b'OK\r\n> ',
            b'help\r\n': b'[HELP] Commands: sysinfo, nodes, ports, exit\r\n> ',
            b'sysinfo\r\n': b'System Information: \r\n  Model: DNA-01\r\n  Version: v2.7.2\r\n> ',
            b'nodes\r\n': b'Nodes: \r\n  1. AP01m (192.168.1.101)\r\n  2. AL03 (192.168.1.103)\r\n> ',
            b'ports\r\n': b'Active Ports: \r\n  2077: Telnet\r\n  5901: VNC\r\n> ',
            b'p s\r\n': b'[Print System]\r\n  Online: AP01m, AL03\r\n> ',
            b'fis\r\n': (b'[Fieldbus Structure]\r\n'
                         b'Token 162: FBC\r\n'
                         b'  Type: Fieldbus Controller\r\n'
                         b'  Status: Active\r\n> '),
            b'rc\r\n': b'[RUPI Counters]\r\n  Packets: 1289\r\n  Errors: 0\r\n> '
        }
        
    def start(self):
        """Starts the telnet server"""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.active = True
        print(f"[TEST] Telnet server listening on {self.host}:{self.port}")
        
        # Start client handling in a new thread
        self.server_thread = threading.Thread(target=self.run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
    def stop(self):
        """Stops the telnet server"""
        self.active = False
        # Connect to self to unblock accept
        try:
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(
                (self.host, self.port))
            self.server_socket.close()
        except:
            pass
        print("[TEST] Telnet server stopped")

    def run_server(self):
        """Server thread handler"""
        while self.active:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"[TEST] Connection from: {addr[0]}:{addr[1]}")
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()
            except OSError:
                break

    def handle_client(self, client_socket):
        """Handles client Telnet session"""
        # Send welcome message
        client_socket.send(b"Telnet Test Server - DNA System Simulator\r\n")
        client_socket.send(b"login: ")
        client_socket.recv(1024)  # Dump login input
        client_socket.send(b"password: ")
        client_socket.recv(1024)  # Dump password input
        client_socket.send(b"Logged in successfully\r\n> ")

        # Process commands
        while self.active:
            try:
                command = client_socket.recv(1024)
                if not command:
                    break
                    
                # Log raw command for debugging
                print(f"[TEST] Raw command: {command}")
                
                # Normalize line endings and strip whitespace
                normalized_cmd = command.strip().replace(b'\r', b'').replace(b'\n', b'')
                
                # Log normalized command
                print(f"[TEST] Normalized command: '{normalized_cmd.decode()}'")
                
                # Match commands without worrying about line endings
                if normalized_cmd == b'help':
                    client_socket.send(self.command_responses[b'help\r\n'])
                    
                elif normalized_cmd == b'sysinfo':
                    client_socket.send(self.command_responses[b'sysinfo\r\n'])
                    
                elif normalized_cmd == b'nodes':
                    client_socket.send(self.command_responses[b'nodes\r\n'])
                    
                elif normalized_cmd == b'ports':
                    client_socket.send(self.command_responses[b'ports\r\n'])
                    
                elif normalized_cmd == b'p s':
                    client_socket.send(self.command_responses[b'p s\r\n'])
                    
                elif normalized_cmd == b'fis':
                    client_socket.send(self.command_responses[b'fis\r\n'])
                    
                elif normalized_cmd == b'rc':
                    client_socket.send(self.command_responses[b'rc\r\n'])
                    
                elif normalized_cmd == b'exit':
                    client_socket.send(b"Logging out...\r\n")
                    break
                    
                else:
                    client_socket.send(b"Unknown command. Type 'help' for options.\r\n> ")
                    
            except (ConnectionResetError, BrokenPipeError):
                break
                
        client_socket.close()
        print(f"[TEST] Connection closed")

if __name__ == "__main__":
    server = TelnetTestServer()
    server.start()
    
    try:
        # Keep server running until keyboard interrupt
        while server.active:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
        print("\nServer terminated by user")
