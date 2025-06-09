"""
Log Writer Service
Manages writing to node log files with LSR formatting
"""
import os
import time
from datetime import datetime
from typing import Dict, TextIO

class LogWriter:
    def __init__(self):
        self.log_handles: Dict[str, TextIO] = {}
        self.log_paths = {}
        
    def _create_log_directory(self, node_name: str) -> str:
        """Creates log directory for a node if it doesn't exist"""
        log_dir = os.path.join("test_logs", node_name)
        os.makedirs(log_dir, exist_ok=True)
        return log_dir
        
    def _generate_filename(self, node_name: str, token: str, log_type: str) -> str:
        """Generates log file path using convention: test_logs/node/token_type.log"""
        log_dir = self._create_log_directory(node_name)
        return os.path.join(log_dir, f"{token}_{log_type}.log")
        
    def open_log(self, node_name: str, token: str, log_type: str) -> str:
        """Opens a log file for writing. Creates LSR header if new file."""
        log_path = self._generate_filename(node_name, token, log_type)
        self.log_paths[token] = log_path
        
        if token not in self.log_handles:
            is_new_file = not os.path.exists(log_path)
            file_handle = open(log_path, 'a', encoding='utf-8')
            self.log_handles[token] = file_handle
            
            # Write header for new files
            if is_new_file:
                self._write_header(node_name, token, log_type, file_handle)
                
        return log_path
        
    def _write_header(self, node_name: str, token: str, log_type: str, file_handle: TextIO):
        """Writes LSR-compliant header to log file"""
        header = (
            f"=== COMMANDER LOG ===\n"
            f"Node: {node_name}\n"
            f"Token: {token}\n"
            f"Type: {log_type.upper()}\n"
            f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"====================\n\n"
        )
        file_handle.write(header)
        
    def append_to_log(self, token: str, content: str, source: str = ""):
        """Appends content to log with optional source annotation"""
        if token not in self.log_handles:
            raise ValueError(f"No open log for token: {token}")
            
        # Add source prefix if provided
        prefix = f"[{source.upper()}] " if source else ""
        formatted = prefix + content.strip()
        
        # Add timestamp to each entry
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_handles[token].write(f"{timestamp} >> {formatted}\n")
        self.log_handles[token].flush()
        
    def close_log(self, token: str):
        """Closes log file for a specific token"""
        if token in self.log_handles:
            self.log_handles[token].close()
            del self.log_handles[token]
            del self.log_paths[token]
            
    def close_all_logs(self):
        """Closes all open log files"""
        for token in list(self.log_handles.keys()):
            self.close_log(token)
            
    def get_log_path(self, token: str) -> str:
        """Returns the absolute path to a token's log file"""
        return os.path.abspath(self.log_paths[token])
