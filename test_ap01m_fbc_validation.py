#!/usr/bin/env python3
"""
Test script to verify that all FBC tokens (162, 163, 164) are properly detected 
for AP01m node with the updated nodes_test.json configuration.
"""

import json
import os
import sys
from typing import Dict, List

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class NodeToken:
    def __init__(self, token_id: str, token_type: str, name: str = "default",
                 ip_address: str = "0.0.0.0", port: int = 23, **kwargs):
        self.token_id = token_id
        self.token_type = token_type
        self.name = name
        self.ip_address = ip_address
        self.port = port
        self.log_path = kwargs.get('log_path', "")
        self.protocol = kwargs.get('protocol', "telnet")

class Node:
    def __init__(self, name: str, ip_address: str):
        self.name = name
        self.ip_address = ip_address
        self.status = "offline"
        self.tokens: Dict[str, NodeToken] = {}
        
    def add_token(self, token: NodeToken):
        self.tokens[token.token_id] = token

class NodeManager:
    def __init__(self, config_path: str = "src/nodes_test.json"):
        self.nodes: Dict[str, Node] = {}
        self.log_root = "test_logs"
        self.config_path = config_path
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
            
        # Process each node in the configuration
        for node_data in config_data:
            node = Node(node_data["name"], node_data["ip_address"])
            
            # Add tokens from configuration
            for token_data in node_data.get("tokens", []):
                token = NodeToken(
                    token_id=token_data["token_id"],
                    token_type=token_data["token_type"],
                    name=f"{node.name} {token_data['token_id']}",
                    ip_address=node.ip_address,
                    port=token_data.get("port", 23),
                    protocol=token_data.get("protocol", "telnet")
                )
                node.add_token(token)
                
            self.nodes[node.name] = node
            print(f"Loaded node {node.name} with {len(node.tokens)} pre-configured tokens")
            
    def scan_fbc_files(self):
        """Scan FBC files and verify all expected tokens are detected"""
        print(f"Scanning FBC files in {self.log_root}")
        if not os.path.exists(self.log_root):
            print(f"ERROR: Log root {self.log_root} does not exist")
            return
            
        # Walk through directories to find FBC files
        for dirpath, _, filenames in os.walk(self.log_root):
            fbc_files = [f for f in filenames if f.lower().endswith('.fbc')]
            if not fbc_files:
                continue
                
            print(f"Found {len(fbc_files)} FBC files in {dirpath}")
            
            for filename in fbc_files:
                full_path = os.path.join(dirpath, filename)
                print(f"Processing file: {full_path}")
                
                # Extract node name from directory structure or filename
                node_name = None
                token_id = None
                
                # Check if we're in a nested structure like FBC/AP01m/
                parent_dir = os.path.basename(os.path.dirname(dirpath))
                if parent_dir == "FBC":
                    node_name = os.path.basename(dirpath)
                else:
                    # For files directly in a node directory like test_logs/AP01m/
                    dir_basename = os.path.basename(dirpath)
                    if dir_basename in self.nodes:
                        node_name = dir_basename
                
                # Extract token ID from filename
                if "_" in filename:
                    parts = filename.split("_")
                    # Look for numeric part that's not the node name
                    for part in reversed(parts):
                        if part.isdigit() and part != node_name:
                            token_id = part.zfill(3)  # Normalize to 3-digit format
                            break
                
                if not node_name or not token_id:
                    print(f"Could not extract node name or token ID from {filename}")
                    continue
                    
                # Find matching node
                matched_node = self.nodes.get(node_name)
                if not matched_node:
                    print(f"Node {node_name} not found in configuration")
                    continue
                    
                # Check if token already exists
                existing_token = matched_node.tokens.get(token_id)
                if existing_token and existing_token.token_type == "FBC":
                    # Update existing FBC token path
                    existing_token.log_path = full_path
                    print(f"Updated existing FBC token {token_id} path: {full_path}")
                elif not existing_token or existing_token.token_type != "FBC":
                    # Create new FBC token
                    new_token = NodeToken(
                        token_id=token_id,
                        token_type="FBC",
                        name=f"{node_name} {token_id}",
                        ip_address=matched_node.ip_address,
                        log_path=full_path
                    )
                    matched_node.add_token(new_token)
                    print(f"Added new FBC token {token_id} for node {node_name}")
                    
    def validate_ap01m_fbc_tokens(self) -> bool:
        """Validate that all expected FBC tokens are detected for AP01m"""
        print("\nValidating AP01m FBC tokens...")
        
        node = self.nodes.get("AP01m")
        if not node:
            print("ERROR: AP01m node not found")
            return False
            
        print(f"AP01m node found with {len(node.tokens)} total tokens")
        
        # Filter FBC tokens
        fbc_tokens = [t for t in node.tokens.values() if t.token_type == "FBC"]
        print(f"Found {len(fbc_tokens)} FBC tokens:")
        for token in fbc_tokens:
            print(f"  - Token ID: {token.token_id}, Path: {token.log_path}")
            
        # Check for required tokens
        required_tokens = {"162", "163", "164"}
        found_tokens = {t.token_id for t in fbc_tokens}
        
        missing_tokens = required_tokens - found_tokens
        if missing_tokens:
            print(f"ERROR: Missing FBC tokens: {missing_tokens}")
            return False
            
        print("SUCCESS: All required FBC tokens (162, 163, 164) detected for AP01m")
        return True

def main():
    """Main function to run the validation"""
    print("Testing FBC token detection for AP01m with updated nodes_test.json...")
    
    # Create node manager with updated configuration
    manager = NodeManager("src/nodes_test.json")
    
    # Scan FBC files
    manager.scan_fbc_files()
    
    # Validate AP01m FBC tokens
    success = manager.validate_ap01m_fbc_tokens()
    
    if success:
        print("\nVALIDATION PASSED: All FBC tokens correctly detected")
        return 0
    else:
        print("\nVALIDATION FAILED: Some FBC tokens missing or misconfigured")
        return 1

if __name__ == "__main__":
    sys.exit(main())