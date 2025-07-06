from .models import NodeToken
"""
Log Writer Service
Manages writing to node log files with LSR formatting
"""
import os
import time
from datetime import datetime
from typing import Dict, TextIO

class LogWriter:
    def __init__(self, node_manager=None):
        self.node_manager = node_manager
        self.log_handles: Dict[str, TextIO] = {}
        self.log_paths = {}
        
    def _create_log_directory(self, node_name: str) -> str:
        """Creates log directory for a node if it doesn't exist"""
        log_dir = os.path.join("test_logs", node_name)
        os.makedirs(log_dir, exist_ok=True)
        return log_dir
        
    def _generate_filename(self, node_name: str, node_ip: str, token_id: str, log_type: str) -> str:
        """Generates log file path using convention: test_logs/FBC/node_name/node_ip_token.fbc"""
        log_dir = os.path.join(self.node_manager.log_root, log_type, node_name)
        os.makedirs(log_dir, exist_ok=True)
        # Normalize IP address format to hyphens
        normalized_ip = node_ip.replace('.', '-')
        # Handle missing token_id with fallback
        safe_token_id = "unknown-token" if not token_id else str(token_id).strip()
        filename = f"{node_name}_{normalized_ip}_{safe_token_id}.{log_type.lower()}"
        return os.path.join(log_dir, filename)
        
    def open_log(self, node_name: str, node_ip: str, token: NodeToken, log_path: str) -> str:
        """Opens a log file for writing. Creates LSR header if new file."""
        # Get log type from actual file extension
        log_type = os.path.splitext(log_path)[1][1:].upper()  # Extract extension without dot
        log_type = log_type if log_type in {'FBC','RPC','LOG','LIS'} else 'UNKNOWN'
        
        print(f"[DEBUG] Opening log - Token type: {token.token_type}, File type: {log_type}, Path: {log_path}")  # Debug
        
        # Validate token matches file type
        if token and token.token_type != log_type:
            raise ValueError(f"Token type {token.token_type} conflicts with file type {log_type}")
            
        # Safely handle token data
        token_id = token.token_id or "unknown-token"
        node_name = node_name or "unknown-node"
        node_ip = node_ip or "unknown-ip"
        token_id_str = str(token.token_id).strip() if token.token_id else "unknown-token"
        
        # Ensure node_name matches file's node name
        file_node = os.path.basename(log_path).split('_')[0]
        if node_name != file_node:
            raise ValueError(f"Node name {node_name} doesn't match file's node {file_node}")
        self.log_paths[token_id_str] = log_path
        
        if token_id_str not in self.log_handles:
            is_new_file = not os.path.exists(log_path)
            file_handle = open(log_path, 'a', encoding='utf-8')
            self.log_handles[token_id_str] = file_handle
            
            # Write header for new files
            if is_new_file:
                self._write_header(node_name_str, token_id_str, log_type, file_handle)
                
        return log_path
        
    def _write_header(self, node_name: str, token_id: str, log_type: str, file_handle: TextIO):
        """Writes LSR-compliant header to log file"""
        header = (
            f"=== COMMANDER LOG ===\n"
            f"Node: {node_name}\n"
            f"Token: {token_id}\n"
            f"Type: {log_type.upper()}\n"
            f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"====================\n\n"
        )
        file_handle.write(header)
        
    def append_to_log(self, token_id: str, content: str, protocol: str):
        """Appends content to log with protocol annotation"""
        print(f"[LogWriter] Received append request - Token: {token_id}, Protocol: {protocol}, Content length: {len(content)}")  # Debug input
        if token_id not in self.log_handles:
            raise ValueError(f"No open log for token ID: {token_id}")
            
        # Handle empty/null content
        safe_content = content.strip() if content else "<empty response>"
        
        # Add source prefix if provided
        prefix = f"[{protocol.upper()}] " if protocol else ""
        formatted = prefix + safe_content
        
        # Add timestamp to each entry
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_handles[token_id].write(f"{timestamp} >> {formatted}\n")
        self.log_handles[token_id].flush()
        print(f"[LogWriter] Wrote {len(formatted)} chars to {self.log_paths[token_id]}")  # Debug write confirmation
        
    def close_log(self, token_id: str):
        """Closes log file for a specific token ID"""
        if token_id in self.log_handles:
            self.log_handles[token_id].close()
            del self.log_handles[token_id]
            del self.log_paths[token_id]
            
    def close_all_logs(self):
        """Closes all open log files"""
        for token in list(self.log_handles.keys()):
            self.close_log(token)
            
    def get_log_path(self, token_id: str) -> str:
        """Returns the absolute path to a token's log file"""
        return os.path.abspath(self.log_paths[token_id])
