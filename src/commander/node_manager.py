"""
Node Manager
Loads and manages node configuration for Commander UI
"""
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class NodeToken:
    name: str
    token_id: str
    token_type: str  # FBC/RPC/LOG/LIS
    ip_address: str
    port: int
    log_path: str = ""
    protocol: str = "telnet"

@dataclass
class Node:
    name: str
    ip_address: str
    status: str = "offline"
    tokens: Dict[str, NodeToken] = field(default_factory=dict)
    
    def add_token(self, token: NodeToken):
        self.tokens[token.token_id] = token

class NodeManager:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.log_root = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "test_logs"
        )
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
            print(f"Loading configuration from: {abs_path}")
            if not os.path.exists(abs_path):
                print(f"Configuration file does not exist: {abs_path}")
                return False
                
            with open(abs_path, 'r', encoding='utf-8') as f:
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
        if isinstance(config_data, list) and all(
            'tokens' in node and 
            isinstance(node['tokens'], list) and 
            all(isinstance(t, str) for t in node['tokens'])
            for node in config_data if 'tokens' in node
        ):
            # Convert old format to new format
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
                for token_data in tokens:
                    try:
                        # Skip tokens missing required fields
                        if "token_id" not in token_data or "token_type" not in token_data or "port" not in token_data:
                            print(f"Skipping invalid token entry: {token_data}")
                            continue
                            
                        token = NodeToken(
                            name=f"{node.name} {token_data['token_id']}",
                            token_id=token_data["token_id"],
                            token_type=token_data["token_type"],
                            ip_address=token_data.get("ip_address", node.ip_address),
                            port=token_data["port"],
                            protocol=token_data.get("protocol", "telnet")
                        )
                        
                        # Generate log path
                        token.log_path = self._generate_log_path(
                            node.name, 
                            token.token_id,
                            token.token_type
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
        """Scans filesystem for existing log files and updates tokens"""
        root = log_root or self.log_root
        if not os.path.exists(root):
            return
            
        # Traverse through all node folders
        for node_name in os.listdir(root):
            node_path = os.path.join(root, node_name)
            if not os.path.isdir(node_path):
                continue
                
            # Find matching node
            node = self.nodes.get(node_name)
            if not node:
                continue
                
            # Scan for log files in node folder
            for filename in os.listdir(node_path):
                if not filename.endswith(".log"):
                    continue
                    
                # Extract token ID and type from filename
                try:
                    # Expected format: {token_id}_{log_type}.log
                    base_name = filename[:-4]  # Remove .log extension
                    token_id, log_type = base_name.split("_", 1)
                except ValueError:
                    continue
                    
                # Update token if exists
                token = node.tokens.get(token_id)
                if token:
                    token.log_path = os.path.join(root, node_name, filename)
            
    def _generate_log_path(self, node_name: str, token_id: str, log_type: str) -> str:
        """Generates standardized log path"""
        return os.path.join(self.log_root, node_name, f"{token_id}_{log_type}.log")
    
    def get_node(self, node_name: str) -> Optional[Node]:
        """Retrieves node by name"""
        return self.nodes.get(node_name)
    
    def get_token(self, node_name: str, token_id: str) -> Optional[NodeToken]:
        """Retrieves token from a node"""
        if node := self.nodes.get(node_name):
            return node.tokens.get(token_id)
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
                token.token_type
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
