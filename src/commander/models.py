from dataclasses import dataclass, field
from typing import Dict


@dataclass
class NodeToken:
    token_id: str
    token_type: str  # FBC/RPC/LOG/LIS
    name: str = "default"
    ip_address: str = "0.0.0.0"
    port: int = 23
    log_path: str = ""
    protocol: str = "telnet"
    
    def __init__(self, token_id: str, token_type: str, name: str = "default",
                 ip_address: str = "0.0.0.0", port: int = 23, **kwargs):
        self.token_id = token_id
        self.token_type = token_type
        self.name = name
        self.ip_address = ip_address
        self.port = port
        self.log_path = kwargs.get('log_path', "")
        self.protocol = kwargs.get('protocol', "telnet")


@dataclass
class Node:
    name: str
    ip_address: str
    status: str = "offline"
    tokens: Dict[str, NodeToken] = field(default_factory=dict)

    def add_token(self, token: NodeToken):
        self.tokens[token.token_id] = token

