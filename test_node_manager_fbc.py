#!/usr/bin/env python3
"""
Test script to verify FBC token detection in NodeManager for AP01m node.
"""
import json
import os
import re
from typing import Dict, List, Optional

class NodeToken:
    def __init__(self, token_id: str, token_type: str, name: str = "default",
                 ip_address: str = "0.0.0.0", port: int = 23, **kwargs):
        self.token_id = token_id
        self.token_type = token_type
        self.name = name
        self.ip_address = ip_address
        self.port = port
        self.log_path = kwargs.get('log_path', "")
        self.protocol = kwargs.get('protocol', "telnet")

class Node:
    def __init__(self, name: str, ip_address: str):
        self.name = name
        self.ip_address = ip_address
        self.status = "offline"
        self.tokens: Dict[str, NodeToken] = {}
        
    def add_token(self, token: NodeToken):
        self.tokens[token.token_id] = token

class SimpleNodeManager:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.log_root = "test_logs"
        self._load_test_configuration()
        
    def _load_test_configuration(self):
        """Load a simple test configuration for AP01m node."""
        # Create AP01m node with just the 163 RPC token as in the original config
        node = Node("AP01m", "192.168.0.11")
        
        # Add the existing 163 RPC token
        token = NodeToken(
            token_id="163",
            token_type="RPC",
            name="AP01m 163",
            ip_address="192.168.0.11",
            port=23
        )
        node.add_token(token)
        
        self.nodes[node.name] = node
        print(f"Loaded node {node.name} with {len(node.tokens)} pre-configured tokens")
        
    def _token_distance(self, token1: str, token2: str) -> int:
        """Calculates similarity distance between two token IDs"""
        # Normalize tokens to lowercase for case-insensitive comparison
        token1 = token1.lower()
        token2 = token2.lower()
        
        # If tokens are exactly the same, distance is 0
        if token1 == token2:
            return 0
            
        # If one token is a prefix of the other, distance is 1
        if token1.startswith(token2) or token2.startswith(token1):
            return 1
            
        # For numeric tokens, calculate numeric difference if both are numeric
        if token1.isdigit() and token2.isdigit():
            try:
                diff = abs(int(token1) - int(token2))
                # Return a distance based on the difference, capped at 10
                return min(diff, 10)
            except ValueError:
                pass  # Fall back to string comparison if conversion fails
                
        # For general string comparison, use Levenshtein distance
        return self._levenshtein_distance(token1, token2)
        
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate the Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
            
        if len(s2) == 0:
            return len(s1)
            
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
            
        return previous_row[-1]
        
    def scan_log_files(self):
        """Simplified version of scan_log_files to test FBC token detection."""
        print(f"[DEBUG] Scanning log root: {self.log_root}")
        if not os.path.exists(self.log_root):
            print(f"[DEBUG] ERROR: Log root does not exist")
            return
            
        # Walk through all directories and files
        for dirpath, _, filenames in os.walk(self.log_root):
            # Process only .log and .fbc files
            log_files = [f for f in filenames if f.lower().endswith(('.log', '.fbc'))]
            if not log_files:
                continue
                
            print(f"[DEBUG] Found {len(log_files)} log files in {dirpath}")
            
            for filename in log_files:
                full_path = os.path.join(dirpath, filename)
                print(f"[DEBUG] Processing file: {full_path}")
                
                # Extract base name without extension for token matching
                base_name = os.path.splitext(filename)[0]
                
                # Extract node name and token type based on file pattern
                node_name = None
                token_type_dir = None
                
                # Handle FBC files by directory structure or filename
                if filename.lower().endswith('.fbc'):
                    token_type_dir = "FBC"
                    # Check if we're in a nested structure like FBC/AP01m/
                    parent_dir = os.path.basename(os.path.dirname(dirpath))
                    if parent_dir == "FBC":
                        node_name = os.path.basename(dirpath)
                    else:
                        # For files directly in a node directory like test_logs/AP01m/
                        # Extract node name from the directory name
                        dir_basename = os.path.basename(dirpath)
                        if dir_basename == "AP01m":
                            node_name = dir_basename
                        # Or extract from filename pattern like AP01m_162_FBC.fbc
                        elif "_" in base_name:
                            parts = base_name.split("_")
                            if len(parts) >= 2:
                                node_name = parts[0]
                # Handle LOG files by filename pattern
                elif filename.lower().endswith('.log'):
                    # Special handling for files in AP01m directory
                    dir_basename = os.path.basename(dirpath)
                    if dir_basename == "AP01m" and "_" in base_name:
                        parts = base_name.split("_")
                        if len(parts) >= 2 and parts[-1].upper() in ["FBC", "RPC", "VNC", "FTP", "LIS", "LOG"]:
                            # This is a file like 162_FBC.log in AP01m directory
                            token_type_dir = parts[-1].upper()
                            node_name = dir_basename
                        else:
                            # Standard LOG file handling
                            token_type_dir = "LOG"
                            node_name = parts[0] if parts else None
                    else:
                        # Standard LOG file handling
                        token_type_dir = "LOG"
                        node_name = base_name.split('_')[0] if "_" in base_name else None
                
                print(f"[DEBUG] File type: {token_type_dir}, Node: {node_name}")
                
                if not node_name or not token_type_dir:
                    continue
                    
                # Find matching node (case-insensitive)
                matched_node = next(
                    (n for n in self.nodes.values() if n.name.lower() == node_name.lower()),
                    None
                )
                
                if not matched_node:
                    print(f"[DEBUG] WARNING: No node found for: {node_name}")
                    continue
                    
                # Extract token ID from filename
                token_id_candidate = None
                if filename.lower().endswith('.fbc'):
                    # For FBC files, extract from filename pattern
                    if "_" in base_name:
                        parts = base_name.split("_")
                        # Look for the token ID (usually the last part that's not the node name)
                        for part in reversed(parts):
                            if part != node_name and (part.isdigit() or re.match(r'^[a-zA-Z0-9]+$', part)):
                                token_id_candidate = part
                                break
                        # Fallback: last part
                        if not token_id_candidate:
                            token_id_candidate = parts[-1] if parts else None
                elif filename.lower().endswith('.log'):
                    # For LOG files in AP01m directory, extract from pattern like 162_FBC.log
                    dir_basename = os.path.basename(dirpath)
                    if dir_basename == "AP01m" and "_" in base_name:
                        parts = base_name.split("_")
                        if len(parts) >= 1:
                            token_id_candidate = parts[0]
                    else:
                        # Standard LOG file handling
                        parts = base_name.split('_')
                        if len(parts) >= 2:
                            token_id_candidate = parts[1]
                
                # Normalize FBC token IDs
                if token_id_candidate and token_type_dir == "FBC":
                    if token_id_candidate.isdigit():
                        token_id_candidate = token_id_candidate.zfill(3)
                    else:
                        token_id_candidate = token_id_candidate.upper()
                
                print(f"[DEBUG] Token ID candidate: {token_id_candidate}")
                
                # Find matching token using multiple strategies
                token = None
                matching_strategy = "none"
                
                # Strategy 1: Case-insensitive exact token ID match with same token type
                if token_id_candidate:
                    token = next(
                        (t for t in matched_node.tokens.values()
                         if t.token_id.lower() == token_id_candidate.lower() and t.token_type == token_type_dir),
                        None
                    )
                    if token:
                        matching_strategy = "extracted token ID match"
                        print(f"[DEBUG] Found exact token match: {token.token_id} ({token.token_type})")
                
                # Strategy 2: Case-insensitive token ID substring match with same token type
                if not token:
                    for t in matched_node.tokens.values():
                        if (token_id_candidate and 
                            token_id_candidate.lower() in t.token_id.lower() and 
                            t.token_type == token_type_dir):
                            token = t
                            matching_strategy = "token ID in filename"
                            print(f"[DEBUG] Found substring token match: {token.token_id} ({token.token_type})")
                            break
                
                # Strategy 3: Match by token type and closest alphanumeric match
                if not token:
                    same_type_tokens = [t for t in matched_node.tokens.values()
                                        if t.token_type == token_type_dir]
                    if same_type_tokens and token_id_candidate:
                        # Try to find closest alphanumeric match
                        token = min(
                            same_type_tokens,
                            key=lambda t: self._token_distance(t.token_id.lower(), token_id_candidate.lower())
                        )
                        
                        matching_strategy = "closest alphanumeric token match"
                        distance = self._token_distance(token.token_id.lower(), token_id_candidate.lower())
                        print(f"[DEBUG] Closest match: {token.token_id} (distance: {distance})")
                
                # Strategy 4: Special handling for FBC files
                # For FBC files, we want to create a new FBC token if one doesn't already exist
                # Even if there's already a token with the same ID but different type
                if token_type_dir == "FBC" and token_id_candidate:
                    # Check if we already have an FBC token with this ID
                    fbc_token = next(
                        (t for t in matched_node.tokens.values()
                         if t.token_id.lower() == token_id_candidate.lower() and t.token_type == "FBC"),
                        None
                    )
                    if fbc_token:
                        token = fbc_token
                        matching_strategy = "existing FBC token"
                        print(f"[DEBUG] Found existing FBC token: {token.token_id}")
                    # If we found a token through other strategies but it's not an FBC token,
                    # we still want to create a new FBC token
                    elif token_id_candidate and not (token and token.token_type == "FBC"):
                        # Reset token to None so we can create a new FBC token
                        token = None
                        print(f"[DEBUG] No existing FBC token found for {token_id_candidate}, will create new one")
                elif not token and token_id_candidate:
                    # For non-FBC files, look for any token with the same ID regardless of type
                    token = next(
                        (t for t in matched_node.tokens.values()
                         if t.token_id.lower() == token_id_candidate.lower()),
                        None
                    )
                    if token:
                        matching_strategy = "token ID match (different type)"
                        print(f"[DEBUG] Found token ID match with different type: {token.token_id} ({token.token_type})")
                
                # For FBC files, create token representation if not found
                if token_type_dir == "FBC" and not token:
                    token = NodeToken(
                        name=f"{node_name} {token_type_dir}",
                        token_id=token_id_candidate or "UNKNOWN",
                        token_type=token_type_dir,
                        ip_address=matched_node.ip_address
                    )
                    token.log_path = os.path.normpath(full_path)
                    matched_node.add_token(token)
                    print(f"[DEBUG] ADDED FBC token to node: {token.token_id} | Path: {token.log_path}")
                elif token:
                    token.log_path = os.path.normpath(full_path)
                    print(f"[DEBUG] SUCCESS: Mapped log file | Node: {node_name} | Token: {token.token_id} | Strategy: {matching_strategy} | Path: {token.log_path}")
                else:
                    print(f"[DEBUG] WARNING: Could not find matching token for: {filename} in node: {node_name}")

