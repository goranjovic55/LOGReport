from dataclasses import dataclass, field
from typing import Dict


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

