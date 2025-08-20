#!/usr/bin/env python3
"""
Simple test script to validate FBC token detection for AP01m node
"""
import sys
import os
import json
from typing import Dict, List, Optional

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Simple implementation of Node and NodeToken classes for testing
class NodeToken:
    def __init__(self, name: str, token_id: str, token_type: str, ip_address: str, port: int = 23, protocol: str = "telnet"):
        self.name = name
        self.token_id = token_id
        self.token_type = token_type.upper()
        self.ip_address = ip_address
        self.port = port
        self.protocol = protocol
        self.log_path = ""

    def __repr__(self):
        return f"NodeToken(name='{self.name}', token_id='{self.token_id}', token_type='{self.token_type}', ip_address='{self.ip_address}', port={self.port}, log_path='{self.log_path}')"

class Node:
    def __init__(self, name: str, ip_address: str):
        self.name = name
        self.ip_address = ip_address
        self.tokens: Dict[str, NodeToken] = {}
        self.status = "offline"

    def add_token(self, token: NodeToken):
        self.tokens[token.token_id] = token

    def __repr__(self):
        return f"Node(name='{self.name}', ip_address='{self.ip_address}', tokens={list(self.tokens.keys())})"

# Simple implementation of NodeManager for testing
class NodeManager:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.log_root = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "test_logs"
        )
        print(f"[DEBUG] Log root set to: {self.log_root}")
        self.selected_node: Optional[Node] = None

    def scan_log_files(self, log_root=None):
        """
        Scans filesystem for log files recursively under log root
        Handles all file locations and structures
        """
        import re
        root = log_root or self.log_root
        print(f"[DEBUG] Scanning log root: {root}")
        if not os.path.exists(root):
            print(f"[DEBUG] ERROR: Log root does not exist")
            return
            
        # First, scan for IPs in log directory names and update token objects
        self._scan_for_dynamic_ips(root)
            
        print(f"[DEBUG] Log root exists")
        
        # Check directory structure
        token_types = ["FBC", "RPC", "LOG", "LIS"]
        for token_type in token_types:
            token_dir = os.path.join(root, token_type)
            if os.path.exists(token_dir):
                print(f"[DEBUG] Found token directory: {token_type}")
                node_dirs = os.listdir(token_dir)
                print(f"[DEBUG] Found {len(node_dirs)} node directories in {token_type}: {node_dirs}")
            else:
                print(f"[DEBUG] WARNING: Token directory not found: {token_type}")
        
        print(f"[DEBUG] Starting recursive scan of: {root}")
        
        # Walk through all directories and files
        for dirpath, _, filenames in os.walk(root):
            # Skip directories without .log files
            log_files = [f for f in filenames if f.lower().endswith(('.log', '.fbc', '.rpc', '.lis'))]
            if not log_files:
                continue
                
            print(f"[DEBUG] Found {len(log_files)} log files in {dirpath}")
            
            for filename in log_files:
                full_path = os.path.join(dirpath, filename)
                print(f"[DEBUG] Processing file: {full_path}")
                
                # Extract base name without extension for token matching
                base_name = os.path.splitext(filename)[0]
                
                # Extract token type and node name based on file pattern
                token_type_dir = None
                node_name = None
                
                # Handle LOG files by filename pattern
                if filename.lower().endswith('.log'):
                    # Extract token type from filename for .log files
                    parts = base_name.split('_')
                    if len(parts) >= 2 and parts[-1].upper() in token_types:
                        # Pattern: XXX_FBC.log, XXX_RPC.log, etc.
                        token_type_dir = parts[-1].upper()
                        # For node-specific files in node directories, use directory name as node_name
                        dir_basename = os.path.basename(dirpath)
                        if dir_basename in [n.name for n in self.nodes.values()]:
                            node_name = dir_basename
                        else:
                            # Fallback to first part of filename as node name
                            node_name = parts[0] if parts else "UNKNOWN"
                    else:
                        # Default to LOG type for files that don't match the pattern
                        token_type_dir = "LOG"
                        # For node-specific files in node directories, use directory name as node_name
                        dir_basename = os.path.basename(dirpath)
                        if dir_basename in [n.name for n in self.nodes.values()]:
                            node_name = dir_basename
                        else:
                            # Fallback to first part of filename as node name
                            node_name = parts[0] if parts else "UNKNOWN"
                    print(f"[DEBUG] LOG file detected: node_name={node_name}, token_type={token_type_dir}")
                # Handle other file types by directory structure
                else:
                    # Token type is the parent directory name
                    token_type_dir = os.path.basename(dirpath)
                    
                    # Handle nested directories (e.g., FBC/AP01m/)
                    parent_dir = os.path.basename(os.path.dirname(dirpath))
                    if parent_dir in token_types:
                        token_type_dir = parent_dir
                        node_name = os.path.basename(dirpath)
                        print(f"[DEBUG] {token_type_dir} file in node directory: node_name={node_name}")
                    else:
                        # For files directly in token type directories
                        node_name = os.path.basename(dirpath)
                        print(f"[DEBUG] {token_type_dir} file: node_name={node_name}")
                
                # Find matching node (case-insensitive)
                matched_node = next(
                    (n for n in self.nodes.values() if n.name.lower() == node_name.lower()),
                    None
                )
                
                if not matched_node:
                    print(f"[DEBUG] WARNING: No node found for: {node_name}")
                    print(f"[DEBUG] Available nodes: {[n.name for n in self.nodes.values()]}")
                    continue
                    
                # Find matching token using multiple strategies
                token = None
                matching_strategy = "none"
                
                # Extract token ID from filename (last alphanumeric part)
                parts = base_name.split('_')
                token_id_candidate = parts[-2] if len(parts) >= 2 and parts[-1].upper() in token_types else (parts[-1] if parts else None)
                
                # Normalize token ID candidate:
                # - Pad numeric IDs to 3 digits
                # - Convert alphanumeric to uppercase for FBC tokens only
                if token_id_candidate:
                    if token_type_dir == "FBC":
                        if token_id_candidate.isdigit():
                            token_id_candidate = token_id_candidate.zfill(3)
                        else:
                            token_id_candidate = token_id_candidate.upper()
                    else:
                        # For non-FBC tokens, just strip whitespace
                        token_id_candidate = token_id_candidate.strip()
                
                # Strategy 1: Case-insensitive exact token ID match
                if token_id_candidate:
                    token = next(
                        (t for t in matched_node.tokens.values()
                         if t.token_id.lower() == token_id_candidate.lower()),
                        None
                    )
                    if token:
                        matching_strategy = "extracted token ID match"
                
                # Strategy 2: Case-insensitive token ID substring match
                if not token:
                    for t in matched_node.tokens.values():
                        if token_id_candidate and token_id_candidate.lower() in t.token_id.lower():
                            token = t
                            matching_strategy = "token ID in filename"
                            break
                
                # Strategy 3: Match by token type and closest alphanumeric match
                if not token:
                    same_type_tokens = [t for t in matched_node.tokens.values()
                                        if t.token_type == token_type_dir]
                    if same_type_tokens and token_id_candidate:
                        # DEBUG: Log alphanumeric matching attempt
                        print(f"[DEBUG] Starting Strategy 3 for alphanumeric token: {token_id_candidate}")
                        print(f"[DEBUG] Available {token_type_dir} tokens: {[t.token_id for t in same_type_tokens]}")
                        
                        # Try to find closest alphanumeric match
                        token = min(
                            same_type_tokens,
                            key=lambda t: self._token_distance(t.token_id.lower(), token_id_candidate.lower())
                        )
                        
                        # DEBUG: Log match result
                        distance = self._token_distance(token.token_id.lower(), token_id_candidate.lower())
                        print(f"[DEBUG] Closest match: {token.token_id} (distance: {distance})")
                        matching_strategy = "closest alphanumeric token match"
                
                # For FBC files, create token representation and add to node
                if token_type_dir == "FBC" and not token:
                    # Preserve original token ID case for FBC files
                    token = NodeToken(
                        name=f"{node_name} {token_type_dir}",
                        token_id=token_id_candidate or "UNKNOWN",
                        token_type=token_type_dir,
                        ip_address=matched_node.ip_address
                    )
                    normalized_path = os.path.normpath(full_path)
                    token.log_path = normalized_path
                    matched_node.add_token(token)
                    print(f"[DEBUG] ADDED FBC token to node: {token.token_id} | Path: {normalized_path}")
                
                # For other token types, maintain existing behavior
                elif token_type_dir == "LOG" or (not token and token_type_dir in token_types):
                    token = NodeToken(
                        name=f"{node_name} {token_type_dir}",
                        token_id=token_id_candidate or "UNKNOWN",
                        token_type=token_type_dir,
                        ip_address=matched_node.ip_address
                    )
                    normalized_path = os.path.normpath(full_path)
                    token.log_path = normalized_path
                    print(f"[DEBUG] Mapped {token_type_dir} file | Node: {node_name} | Path: {normalized_path}")
                elif token:
                    normalized_path = os.path.normpath(full_path)
                    token.log_path = normalized_path
                    
                    # Ensure token is added to node if not already present
                    if token.token_id not in matched_node.tokens:
                        matched_node.add_token(token)
                        print(f"[DEBUG] ADDED token to node: {token.token_id} ({token.token_type})")
                    
                    print(f"[DEBUG] SUCCESS: Mapped log file | Node: {node_name} | Token: {token.token_id} | Strategy: {matching_strategy} | Path: {normalized_path}")
                else:
                    print(f"[DEBUG] WARNING: Could not find matching token for: {filename} in node: {node_name}")
                    print(f"[DEBUG] Available tokens: {[t.token_id for t in matched_node.tokens.values()]}")
                    print(f"[DEBUG] Token ID candidate: {token_id_candidate}")

    def _token_distance(self, token1: str, token2: str) -> int:
        """Calculates similarity distance between two token IDs"""
        # Normalize tokens to lowercase for case-insensitive comparison
        token1 = token1.lower()
        token2 = token2.lower()
        
        if token1 == token2:
            return 0
        if token1.startswith(token2) or token2.startswith(token1):
            return 1
        return 2

    def _scan_for_dynamic_ips(self, log_root: str):
        """
        Scans log directory for IPs using regex pattern and updates token objects
        Pattern: r"(\d{1,3}-\d{1,3}-\d{1,3}-\d{1,3})"
        """
        import re
        ip_pattern = r"(\d{1,3}-\d{1,3}-\d{1,3}-\d{1,3})"
        print(f"[DEBUG] Scanning for dynamic IPs in: {log_root}")
        
        # Walk through all directories and files
        for dirpath, _, filenames in os.walk(log_root):
            # Process directory names for IP patterns
            dir_name = os.path.basename(dirpath)
            ip_matches = re.findall(ip_pattern, dir_name)
            if ip_matches:
                # Convert IP format from 192-168-0-11 to 192.168.0.11
                for ip_match in ip_matches:
                    formatted_ip = ip_match.replace('-', '.')
                    print(f"[DEBUG] Found IP in directory name: {ip_match} -> {formatted_ip}")
                    # Update tokens with this IP if they don't already have a valid IP
                    self._update_tokens_with_ip(formatted_ip)
            
            # Process filenames for IP patterns
            for filename in filenames:
                ip_matches = re.findall(ip_pattern, filename)
                if ip_matches:
                    # Convert IP format from 192-168-0-11 to 192.168.0.11
                    for ip_match in ip_matches:
                        formatted_ip = ip_match.replace('-', '.')
                        print(f"[DEBUG] Found IP in filename: {ip_match} -> {formatted_ip}")
                        # Update tokens with this IP if they don't already have a valid IP
                        self._update_tokens_with_ip(formatted_ip)

    def _update_tokens_with_ip(self, ip_address: str):
        """
        Updates token objects with discovered IP addresses
        Only updates tokens that don't already have a valid IP address
        """
        print(f"[DEBUG] Updating tokens with IP: {ip_address}")
        for node in self.nodes.values():
            for token in node.tokens.values():
                # Only update tokens without a valid IP address
                if not token.ip_address or token.ip_address == "0.0.0.0":
                    print(f"[DEBUG] Updating token {token.token_id} with IP {ip_address}")
                    token.ip_address = ip_address

