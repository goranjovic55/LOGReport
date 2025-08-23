"""
Node Manager
Loads and manages node configuration for Commander UI
"""
import json
import os
import logging
import re
from typing import Dict, List, Optional
from .models import Node, NodeToken
from .utils.token_utils import normalize_token, is_fbc_token, is_rpc_token

class NodeManager:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        # Set log root to user's DIA directory
        # Set log root to project's test_logs directory
        self.log_root = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "test_logs"
        )
        print(f"[DEBUG] Log root set to: {self.log_root}")
        self.selected_node: Optional[Node] = None
        # Use test nodes configuration for development
        self.config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "nodes_test.json"
        )
        # Load configuration immediately after setting path
        self.load_configuration()
        
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
            logging.error("Configuration path is empty")
            return False
            
        try:
            abs_path = os.path.abspath(path)
            normalized_path = os.path.normpath(abs_path)
            logging.info(f"Loading configuration from: {normalized_path}")
            
            if not os.path.exists(normalized_path):
                logging.error(f"Configuration file does not exist: {normalized_path}")
                return False
                
            # Check file size (prevent loading extremely large files)
            file_size = os.path.getsize(normalized_path)
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                logging.error(f"Configuration file too large: {file_size} bytes")
                return False
                
            with open(normalized_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # Validate configuration structure before parsing
            if not self._validate_config_structure(config_data):
                logging.error("Configuration structure validation failed")
                return False
                
            self._parse_config(config_data)
            logging.info("Configuration loaded successfully")
            return True
            
        except FileNotFoundError:
            logging.error(f"File not found: {path}")
            return False
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error in {path}: {str(e)}")
            return False
        except PermissionError:
            logging.error(f"Permission denied accessing configuration file: {path}")
            return False
        except KeyError as e:
            logging.error(f"Missing required key in configuration: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error loading configuration: {str(e)}")
            return False
    
    def _validate_config_structure(self, config_data) -> bool:
        """Validates the basic structure of configuration data"""
        if config_data is None:
            return False
            
        if isinstance(config_data, list):
            # List format - check if it's empty or contains valid nodes
            if not config_data:
                return True  # Empty list is valid
                
            # Check first node to determine format
            first_node = config_data[0]
            if not isinstance(first_node, dict):
                return False
                
            # Check for required fields in first node
            if "name" not in first_node or "ip_address" not in first_node:
                return False
                
            # Check tokens format if present
            if "tokens" in first_node:
                tokens = first_node["tokens"]
                if not isinstance(tokens, list):
                    return False
                    
                # Check first token structure
                if tokens and not isinstance(tokens[0], dict):
                    # This might be old format with string tokens
                    pass
                elif tokens:
                    # Check required fields for token objects
                    required_token_fields = {"token_type", "port"}
                    first_token = tokens[0]
                    if not all(field in first_token for field in required_token_fields):
                        return False
                        
        elif isinstance(config_data, dict):
            # Dict format - should have 'nodes' key
            if "nodes" not in config_data:
                return False
            if not isinstance(config_data["nodes"], list):
                return False
                
        else:
            # Unsupported format
            return False
            
        return True
            
    def _parse_config(self, config_data: dict):
        """Parses raw configuration into Node objects, supports multiple formats"""
        self.nodes.clear()  # Clear existing nodes
        
        # Validate configuration data structure
        if not config_data:
            logging.warning("Empty configuration data provided")
            return
            
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
                logging.info("Detected old format - converting to new format")
                config_data = self._convert_old_format(config_data)
        
        # Ensure config_data is a list after format conversion
        if not isinstance(config_data, list):
            logging.error(f"Invalid configuration format after conversion: {type(config_data)}")
            return
            
        processed_nodes = 0
        skipped_nodes = 0
        
        for node_data in config_data:
            try:
                # Validate node data structure
                if not isinstance(node_data, dict):
                    logging.warning(f"Skipping invalid node entry (not a dict): {node_data}")
                    skipped_nodes += 1
                    continue
                    
                if "name" not in node_data or "ip_address" not in node_data:
                    logging.warning(f"Skipping invalid node entry (missing required fields): {node_data}")
                    skipped_nodes += 1
                    continue
                    
                # Validate node name and IP address
                node_name = str(node_data["name"]).strip()
                ip_address = str(node_data["ip_address"]).strip()
                
                if not node_name or not ip_address:
                    logging.warning(f"Skipping node with empty name or IP address: {node_data}")
                    skipped_nodes += 1
                    continue
                
                node = Node(
                    name=node_name,
                    ip_address=ip_address
                )
                
                # Process tokens with enhanced validation
                tokens = node_data.get("tokens", [])
                if not isinstance(tokens, list):
                    logging.warning(f"Skipping invalid tokens format for node '{node_name}': {tokens}")
                    tokens = []
                
                processed_tokens = 0
                skipped_tokens = 0
                
                for token_data in tokens:
                    try:
                        # Validate token data structure
                        if not isinstance(token_data, dict):
                            logging.warning(f"Skipping invalid token entry (not a dict) in node '{node_name}': {token_data}")
                            skipped_tokens += 1
                            continue
                            
                        # Validate required fields exist
                        if "token_type" not in token_data or "port" not in token_data:
                            logging.warning(f"Skipping invalid token entry (missing required fields) in node '{node_name}': {token_data}")
                            skipped_tokens += 1
                            continue
                            
                        # Validate token type and port
                        token_type = str(token_data["token_type"]).strip().upper()
                        try:
                            port = int(token_data["port"])
                            if not (1 <= port <= 65535):
                                logging.warning(f"Skipping token with invalid port {port} in node '{node_name}'")
                                skipped_tokens += 1
                                continue
                        except (ValueError, TypeError):
                            logging.warning(f"Skipping token with invalid port format in node '{node_name}': {token_data['port']}")
                            skipped_tokens += 1
                            continue
                        
                        # Get and process token_id
                        token_id = token_data.get('token_id')
                        if token_id is None:
                            logging.warning(f"Skipping token with missing 'token_id' in node '{node_name}'")
                            skipped_tokens += 1
                            continue
                            
                        token_id = str(token_id).strip()
                        if not token_id:
                            logging.warning(f"Skipping token with empty 'token_id' in node '{node_name}'")
                            skipped_tokens += 1
                            continue
                            
                        # Use consistent token normalization from token_utils
                        normalized_token_id = normalize_token(token_id)
                        logging.debug(f"Normalized token: {token_id} -> {normalized_token_id}")
                        token_id = normalized_token_id

                        # Validate IP address if provided
                        token_ip = token_data.get("ip_address", node.ip_address)
                        if token_ip:
                            token_ip = str(token_ip).strip()
                            if not token_ip:
                                token_ip = node.ip_address

                        token = NodeToken(
                            name=node.name,
                            token_id=token_id,
                            token_type=token_type,
                            ip_address=token_ip,
                            port=port,
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
                        processed_tokens += 1
                    except Exception as e:
                        logging.error(f"Error processing token in node '{node_name}': {str(e)}")
                        skipped_tokens += 1
                
                logging.info(f"Processed node '{node_name}': {processed_tokens} tokens, {skipped_tokens} skipped")
                self.nodes[node.name] = node
                processed_nodes += 1
            except Exception as e:
                logging.error(f"Error processing node: {str(e)}")
                skipped_nodes += 1
        
        logging.info(f"Configuration parsing complete: {processed_nodes} nodes processed, {skipped_nodes} nodes skipped")
                
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
                
                # Use consistent token normalization
                normalized_token_id = normalize_token(str(token_id))
                tokens.append({
                    "token_id": normalized_token_id,
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
    def _generate_log_path(self, node_name: str, token_id: str, log_type: str, ip_address: str) -> str:
        """Generates standardized log path with formatted IP"""
        # Format IP address: 192.168.0.11 -> 192-168-0-11
        formatted_ip = ip_address.replace('.', '-')
        
        # Create path: <log_root>/<token_type>/<node_name>/<filename>
        filename = f"{node_name}_{token_id}_{formatted_ip}_{token_id}.{log_type.lower()}"
        return os.path.join(self.log_root, log_type, node_name, filename)
    
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
            # Use consistent token normalization
            normalized_token_id = normalize_token(token_data["token_id"])
            token = NodeToken(
                name=f"{node.name} {normalized_token_id}",
                token_id=normalized_token_id,
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
                    "token_id": token.token_id,  # Already normalized when created
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
        
    def get_tokens_by_type(self, token_type: str) -> List[NodeToken]:
        """Get all tokens of specified type for selected node"""
        if not self.selected_node:
            return []
        return [t for t in self.selected_node.tokens.values()
                if t.token_type == token_type.upper()]
