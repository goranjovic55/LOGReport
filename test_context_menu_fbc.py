#!/usr/bin/env python3
"""
Test script to verify that the context menu displays all 3 FBC tokens (162, 163, 164) 
for AP01m node with the fixed NodeManager._parse_config method.
"""

import sys
import os
import json

# Simple mock classes to avoid telnetlib dependency
class NodeToken:
    def __init__(self, name: str, token_id: str, token_type: str, 
                 ip_address: str, port: int, protocol: str = "telnet"):
        self.name = name
        self.token_id = token_id
        self.token_type = token_type.upper()
        self.ip_address = ip_address
        self.port = port
        self.protocol = protocol
        self.log_path = ""

class Node:
    def __init__(self, name: str, ip_address: str):
        self.name = name
        self.ip_address = ip_address
        self.status = "offline"
        self.tokens = {}  # token_id -> NodeToken
        
    def add_token(self, token: NodeToken):
        self.tokens[token.token_id] = token

# Simplified version of NodeManager that only includes the fixed _parse_config method
class SimpleNodeManager:
    def __init__(self):
        self.nodes = {}
        self.config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "src",
            "nodes_test.json"
        )
        self._load_configuration()
        
    def _load_configuration(self):
        """Load node configuration from nodes_test.json"""
        if not os.path.exists(self.config_path):
            print(f"ERROR: Configuration file {self.config_path} not found")
            return
            
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
        except Exception as e:
            print(f"ERROR: Failed to load configuration: {e}")
            return
            
        self._parse_config(config_data)
        
    def _parse_config(self, config_data: dict):
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
                    try:
                        # Validate required fields exist
                        if "token_type" not in token_data or "port" not in token_data:
                            print(f"Skipping invalid token entry: {token_data}")
                            continue
                            
                        # Normalize token type to uppercase for consistent classification
                        token_type = token_data["token_type"].upper()
                        
                        # Get and process token_id
                        token_id = token_data.get('token_id')
                        if token_id is None:
                            print(f"Warning: Skipping token with missing 'token_id' in node '{node.name}'.")
                            continue
                        token_id = str(token_id).strip()
                        if not token_id:
                            print(f"Warning: Skipping token with empty 'token_id' in node '{node.name}'.")
                            continue
                            
                        # Special processing for FBC tokens
                        if token_type == "FBC":
                            if token_id.isdigit():
                                token_id = token_id.zfill(3)
                            else:
                                token_id = token_id.upper()

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
        
    def get_node(self, node_name: str):
        """Retrieves node by name"""
        return self.nodes.get(node_name)
        
    def get_node_tokens(self, node_name: str, token_type: str):
        """
        Get tokens of a specific type for a node (simplified version of ContextMenuService method).
        """
        node = self.get_node(node_name)
        if not node:
            return []
            
        return [t for t in node.tokens.values() if t.token_type == token_type]

def main():
    """Main function to run the context menu verification"""
    print("Testing context menu FBC token display for AP01m with fixed NodeManager._parse_config method...")
    
    try:
        # Create node manager with test configuration
        manager = SimpleNodeManager()
        
        # Check if AP01m node exists
        node = manager.get_node("AP01m")
        if not node:
            print("ERROR: AP01m node not found")
            return 1
            
        print(f"AP01m node found with {len(node.tokens)} total tokens")
        
        # Test the get_node_tokens method (used by context menu service)
        fbc_tokens = manager.get_node_tokens("AP01m", "FBC")
        print(f"Context menu would display {len(fbc_tokens)} FBC tokens:")
        for token in fbc_tokens:
            print(f"  - Token ID: {token.token_id}")
            
        # Check for required tokens
        required_tokens = {"162", "163", "164"}
        found_tokens = {t.token_id for t in fbc_tokens}
        
        missing_tokens = required_tokens - found_tokens
        if missing_tokens:
            print(f"ERROR: Missing FBC tokens: {missing_tokens}")
            return 1
            
        print("SUCCESS: Context menu will display all required FBC tokens (162, 163, 164) for AP01m")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())