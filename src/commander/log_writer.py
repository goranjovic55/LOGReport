from .models import NodeToken
"""
Log Writer Service
Manages writing to node log files with LSR formatting
"""
import os
import logging
from logging.handlers import RotatingFileHandler
import time
from datetime import datetime
from typing import Dict, TextIO

class LogWriter:
    def __init__(self, node_manager=None):
        super().__init__()
        self.node_manager = node_manager
        self.loggers: Dict[str, logging.Logger] = {}
        self.log_paths = {}
        self.thread_pool = None  # Will be set by CommanderWindow
        
    def set_thread_pool(self, thread_pool):
        """Set the thread pool for asynchronous operations"""
        self.thread_pool = thread_pool
        
    def _create_log_directory(self, node_name: str) -> str:
        """Creates log directory for a node if it doesn't exist"""
        log_dir = os.path.join("test_logs", node_name)
        os.makedirs(log_dir, exist_ok=True)
        return log_dir
        
    def _generate_filename(self, node_name: str, node_ip: str, token_id: str, log_type: str) -> str:
        """Generates log file path using convention: test_logs/FBC/node_name/node_ip_token.fbc"""
        # Validate log type
        if log_type not in {'FBC', 'RPC', 'LOG', 'LIS'}:
            log_type = 'LOG'
            
        log_dir = os.path.join(self.node_manager.log_root, log_type, node_name)
        os.makedirs(log_dir, exist_ok=True)
        # Normalize IP address format to hyphens
        normalized_ip = node_ip.replace('.', '-')
        # Handle missing token_id with fallback
        safe_token_id = "unknown-token" if not token_id else str(token_id).strip()
        filename = f"{node_name}_{normalized_ip}_{safe_token_id}.{log_type.lower()}"
        return os.path.join(log_dir, filename)

    def get_log_path(self, node_name: str, node_ip: str, token: NodeToken) -> str:
        """Returns the full path to a token's log file, creating directories if needed"""
        return self._generate_filename(
            node_name,
            node_ip.replace('.', '-'),
            token.token_id,
            token.token_type
        )
        
    def open_log(self, node_name: str, node_ip: str, token: NodeToken, log_path: str) -> str:
        """Opens a log file for writing. Creates LSR header if new file."""
        # Get log type from actual file extension
        log_type = os.path.splitext(log_path)[1][1:].upper()  # Extract extension without dot
        log_type = log_type if log_type in {'FBC','RPC','LOG','LIS'} else 'UNKNOWN'
        
        print(f"[DEBUG] Opening log - Token type: {token.token_type}, File type: {log_type}, Path: {log_path}")  # Debug
        
        # Validate all supported log types
        valid_types = {'FBC', 'RPC', 'LOG', 'LIS', 'UNKNOWN'}  # Include UNKNOWN type for validation
        if token and token.token_type != log_type and log_type in valid_types:
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
            
        # Validate IP address in filename matches token IP
        self._validate_ip_address(node_name, node_ip, token, log_path)
        
        self.log_paths[token_id_str] = log_path
        
        if token_id_str not in self.loggers:
            # Create logger specific to this token
            logger = logging.getLogger(f"commander.{token_id_str}")
            logger.setLevel(logging.INFO)
            
            # Create rotating file handler (10MB max, keep 5 backups)
            handler = RotatingFileHandler(
                log_path,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8',
                delay=True  # Delay opening until first write to check file existence
            )
            
            # Create formatter that just passes through messages (we format them ourselves)
            handler.setFormatter(logging.Formatter('%(message)s'))
            logger.addHandler(handler)
            
            # Check if file is new (handler creates it on first write)
            # Ensure file is created by forcing first write
            if not os.path.exists(log_path) or os.path.getsize(log_path) == 0:
                # Create file and write header
                with open(log_path, 'w', encoding='utf-8') as f:
                    self._write_header(node_name, token_id_str, log_type, f)
                    
            self.loggers[token_id_str] = logger
                
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
        
    def _validate_ip_address(self, node_name: str, node_ip: str, token: NodeToken, log_path: str):
        """
        Validates that token IP matches filename IP and provides warning/correction
        """
        # Extract IP from filename (format: node_ip_token.type)
        filename_parts = os.path.basename(log_path).split('_')
        if len(filename_parts) >= 2:
            filename_ip_formatted = filename_parts[1]  # IP part in filename
            filename_ip = filename_ip_formatted.replace('-', '.')  # Convert to standard format
            
            # Check if token IP differs from filename IP
            token_ip = token.ip_address if token.ip_address else "unknown-ip"
            if token_ip != filename_ip and token_ip != "unknown-ip" and filename_ip != "unknown-ip":
                print(f"[WARNING] Token IP {token_ip} != Filename IP {filename_ip} for token {token.token_id}")
                # For now, we'll just log the warning. In a real implementation, we might want
                # to prompt for user confirmation before correcting the IP
                # token.ip_address = filename_ip  # Automatic correction (commented out for safety)
        
    def append_to_log(self, token_id: str, content: str, protocol: str):
        """Appends content to log with protocol annotation"""
        try:
            logging.info(f"Attempting to append to log for token {token_id}")
            if token_id not in self.loggers:
                raise ValueError(f"No open log for token ID: {token_id}")
                
            # Handle empty/null content
            safe_content = content.strip() if content else "<empty response>"
            log_path = self.log_paths[token_id]
            logging.debug(f"Sanitizing content for log: {log_path}")
            
            # Add source prefix if provided
            prefix = f"[{protocol.upper()}] " if protocol else ""
            formatted = prefix + safe_content
            
            # Add timestamp to each entry
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            try:
                # Use logger to write formatted message
                self.loggers[token_id].info(f"{timestamp} >> {formatted}")
                logging.info(f"Successfully appended to log for token {token_id}")
                logging.debug(f"Wrote to log: {log_path}")
                
            except IOError as e:
                error_msg = f"Failed to write to log file {log_path}: {str(e)}"
                logging.error(error_msg, exc_info=True)
                raise IOError(error_msg)
                
        except Exception as e:
            error_msg = f"Error in append_to_log for token {token_id}: {str(e)}"
            logging.error(error_msg, exc_info=True)
            raise type(e)(error_msg) from e
        
    def close_log(self, token_id: str):
        """Closes log file for a specific token ID"""
        if token_id in self.loggers:
            logger = self.loggers[token_id]
            # Remove and close all handlers
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
            del self.loggers[token_id]
            del self.log_paths[token_id]
            
    def close_all_logs(self):
        """Closes all open log files"""
        for token in list(self.loggers.keys()):
            self.close_log(token)
