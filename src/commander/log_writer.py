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
from typing import Dict, TextIO, Tuple

class LogWriter:
    def __init__(self, node_manager=None):
        super().__init__()
        self.node_manager = node_manager
        self.loggers: Dict[Tuple[str, str], logging.Logger] = {}  # (token_id, protocol) -> logger
        self.log_paths: Dict[Tuple[str, str], str] = {}  # (token_id, protocol) -> path
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
        filename = f"{node_name}_{safe_token_id}_{normalized_ip}_{safe_token_id}.{log_type.lower()}"
        return os.path.join(log_dir, filename)

    def get_node_log_path(self, node, token_id, protocol) -> str:
        """Generates standardized log path with formatted IP for a node and token"""
        # Format IP address: 192.168.0.11 -> 192-168-0-11
        formatted_ip = node.ip_address.replace('.', '-')
        
        # Create path: <log_root>/<token_type>/<node_name>/<filename>
        filename = f"{node.name}_{formatted_ip}_{token_id}.{protocol.lower()}"
        return os.path.join(self.node_manager.log_root, protocol.upper(), node.name, filename)

    def get_log_path(self, node_name: str, node_ip: str, token: NodeToken) -> str:
        """Returns the full path to a token's log file, creating directories if needed"""
        return self._generate_filename(
            node_name or "unknown-node",
            (node_ip or "unknown-ip").replace('.', '-'),
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
        # Allow FBC to RPC token conversion scenarios
        if token and token.token_type != log_type and log_type in valid_types:
            # Allow FBC to RPC conversion but not other combinations
            if not (token.token_type == "FBC" and log_type == "RPC"):
                raise ValueError(f"Token type {token.token_type} conflicts with file type {log_type}")
            
        # Safely handle token data
        token_id = token.token_id or "unknown-token"
        node_name = node_name or "unknown-node"
        node_ip = node_ip or "unknown-ip"
        token_id_str = str(token.token_id).strip() if token.token_id else "unknown-token"
        
        # Use provided protocol or default to token's type
        protocol = log_type.lower()
        
        # Ensure node_name matches file's node name
        # Extract node_name from filename with special handling for LIS files
        filename = os.path.basename(log_path)
        filename_parts = filename.split('_')
        
        if log_type == 'LIS':
            # LIS files have format: {node_name}_{ip}_exe{number}_{suffix}.{extension}
            # Extract node_name as the first part
            file_node = filename_parts[0] if filename_parts else ""
        elif len(filename_parts) >= 4:
            # Standard format: {node_name}_{token_id}_{ip}_{token_id}.{extension}
            # Node name is everything except the last 3 parts (token_id, ip, token_id)
            file_node = '_'.join(filename_parts[:-3])
        else:
            # Fallback for unexpected filename format
            file_node = filename_parts[0] if filename_parts else ""
        if node_name != file_node:
            raise ValueError(f"Node name {node_name} doesn't match file's node {file_node}")
            
        # Validate IP address in filename matches token IP
        self._validate_ip_address(node_name, node_ip, token, log_path)
        
        # Check if directory exists before proceeding
        log_dir = os.path.dirname(log_path)
        if not os.path.exists(log_dir):
            # Directory doesn't exist, raise error instead of creating directories
            raise FileNotFoundError(f"Log directory does not exist: {log_dir}")
            
        # Use composite key (token_id, protocol) for log_paths
        key = (token_id_str, protocol)
        self.log_paths[key] = log_path
        
        if key not in self.loggers:
            # Create logger specific to this token and protocol
            logger = logging.getLogger(f"commander.{token_id_str}.{protocol}")
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
                    
            self.loggers[key] = logger
                
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
            # Use provided protocol or default to "fbc"
            protocol = protocol.lower() if protocol else "fbc"
            
            logging.info(f"Attempting to append to log for token {token_id} with protocol {protocol}")
            
            # Use composite key (token_id, protocol) to find logger
            key = (token_id, protocol)
            if key not in self.loggers:
                raise ValueError(f"No open log for token ID: {token_id} with protocol {protocol}")
                
            # Handle empty/null content
            safe_content = content.strip() if content else "<empty response>"
            log_path = self.log_paths.get(key, "unknown path")
            logging.debug(f"Sanitizing content for log: {log_path}")
            
            # Validate protocol parameter (just ensure it's a valid protocol, not that it matches file extension)
            if protocol:
                valid_protocols = {'telnet', 'vnc', 'fbc', 'rpc', 'log', 'lis'}
                if protocol.lower() not in valid_protocols:
                    raise ValueError(f"Invalid protocol: {protocol}")
            
            # Add source prefix if provided
            prefix = f"[{protocol.upper()}] " if protocol else ""
            formatted = prefix + safe_content
            
            # Add timestamp to each entry
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            try:
                # Use logger to write formatted message
                self.loggers[key].info(f"{timestamp} >> {formatted}")
                logging.info(f"Successfully appended to log for token {token_id} with protocol {protocol}")
                logging.debug(f"Wrote to log: {log_path}")
                
                # Log debugging information
                logging.debug(f"Using token type: {protocol}")
                logging.debug(f"Generated log path: {log_path}")
                
            except IOError as e:
                error_msg = f"Failed to write to log file {log_path}: {str(e)}"
                logging.error(error_msg, exc_info=True)
                raise IOError(error_msg)
                
        except Exception as e:
            error_msg = f"Error in append_to_log for token {token_id} with protocol {protocol}: {str(e)}"
            logging.error(error_msg, exc_info=True)
            raise type(e)(error_msg) from e
        
    def close_log(self, token_id: str, protocol: str = "fbc"):
        """Closes log file for a specific token ID and protocol"""
        # Use provided protocol or default to "fbc"
        protocol = protocol.lower() if protocol else "fbc"
        
        # Use composite key (token_id, protocol) to find logger
        key = (token_id, protocol)
        if key in self.loggers:
            logger = self.loggers[key]
            # Remove and close all handlers
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
            del self.loggers[key]
            del self.log_paths[key]
            
    def close_all_logs(self):
        """Closes all open log files"""
        for token_id, protocol in list(self.loggers.keys()):
            self.close_log(token_id, protocol)