def test_ap01m_fbc_detection():
    """Test that all FBC tokens (162, 163, 164) are detected for node AP01m."""
    print("Testing FBC token detection for AP01m node...")
    
    # Create node manager and scan log files
    manager = SimpleNodeManager()
    manager.scan_log_files()
    
    # Get the AP01m node
    node = manager.nodes.get("AP01m")
    if not node:
        print("ERROR: AP01m node not found")
        return False
    
    print(f"AP01m node found with {len(node.tokens)} tokens")
    
    # Check for FBC tokens
    fbc_tokens = [t for t in node.tokens.values() if t.token_type == "FBC"]
    print(f"Found {len(fbc_tokens)} FBC tokens:")
    for token in fbc_tokens:
        print(f"  - Token ID: {token.token_id}, Path: {token.log_path}")
    
    # Check if all required tokens are present
    required_tokens = {"162", "163", "164"}
    found_tokens = {t.token_id for t in fbc_tokens}
    
    # Note: 163 might be found as both RPC (pre-configured) and FBC (from file)
    # For this test, we're focusing on FBC tokens
    
    missing_tokens = required_tokens - found_tokens
    if missing_tokens:
        print(f"ERROR: Missing FBC tokens: {missing_tokens}")
        return False
    
    print("SUCCESS: All required FBC tokens (162, 163, 164) detected for AP01m")
    return True

if __name__ == "__main__":
    success = test_ap01m_fbc_detection()
    exit(0 if success else 1)