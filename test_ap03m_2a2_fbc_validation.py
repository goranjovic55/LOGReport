import sys
import os
import json

class Node:
    def __init__(self, name, ip_address):
        self.name = name
        self.ip_address = ip_address
        self.tokens = {}
        self.status = "disconnected"
        
    def add_token(self, token):
        self.tokens[token.token_id] = token

class NodeToken:
    def __init__(self, name, token_id, token_type, ip_address, port=23, protocol="telnet"):
        self.name = name
        self.token_id = token_id
        self.token_type = token_type.upper()
        self.ip_address = ip_address
        self.port = port
        self.protocol = protocol
        self.log_path = None

class NodeManager:
    def __init__(self):
        self.nodes = {}
        # Set log root to project's test_logs directory
        self.log_root = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "test_logs"
        )
        print(f"[DEBUG] Log root set to: {self.log_root}")
        self.selected_node = None
        # Use test nodes configuration for development
        self.config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "nodes_test.json"
        )
        # Load configuration immediately after setting path
        self.load_configuration()
        
    def load_configuration(self, file_path=None):
        """Loads node configuration from JSON file"""
        path = file_path or self.config_path
        
        if not path:
            print("Configuration path is empty")
            return False
            
        try:
            abs_path = os.path.abspath(path)
            normalized_path = os.path.normpath(abs_path)
            print(f"Loading configuration from: {normalized_path}")
            if not os.path.exists(normalized_path):
                print(f"Configuration file does not exist: {normalized_path}")
                return False
                
            with open(normalized_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                # Validate configuration before parsing
                if not self._validate_config(config_data):
                    print("Configuration validation failed")
                    return False
                self._parse_config(config_data)
            print("Configuration loaded successfully")
            return True
        except FileNotFoundError:
            print(f"File not found: {path}")
            return False
        except json.JSONDecodeError as e:
            print(f"JSON parsing error in {path}: {str(e)}")
            return False
        except KeyError as e:
            print(f"Missing required key in configuration: {str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error loading configuration: {str(e)}")
            return False
            
    def _parse_config(self, config_data):
        """Parses raw configuration into Node objects, supports multiple formats"""
        self.nodes.clear()  # Clear existing nodes
        
        # Check if this is the old format (array of nodes without nested tokens)
        # Check if this is the old format (array of nodes with string tokens arrays)
        if isinstance(config_data, list) and config_data:
            first_node = config_data[0]
            is_old_format = (
                'ip' in first_node and
                'tokens' in first_node and
                isinstance(first_node['tokens'], list) and
                all(isinstance(t, str) for t in first_node['tokens'])
            )
            
            if is_old_format:
                print("Detected old format - converting to new format")
                config_data = self._convert_old_format(config_data)
        
        for node_data in config_data:
            try:
                # Skip entries that don't have required fields
                if "name" not in node_data or "ip" not in node_data:
                    print(f"Skipping invalid node entry: {node_data}")
                    continue
                    
                node = Node(
                    name=node_data["name"],
                    ip_address=node_data["ip"]
                )
                
                # Handle old format with string tokens
                tokens = node_data.get("tokens", [])
                token_types = node_data.get("types", [])
                
                # Match token ids with types
                for i, token_id in enumerate(tokens):
                    # Get token type
                    token_type = token_types[i] if i < len(token_types) else 'UNKNOWN'
                    
                    # Normalize FBC token IDs: pad numeric IDs with zeros, convert alphanumeric to uppercase
                    if token_type.upper() == "FBC":
                        if str(token_id).isdigit():
                            token_id = str(token_id).zfill(3)
                        else:
                            token_id = str(token_id).upper()
                    
                    token = NodeToken(
                        name=node.name,
                        token_id=token_id,
                        token_type=token_type,
                        ip_address=node.ip_address,
                        port=23  # Default port
                    )
                    node.add_token(token)
                
                self.nodes[node.name] = node
            except Exception as e:
                print(f"Error processing node: {str(e)}")
                
    def _validate_config(self, config_data):
        """Validates configuration data for consistency and correctness"""
        if not isinstance(config_data, list):
            print("Configuration data must be a list")
            return False
            
        for i, node_data in enumerate(config_data):
            # Check required fields
            if "name" not in node_data:
                print(f"Node {i} missing required 'name' field")
                return False
                
            if "ip" not in node_data:
                print(f"Node {i} missing required 'ip' field")
                return False
                
            # Validate tokens if present
            tokens = node_data.get("tokens", [])
            if not isinstance(tokens, list):
                print(f"Node {i} tokens must be a list")
                return False
                
        return True
        
    def _convert_old_format(self, old_config):
        """Converts old configuration format to new format"""
        # This is a simplified version for our test
        return old_config
            
    def scan_log_files(self, log_root=None):
        """
        Scans filesystem for log files recursively under log root
        Handles all file locations and structures
        """
        root = log_root or self.log_root
        print(f"[DEBUG] Scanning log root: {root}")
        if not os.path.exists(root):
            print(f"[DEBUG] ERROR: Log root does not exist")
            return
            
        print(f"[DEBUG] Log root exists")
        
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
                
                # Improved filename parsing for various naming conventions
                # Handle files with extensions in filename like 162_FBC.log
                if filename.lower().endswith('.log'):
                    # Check if in a token directory (FBC, RPC, etc.)
                    current_dir = os.path.basename(dirpath)
                    parent_dir = os.path.basename(os.path.dirname(dirpath))
                    
                    token_types = ["FBC", "RPC", "LOG", "LIS"]
                    if parent_dir in token_types:
                        # File is in <token_type>/<node_name> directory
                        token_type_dir = parent_dir
                        node_name = current_dir
                        print(f"[DEBUG] {token_type_dir} LOG file in node directory: node_name={node_name}")
                    elif current_dir in token_types:
                        # File is directly in token directory
                        token_type_dir = current_dir
                        # Extract node name from filename (first alphanumeric segment)
                        node_name = base_name.split('_')[0]
                        print(f"[DEBUG] {token_type_dir} LOG file: node_name={node_name}")
                    else:
                        # Check if filename contains token type
                        token_type_in_name = None
                        for tt in token_types:
                            if tt.lower() in filename.lower():
                                token_type_in_name = tt
                                break
                        
                        if token_type_in_name:
                            token_type_dir = token_type_in_name
                            # Extract node name from filename (first alphanumeric segment)
                            node_name = base_name.split('_')[0]
                            print(f"[DEBUG] {token_type_dir} LOG file detected in filename: node_name={node_name}")
                        else:
                            token_type_dir = "LOG"
                            node_name = base_name.split('_')[0]
                            print(f"[DEBUG] Generic LOG file: node_name={node_name}")
                else:
                    # For .fbc, .rpc, .lis files, determine type from extension
                    ext = os.path.splitext(filename)[1][1:].upper()  # Remove the dot
                    token_type_dir = ext
                    
                    # Extract node name from directory structure
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
                
                # Extract token ID from filename using improved parsing
                token_id_candidate = self._extract_token_id_from_filename(base_name, token_type_dir)
                
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
                
                # Try to match with existing tokens first - exact match with token ID and type
                if token_id_candidate:
                    token = next(
                        (t for t in matched_node.tokens.values()
                         if t.token_id.lower() == token_id_candidate.lower() and t.token_type == token_type_dir),
                        None
                    )
                    if token:
                        matching_strategy = "exact token ID and type match"
                
                # If no exact match, try matching by token ID only (same type tokens)
                if not token:
                    same_type_tokens = [t for t in matched_node.tokens.values()
                                        if t.token_type == token_type_dir]
                    if same_type_tokens and token_id_candidate:
                        # Try direct match first
                        token = next(
                            (t for t in same_type_tokens
                             if t.token_id.lower() == token_id_candidate.lower()),
                            None
                        )
                        if token:
                            matching_strategy = "token ID match within same type"
                
                # For FBC tokens, if no match found, don't create a new token automatically
                # Only create new tokens for LOG/LIS files or when explicitly needed
                if token_type_dir == "FBC" and not token:
                    print(f"[DEBUG] No matching FBC token found for {token_id_candidate} in node {node_name}")
                    print(f"[DEBUG] Available FBC tokens: {[t.token_id for t in matched_node.tokens.values() if t.token_type == 'FBC']}")
                elif token_type_dir in ["LOG", "LIS"] and not token:
                    # For LOG and LIS files, create a token if none exists
                    token = NodeToken(
                        name=f"{node_name} {token_type_dir}",
                        token_id=token_id_candidate or "UNKNOWN",
                        token_type=token_type_dir,
                        ip_address=matched_node.ip_address
                    )
                    normalized_path = os.path.normpath(full_path)
                    token.log_path = normalized_path
                    matched_node.add_token(token)
                    print(f"[DEBUG] ADDED {token_type_dir} token to node: {token.token_id} | Path: {normalized_path}")
                
                # For other token types, maintain existing behavior
                elif token_type_dir == "LOG" or (not token and token_type_dir in ["FBC", "RPC", "LOG", "LIS"]):
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
                    
    def _extract_token_id_from_filename(self, base_name, token_type):
        """
        Extract token ID from filename using improved parsing for various naming conventions.
        Handles patterns like:
        - AP01m_162_FBC
        - AP01m_163_RPC
        - 162_FBC
        - 163_RPC
        - AP01m_192-168-0-11_162
        - TEST_NODE_192.168.0.1_123
        """
        parts = base_name.split('_')
        if not parts:
            return ""
            
        # If the last part is a token type, use the part before it as token ID
        if len(parts) >= 2 and parts[-1].upper() in ["FBC", "RPC", "LOG", "LIS", "VNC", "FTP"]:
            return parts[-2]
            
        # If we have multiple parts, try to identify the token ID
        # Look for numeric/alphanumeric part that could be token ID
        # Usually it's the last part or second to last part
        if len(parts) >= 2:
            # Check if the last part is a number (likely the token ID)
            if parts[-1].isdigit():
                return parts[-1]
            # Check if the second to last part is a number (likely the token ID)
            elif len(parts) >= 3 and parts[-2].isdigit():
                return parts[-2]
            # For alphanumeric tokens, check the last part
            elif parts[-1].isalnum() and not parts[-1].isdigit():
                # Additional check to avoid IP-like parts
                if '.' not in parts[-1] and '-' not in parts[-1]:
                    return parts[-1]
                    
        # If we have at least one part, use the last one as token ID
        return parts[-1] if parts else ""

def test_ap03m_2a2_fbc_token():
    """Test the specific edge case with AP03m node and 2a2 FBC token"""
    print("Testing AP03m node with 2a2 FBC token...")
    
    # Create a NodeManager instance
    manager = NodeManager()
    
    # Print loaded nodes and tokens for AP03m
    print("\nLoaded AP03m node:")
    ap03m_node = manager.nodes.get("AP03m")
    if ap03m_node:
        print(f"  Node: {ap03m_node.name} (IP: {ap03m_node.ip_address})")
        for token_id, token in ap03m_node.tokens.items():
            print(f"    Token: {token_id} (Type: {token.token_type}, Port: {token.port})")
    else:
        print("  AP03m node not found!")
        return False
    
    # Test the _extract_token_id_from_filename method for the specific case
    print("\nTesting _extract_token_id_from_filename method for 2a2_FBC.log:")
    base_name = "2a2_FBC"
    token_type = "FBC"
    token_id = manager._extract_token_id_from_filename(base_name, token_type)
    print(f"  {base_name} -> Raw Token ID: {token_id}")
    
    # Apply FBC token normalization (what happens during scan_log_files)
    if token_type == "FBC":
        if token_id.isdigit():
            normalized_token_id = token_id.zfill(3)
        else:
            normalized_token_id = token_id.upper()
    else:
        normalized_token_id = token_id.strip()
        
    print(f"  {base_name} -> Normalized Token ID: {normalized_token_id}")
    
    # Check if the normalized token ID matches what we expect
    expected_token_id = "2A2"  # After normalization
    if normalized_token_id == expected_token_id:
        print(f"  ✓ Token ID extraction and normalization correct: {normalized_token_id}")
    else:
        print(f"  ✗ Token ID normalization issue: got {normalized_token_id}, expected {expected_token_id}")
        return False
    
    # Test scanning log files for the specific case
    print("\nTesting scan_log_files method for AP03m/2a2_FBC.log:")
    test_logs_path = os.path.join(os.path.dirname(__file__), 'test_logs')
    if os.path.exists(test_logs_path):
        print(f"Scanning log files in: {test_logs_path}")
        manager.log_root = test_logs_path
        manager.scan_log_files()
        
        # Check if the token has the correct log path
        ap03m_node = manager.nodes.get("AP03m")
        if ap03m_node:
            token_2a2 = ap03m_node.tokens.get("2A2")  # After normalization
            if token_2a2 and token_2a2.log_path:
                expected_path = os.path.join(test_logs_path, "AP03m", "2a2_FBC.log")
                if os.path.normpath(token_2a2.log_path) == os.path.normpath(expected_path):
                    print(f"  ✓ Log path correctly mapped: {token_2a2.log_path}")
                    return True
                else:
                    print(f"  ✗ Log path mismatch: got {token_2a2.log_path}, expected {expected_path}")
                    # Let's see what path was actually set
                    print(f"      Actual path: {token_2a2.log_path}")
                    print(f"      Expected path: {expected_path}")
                    return False
            else:
                print("  ✗ Token 2A2 not found or has no log path")
                # Let's check what tokens are available
                print(f"      Available tokens: {list(ap03m_node.tokens.keys())}")
                return False
        else:
            print("  ✗ AP03m node not found after scanning")
            return False
    else:
        print("Test logs directory not found")
        return False

if __name__ == "__main__":
    success = test_ap03m_2a2_fbc_token()
    if success:
        print("\n✓ AP03m 2a2 FBC token validation PASSED")
    else:
        print("\n✗ AP03m 2a2 FBC token validation FAILED")
    sys.exit(0 if success else 1)