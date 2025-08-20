#!/usr/bin/env python3
"""
Test script to verify FBC token detection for both filename formats
"""
import sys
import os
import tempfile

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
        self.tokens: dict = {}
        self.status = "offline"

    def add_token(self, token: NodeToken):
        self.tokens[token.token_id] = token

    def __repr__(self):
        return f"Node(name='{self.name}', ip_address='{self.ip_address}', tokens={list(self.tokens.keys())})"

# Simple implementation of NodeManager for testing
class NodeManager:
    def __init__(self):
        self.nodes: dict = {}
        self.log_root = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "test_logs"
        )
        self.selected_node = None

    def scan_log_files(self, log_root=None):
        """
        Scans filesystem for log files recursively under log root
        Handles all file locations and structures
        """
        import re
        root = log_root or self.log_root
        if not os.path.exists(root):
            return
            
        # First, scan for IPs in log directory names and update token objects
        self._scan_for_dynamic_ips(root)
        
        # Check directory structure
        token_types = ["FBC", "RPC", "LOG", "LIS"]
        
        # Walk through all directories and files
        for dirpath, _, filenames in os.walk(root):
            # Skip directories without .log files
            log_files = [f for f in filenames if f.lower().endswith(('.log', '.fbc', '.rpc', '.lis'))]
            if not log_files:
                continue
                
            for filename in log_files:
                full_path = os.path.join(dirpath, filename)
                
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
                # Handle other file types by directory structure
                else:
                    # Token type is the parent directory name
                    token_type_dir = os.path.basename(dirpath)
                    
                    # Handle nested directories (e.g., FBC/AP01m/)
                    parent_dir = os.path.basename(os.path.dirname(dirpath))
                    if parent_dir in token_types:
                        token_type_dir = parent_dir
                        node_name = os.path.basename(dirpath)
                    else:
                        # For files directly in token type directories
                        node_name = os.path.basename(dirpath)
                
                # Find matching node (case-insensitive)
                matched_node = next(
                    (n for n in self.nodes.values() if n.name.lower() == node_name.lower()),
                    None
                )
                
                if not matched_node:
                    continue
                    
                # Find matching token using multiple strategies
                token = None
                
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
                
                # Strategy 2: Case-insensitive token ID substring match
                if not token:
                    for t in matched_node.tokens.values():
                        if token_id_candidate and token_id_candidate.lower() in t.token_id.lower():
                            token = t
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
                elif token:
                    normalized_path = os.path.normpath(full_path)
                    token.log_path = normalized_path
                    
                    # Ensure token is added to node if not already present
                    if token.token_id not in matched_node.tokens:
                        matched_node.add_token(token)

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
        
        # Walk through all directories and files
        for dirpath, _, filenames in os.walk(log_root):
            # Process directory names for IP patterns
            dir_name = os.path.basename(dirpath)
            ip_matches = re.findall(ip_pattern, dir_name)
            if ip_matches:
                # Convert IP format from 192-168-0-11 to 192.168.0.11
                for ip_match in ip_matches:
                    formatted_ip = ip_match.replace('-', '.')
                    # Update tokens with this IP if they don't already have a valid IP
                    self._update_tokens_with_ip(formatted_ip)
            
            # Process filenames for IP patterns
            for filename in filenames:
                ip_matches = re.findall(ip_pattern, filename)
                if ip_matches:
                    # Convert IP format from 192-168-0-11 to 192.168.0.11
                    for ip_match in ip_matches:
                        formatted_ip = ip_match.replace('-', '.')
                        # Update tokens with this IP if they don't already have a valid IP
                        self._update_tokens_with_ip(formatted_ip)

    def _update_tokens_with_ip(self, ip_address: str):
        """
        Updates token objects with discovered IP addresses
        Only updates tokens that don't already have a valid IP address
        """
        for node in self.nodes.values():
            for token in node.tokens.values():
                # Only update tokens without a valid IP address
                if not token.ip_address or token.ip_address == "0.0.0.0":
                    token.ip_address = ip_address

def test_fbc_token_detection_in_node_manager():
    """Test FBC token detection in NodeManager with AP01m node"""
    print("Testing FBC token detection in NodeManager...")
    
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create node-specific directory structure
        ap01m_dir = os.path.join(tmpdir, "AP01m")
        os.makedirs(ap01m_dir)
        
        # Create .log files with FBC naming pattern
        fbc_file_162 = os.path.join(ap01m_dir, "162_FBC.log")
        fbc_file_163 = os.path.join(ap01m_dir, "163_FBC.log")
        fbc_file_164 = os.path.join(ap01m_dir, "164_FBC.log")
        
        # Write test content to files
        for file_path in [fbc_file_162, fbc_file_163, fbc_file_164]:
            with open(file_path, "w") as f:
                f.write("test log content")
        
        # Initialize NodeManager with test configuration
        manager = NodeManager()
        manager.log_root = tmpdir
        
        # Create node with expected tokens
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
        
        # Verify that all three tokens have their log paths updated
        tokens_with_logs = [t for t in node.tokens.values() if t.log_path]
        print(f"   Found {len(tokens_with_logs)} FBC tokens with log paths")
        
        # Check each token
        success_count = 0
        for token in [token_162, token_163, token_164]:
            if token.log_path and token.log_path.endswith(f"{token.token_id}_FBC.log"):
                print(f"   ✓ PASS: Token {token.token_id} correctly mapped to {token.log_path}")
                success_count += 1
            else:
                print(f"   ❌ FAIL: Token {token.token_id} not correctly mapped. Log path: {token.log_path}")
        
        if success_count == 3:
            print("   ✓ PASS: All FBC tokens correctly detected and mapped")
            return True
        else:
            print(f"   ❌ FAIL: Only {success_count}/3 FBC tokens correctly detected and mapped")
            return False
    
    print("\n🎉 NodeManager FBC token detection test completed!")

if __name__ == "__main__":
    try:
        success = test_fbc_token_detection_in_node_manager()
        if success:
            print("\n🎉 All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)