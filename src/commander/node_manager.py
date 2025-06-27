"""
Node Manager
Loads and manages node configuration for Commander UI
"""
import os
from typing import Dict, List, Optional
from .models import Node, NodeToken
from .node_config import NodeConfigMixin
from .node_log import NodeLogMixin

class NodeManager(NodeConfigMixin, NodeLogMixin):
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
    
