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
    DEFAULT_CONFIG_PATH = "src/nodes.json"
    
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        
    def load_configuration(self, file_path: str = DEFAULT_CONFIG_PATH) -> bool:
        """Loads node configuration from JSON file"""
        if not os.path.exists(file_path):
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                self._parse_config(config_data)
            return True
        except (json.JSONDecodeError, KeyError):
            return False
            
    def _parse_config(self, config_data: dict):
        """Parses raw configuration into Node objects"""
        for node_data in config_data:
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
                
                # Generate log path
                token.log_path = self._generate_log_path(
                    node.name, 
                    token.token_id,
                    token.token_type
                )
                
                node.add_token(token)
                
            self.nodes[node.name] = node
            
    def _generate_log_path(self, node_name: str, token: str, log_type: str) -> str:
        """Generates standardized log path"""
        return os.path.join("test_logs", node_name, f"{token}_{log_type}.log")
    
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
    
    def save_configuration(self, file_path: str = DEFAULT_CONFIG_PATH) -> bool:
        """Saves current configuration to JSON file"""
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
