#!/usr/bin/env python3
"""
Simple test script to verify the nodes_test.json configuration
"""

import json
import sys
import os

def test_nodes_config():
    """Test that nodes_test.json has the correct configuration for AP01m"""
    config_path = "src/nodes_test.json"
    
    if not os.path.exists(config_path):
        print(f"ERROR: Configuration file {config_path} not found")
        return False
        
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        return False
        
    # Find AP01m node
    ap01m_node = None
    for node in config_data:
        if node.get("name") == "AP01m":
            ap01m_node = node
            break
            
    if not ap01m_node:
        print("ERROR: AP01m node not found in configuration")
        return False
        
    print(f"AP01m node found with IP: {ap01m_node.get('ip_address')}")
    
    # Check IP address
    if ap01m_node.get("ip_address") != "192.168.0.11":
        print("ERROR: Incorrect IP address for AP01m")
        return False
        
    # Check tokens
    tokens = ap01m_node.get("tokens", [])
    print(f"Found {len(tokens)} tokens")
    
    # Expected tokens
    expected_tokens = {
        "162": "FBC",
        "163": "FBC", 
        "164": "FBC"
    }
    
    # Check that we have the right number of tokens
    if len(tokens) != len(expected_tokens):
        print(f"ERROR: Expected {len(expected_tokens)} tokens, found {len(tokens)}")
        return False
        
    # Check each token
    found_tokens = {}
    for token in tokens:
        token_id = token.get("token_id")
        token_type = token.get("token_type")
        found_tokens[token_id] = token_type
        print(f"  Token {token_id}: {token_type}")
        
    # Verify all expected tokens are present with correct types
    for token_id, expected_type in expected_tokens.items():
        if token_id not in found_tokens:
            print(f"ERROR: Missing token {token_id}")
            return False
        if found_tokens[token_id] != expected_type:
            print(f"ERROR: Token {token_id} has type {found_tokens[token_id]}, expected {expected_type}")
            return False
            
    print("SUCCESS: All tokens present with correct types")
    return True

if __name__ == "__main__":
    success = test_nodes_config()
    sys.exit(0 if success else 1)