import sys
import os
import json
import re

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import only the models we need
from commander.models import Node, NodeToken

class TestNodeManager:
    def __init__(self):
        self.nodes = {}
        self.log_root = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "test_logs"
        )
        print(f"[DEBUG] Log root set to: {self.log_root}")
        self.config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "nodes_test.json"
        )
        self.load_configuration()
        
    def set_config_path(self, path):
        """Set the configuration file path"""
        self.config_path = path
        
    def set_log_root(self, path):
        """Set the root folder for log files"""
        self.log_root = path
        
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
                if "name" not in node_data or "ip_address" not in node_data:
                    print(f"Skipping invalid node entry: {node_data}")
                    continue
                    
                node = Node(
                    name=node_data["name"],
                    ip_address=node_data["ip_address"]
                )
                
                tokens = node_data.get("tokens", [])
                for token_data in node_data.get('tokens', []):
                    token_id = token_data.get('token_id')
                    if token_id is None:
                        print(f"Warning: Skipping token with missing 'token_id' in node '{node.name}'.")
                        continue
                    
                    # Ensure token_id is a string and strip whitespace
                    token_id = str(token_id).strip()
                    if not token_id:  # Check if empty after stripping
                        print(f"Warning: Skipping token with empty 'token_id' in node '{node.name}'.")
                        continue
                        
                    # Normalize FBC token IDs: pad numeric IDs with zeros, convert alphanumeric to uppercase
                    if token_data["token_type"].upper() == "FBC":
                        if token_id.isdigit():
                            token_id = token_id.zfill(3)
                        else:
                            token_id = token_id.upper()

                    try:
                        # Validate required fields exist
                        if "token_type" not in token_data or "port" not in token_data:
                            print(f"Skipping invalid token entry: {token_data}")
                            continue
                            
                        # Normalize token type to uppercase for consistent classification
                        token_type = token_data["token_type"].upper()
                        
                        # Ensure token_id is string and exists
                        token_id = str(token_id).strip()
                        if not token_id:
                            print(f"Skipping token with empty 'token_id' in node '{node.name}'")
                            continue
                            
                        token = NodeToken(
                            name=node.name,
                            token_id=token_id,
                            token_type=token_type,
                            ip_address=token_data.get("ip_address", node.ip_address),
                            port=token_data["port"],
                            protocol=token_data.get("protocol", "telnet")
                        )
                        
                        node.add_token(token)
                    except Exception as e:
                        print(f"Error processing token: {str(e)}")
                
                self.nodes[node.name] = node
            except Exception as e:
                print(f"Error processing node: {str(e)}")
                
    def _convert_old_format(self, old_config):
        """Converts old configuration format to new format"""
        new_config = []
        for node in old_config:
            # Skip entries that don't match old format
            if 'ip' not in node:
                continue
                
            tokens = []
            token_ids = node.get('tokens', [])
            token_types = node.get('types', ['UNKNOWN'] * len(token_ids))
            
            # Match token ids with types
            for i, token_id in enumerate(token_ids):
                # Get token type
                token_type = token_types[i] if i < len(token_types) else 'UNKNOWN'
                
                tokens.append({
                    "token_id": str(token_id),
                    "token_type": token_type,
                    "port": 23  # Default port
                })
                
            new_config.append({
                "name": node["name"],
                "ip_address": node["ip"],
                "tokens": tokens
            })
            
        return new_config
        
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
                
                # Improved filename parsing for various naming conventions
                # Handle files with extensions in filename like 162_FBC.log
                if filename.lower().endswith('.log'):
                    # Extract token type from filename if present
                    parts = base_name.split('_')
                    if len(parts) >= 2:
                        potential_token_type = parts[-1].upper()
                        if potential_token_type in token_types:
                            token_type_dir = potential_token_type
                            # Extract node name from the beginning part
                            node_name = '_'.join(parts[:-1])
                        else:
                            token_type_dir = "LOG"
                            node_name = parts[0]
                    else:
                        token_type_dir = "LOG"
                        node_name = base_name
                    print(f"[DEBUG] LOG file detected: node_name={node_name}, token_type={token_type_dir}")
                else:
                    # For .fbc, .rpc, .lis files, determine type from extension
                    ext = os.path.splitext(filename)[1][1:].upper()  # Remove the dot
                    token_type_dir = ext
                    
                    # Extract node name from directory structure
                    parent_dir = os.path.basename(os.path.dirname(dirpath))
                    if parent_dir in token_types:
                        # File is in a structure like FBC/AP01m/filename.fbc
                        token_type_dir = parent_dir
                        node_name = os.path.basename(dirpath)
                        print(f"[DEBUG] {token_type_dir} file in node directory: node_name={node_name}")
                    else:
                        # File is in a structure like AP01m/filename.fbc
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
                
                # If still no match, try alphanumeric matching for same type tokens
                if not token and token_id_candidate:
                    same_type_tokens = [t for t in matched_node.tokens.values()
                                        if t.token_type == token_type_dir]
                    if same_type_tokens:
                        print(f"[DEBUG] Starting alphanumeric matching for {token_type_dir} tokens: {token_id_candidate}")
                        print(f"[DEBUG] Available {token_type_dir} tokens: {[t.token_id for t in same_type_tokens]}")
                        token = min(
                            same_type_tokens,
                            key=lambda t: self._token_distance(t.token_id.lower(), token_id_candidate.lower())
                        )
                        distance = self._token_distance(token.token_id.lower(), token_id_candidate.lower())
                        print(f"[DEBUG] Closest match: {token.token_id} (distance: {distance})")
                        matching_strategy = "closest alphanumeric token match within same type"
                
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
                    
    def _token_distance(self, token1, token2):
        """Calculates similarity distance between two token IDs"""
        # Normalize tokens to lowercase for case-insensitive comparison
        token1 = token1.lower()
        token2 = token2.lower()
        
        if token1 == token2:
            return 0
        if token1.startswith(token2) or token2.startswith(token1):
            return 1
        return 2
        
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

