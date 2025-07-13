"""
Node Manager
Loads and manages node configuration for Commander UI
"""
import json
import os
import logging
from typing import Dict, List, Optional
from .models import Node, NodeToken

class NodeManager:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        # Set log root to user's DIA directory
        self.log_root = r"C:\Users\gorjovicgo\_DIA"
        print(f"[DEBUG] Log root set to: {self.log_root}")
        self.selected_node: Optional[Node] = None
        # Default config path relative to project root
        self.config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "nodes.json"
        )
        
    def set_config_path(self, path):
        """Set the configuration file path"""
        self.config_path = path
        
    def set_log_root(self, path):
        """Set the root folder for log files"""
        self.log_root = path
        # Update log paths when log root changes
        self.scan_log_files()
        
    def load_configuration(self, file_path: str = None) -> bool:
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
            
    def _parse_config(self, config_data: dict):
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
                        print(f"Warning: Skipping token with missing 'token_id' in node '{node_name}'.")
                        continue
                    
                    # Ensure token_id is a string and strip whitespace
                    token_id = str(token_id).strip()
                    if not token_id:  # Check if empty after stripping
                        print(f"Warning: Skipping token with empty 'token_id' in node '{node_name}'.")
                        continue
                        
                    # Normalize FBC token IDs to 3 digits with leading zeros
                    if token_data["token_type"].upper() == "FBC" and token_id.isdigit():
                        token_id = token_id.zfill(3)

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
                            name=f"{node.name} {token_id}",
                            token_id=token_id,
                            token_type=token_type,
                            ip_address=token_data.get("ip_address", node.ip_address),
                            port=token_data["port"],
                            protocol=token_data.get("protocol", "telnet")
                        )
                        
                        # Generate log path with formatted IP
                        token.log_path = self._generate_log_path(
                            node.name,
                            token.token_id,
                            token.token_type,
                            token.ip_address
                        )
                        
                        node.add_token(token)
                    except Exception as e:
                        print(f"Error processing token: {str(e)}")
                
                self.nodes[node.name] = node
            except Exception as e:
                print(f"Error processing node: {str(e)}")
                
    def _convert_old_format(self, old_config: list) -> list:
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
                
                # Extract token type from parent directory name
                token_type_dir = os.path.basename(dirpath)
                
                # Handle nested directory structures (e.g., FBC/LOG/)
                parent_dir = os.path.basename(os.path.dirname(dirpath))
                if parent_dir in token_types:
                    token_type_dir = parent_dir
                
                # Extract node name from either filename or directory
                if token_type_dir == "LOG":
                    # For LOG files, extract node name from filename (format: NODE_IP.log)
                    node_name = filename.split('_')[0]
                    print(f"[DEBUG] LOG file - extracted node name from filename: {node_name}")
                else:
                    # For token-specific files, use directory name for node
                    node_name = os.path.basename(dirpath)
                    print(f"[DEBUG] Node name from directory: {node_name}")
                
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
                
                # Extract potential token ID from filename (last numeric part)
                token_candidates = [part for part in base_name.split('_') if part.isdigit()]
                token_id_candidate = token_candidates[-1] if token_candidates else None
                
                # Strategy 1: Match by extracted token ID candidate
                if token_id_candidate:
                    token = next(
                        (t for t in matched_node.tokens.values()
                         if t.token_id == token_id_candidate),
                        None
                    )
                    if token:
                        matching_strategy = "extracted token ID match"
                
                # Strategy 2: Filename contains token ID
                if not token:
                    for t in matched_node.tokens.values():
                        if t.token_id in base_name:
                            token = t
                            matching_strategy = "token ID in filename"
                            break
                
                # Strategy 3: Match by token type and closest numeric match
                if not token:
                    same_type_tokens = [t for t in matched_node.tokens.values()
                                        if t.token_type == token_type_dir]
                    if same_type_tokens:
                        # Try to find closest numeric match
                        if token_id_candidate and token_id_candidate.isdigit():
                            token_id_int = int(token_id_candidate)
                            closest = min(
                                same_type_tokens,
                                key=lambda t: abs(int(t.token_id) - token_id_int)
                            )
                            token = closest
                            matching_strategy = "closest numeric token match"
                
                # For LOG files, create a generic token representation
                if token_type_dir == "LOG" or (not token and token_type_dir in token_types):
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
                    print(f"[DEBUG] SUCCESS: Mapped log file | Node: {node_name} | Token: {token.token_id} | Strategy: {matching_strategy} | Path: {normalized_path}")
                else:
                    print(f"[DEBUG] WARNING: Could not find matching token for: {filename} in node: {node_name}")
                    print(f"[DEBUG] Available tokens: {[t.token_id for t in matched_node.tokens.values()]}")
    def _generate_log_path(self, node_name: str, token_id: str, log_type: str, ip_address: str) -> str:
        """Generates standardized log path with formatted IP"""
        # Format IP address: 192.168.0.11 -> 192-168-0-11
        formatted_ip = ip_address.replace('.', '-')
        
        # Create path: <log_root>/<token_type>/<node_name>/<filename>
        filename = f"{node_name}_{formatted_ip}_{token_id}.{log_type.lower()}"
        return os.path.join(self.log_root, log_type, node_name, filename)
    
    def get_node(self, node_name: str) -> Optional[Node]:
        """Retrieves node by name"""
        return self.nodes.get(node_name)
    
    def get_token(self, node_name: str, token_id: str) -> Optional[NodeToken]:
        """Retrieves token from a node with normalized token ID"""
        if node := self.nodes.get(node_name):
            # Normalize token ID by stripping and converting to string
            normalized_id = str(token_id).strip()
            return node.tokens.get(normalized_id)
        return None
        
    def get_node_by_token(self, token: NodeToken) -> Optional[Node]:
        """Finds the node that owns a given token"""
        for node in self.nodes.values():
            if token.token_id in node.tokens:
                return node
        return None
        
    def update_status(self, node_name: str, status: str):
        """Updates node connection status"""
        if node := self.nodes.get(node_name):
            node.status = status
    
    def get_all_nodes(self) -> List[Node]:
        """Returns all nodes as list"""
        return list(self.nodes.values())
        
    def add_node(self, node_data: dict):
        """Adds a new node from UI"""
        node = Node(
            name=node_data["name"],
            ip_address=node_data["ip_address"]
        )
        
        for token_data in node_data["tokens"]:
            token = NodeToken(
                name=f"{node.name} {token_data['token_id']}",
                token_id=token_data["token_id"],
                token_type=token_data["token_type"],
                ip_address=token_data.get("ip_address", node.ip_address),
                port=token_data["port"],
                protocol=token_data.get("protocol", "telnet")
            )
            token.log_path = self._generate_log_path(
                node.name,
                token.token_id,
                token.token_type,
                token.ip_address
            )
            node.add_token(token)
            
        self.nodes[node.name] = node
    
    def save_configuration(self, file_path: str = None) -> bool:
        """Saves current configuration to JSON file"""
        if file_path is None:
            file_path = self.config_path
        config_data = []
        for node in self.nodes.values():
            node_data = {
                "name": node.name,
                "ip_address": node.ip_address,
                "tokens": []
            }
            
            for token in node.tokens.values():
                token_data = {
                    "token_id": token.token_id,
                    "token_type": token.token_type,
                    "ip_address": token.ip_address,
                    "port": token.port,
                    "protocol": token.protocol
                }
                node_data["tokens"].append(token_data)
                
            config_data.append(node_data)
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
            return True
        except (OSError, TypeError):
            return False
            
    def create_empty_config(self, file_path: str):
        """Creates an empty configuration file with proper format"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)

    def get_selected_node(self) -> Optional[Node]:
        """Returns currently selected node or None if none selected"""
        return self.selected_node

    def set_selected_node(self, node_name: str):
        """Sets the currently selected node"""
        self.selected_node = self.nodes.get(node_name)