def test_ap01m_fbc_detection():
    """Test FBC token detection for AP01m node"""
    print("Testing FBC token detection for AP01m node...")
    
    # Initialize NodeManager
    manager = NodeManager()
    
    # Create AP01m node with expected tokens
    node = Node(name="AP01m", ip_address="192.168.1.101")
    
    # Add the three FBC tokens that should be detected
    token_162 = NodeToken(
        name="AP01m 162",
        token_id="162",
        token_type="FBC",
        ip_address="192.168.1.101",
        port=2077
    )
    node.add_token(token_162)
    
    token_163 = NodeToken(
        name="AP01m 163",
        token_id="163",
        token_type="FBC",
        ip_address="192.168.1.101",
        port=2077
    )
    node.add_token(token_163)
    
    token_164 = NodeToken(
        name="AP01m 164",
        token_id="164",
        token_type="FBC",
        ip_address="192.168.1.101",
        port=2077
    )
    node.add_token(token_164)
    
    manager.nodes = {"AP01m": node}
    
    # Scan log files
    manager.scan_log_files()
    
    # Check how many FBC tokens were found
    fbc_tokens = [t for t in node.tokens.values() if t.token_type == "FBC"]
    print(f"Found {len(fbc_tokens)} FBC tokens for node AP01m")
    print(f"Tokens: {[t.token_id for t in fbc_tokens]}")
    
    # Check if all three tokens have log paths
    tokens_with_logs = [t for t in fbc_tokens if t.log_path]
    print(f"Tokens with log paths: {len(tokens_with_logs)}")
    for t in tokens_with_logs:
        print(f"  Token {t.token_id}: {t.log_path}")
    
    # Verify that all three tokens have their log paths updated
    expected_files = [
        os.path.join("test_logs", "AP01m", "162_FBC.log"),
        os.path.join("test_logs", "AP01m", "163_FBC.log"),
        os.path.join("test_logs", "AP01m", "164_FBC.log")
    ]
    
    for token in [token_162, token_163, token_164]:
        if token.log_path:
            print(f"✓ Token {token.token_id} has log path: {token.log_path}")
        else:
            print(f"✗ Token {token.token_id} does not have a log path")
    
    print("\nTest completed!")

if __name__ == "__main__":
    try:
        test_ap01m_fbc_detection()
        sys.exit(0)
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)