def test_fbc_token_detection():
    """Test FBC token detection in NodeManager.scan_log_files()"""
    print("Testing FBC token detection...")
    
    # Create a NodeManager instance
    manager = TestNodeManager()
    
    # Load the test configuration
    test_config_path = os.path.join(os.path.dirname(__file__), 'nodes_test.json')
    if os.path.exists(test_config_path):
        print(f"Loading test configuration from: {test_config_path}")
        manager.set_config_path(test_config_path)
        success = manager.load_configuration()
        print(f"Configuration load result: {success}")
    else:
        print("Test configuration not found, using default configuration")
    
    # Print loaded nodes and tokens
    print("\nLoaded nodes:")
    for node_name, node in manager.nodes.items():
        print(f"  Node: {node_name} (IP: {node.ip_address})")
        for token_id, token in node.tokens.items():
            print(f"    Token: {token_id} (Type: {token.token_type}, Port: {token.port})")
    
    # Test the _extract_token_id_from_filename method
    print("\nTesting _extract_token_id_from_filename method:")
    test_cases = [
        ("AP01m_162_FBC", "FBC"),
        ("AP01m_163_RPC", "RPC"),
        ("162_FBC", "FBC"),
        ("163_RPC", "RPC"),
        ("AP01m_192-168-0-11_162", "FBC"),
        ("AP01m_192.168.0.11_162", "FBC"),
    ]
    
    for base_name, token_type in test_cases:
        token_id = manager._extract_token_id_from_filename(base_name, token_type)
        print(f"  {base_name} -> {token_id}")
    
    # Test scanning log files
    print("\nTesting scan_log_files method:")
    test_logs_path = os.path.join(os.path.dirname(__file__), 'test_logs')
    if os.path.exists(test_logs_path):
        print(f"Scanning log files in: {test_logs_path}")
        manager.set_log_root(test_logs_path)
        manager.scan_log_files()
        
        # Check if FBC tokens were correctly detected
        print("\nChecking FBC token detection results:")
        for node_name, node in manager.nodes.items():
            fbc_tokens = [t for t in node.tokens.values() if t.token_type == "FBC"]
            if fbc_tokens:
                print(f"  Node {node_name}:")
                for token in fbc_tokens:
                    print(f"    Token {token.token_id}: log_path = {token.log_path}")
    else:
        print("Test logs directory not found")
    
    print("\nTest completed.")

if __name__ == "__main__":
    test_fbc_token_detection()