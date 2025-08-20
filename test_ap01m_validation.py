#!/usr/bin/env python3
"""
Test script to validate FBC token detection for AP01m node
"""
import sys
import os

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.commander.node_manager import NodeManager
from src.commander.models import Node, NodeToken

def test_ap01m_fbc_detection():
    """Test FBC token detection for AP01m node"""
    print("Testing FBC token detection for AP01m node...")
    
    # Initialize NodeManager
    manager = NodeManager()
    
    # Create AP01m node with expected tokens
    node = Node(name="AP01m", ip_address="192.168.1.101")
    
    # Add the three FBC tokens that should be detected
    token_162 = NodeToken(
        name="AP01m 162",
        token_id="162",
        token_type="FBC",
        ip_address="192.168.1.101",
        port=2077
    )
    node.add_token(token_162)
    
    token_163 = NodeToken(
        name="AP01m 163",
        token_id="163",
        token_type="FBC",
        ip_address="192.168.1.101",
        port=2077
    )
    node.add_token(token_163)
    
    token_164 = NodeToken(
        name="AP01m 164",
        token_id="164",
        token_type="FBC",
        ip_address="192.168.1.101",
        port=2077
    )
    node.add_token(token_164)
    
    manager.nodes = {"AP01m": node}
    
    # Scan log files
    manager.scan_log_files()
    
    # Check how many FBC tokens were found
    fbc_tokens = [t for t in node.tokens.values() if t.token_type == "FBC"]
    print(f"Found {len(fbc_tokens)} FBC tokens for node AP01m")
    print(f"Tokens: {[t.token_id for t in fbc_tokens]}")
    
    # Check if all three tokens have log paths
    tokens_with_logs = [t for t in fbc_tokens if t.log_path]
    print(f"Tokens with log paths: {len(tokens_with_logs)}")
    for t in tokens_with_logs:
        print(f"  Token {t.token_id}: {t.log_path}")
    
    # Verify that all three tokens have their log paths updated
    expected_files = [
        os.path.join("test_logs", "AP01m", "162_FBC.log"),
        os.path.join("test_logs", "AP01m", "163_FBC.log"),
        os.path.join("test_logs", "AP01m", "164_FBC.log")
    ]
    
    for token in [token_162, token_163, token_164]:
        if token.log_path:
            print(f"✓ Token {token.token_id} has log path: {token.log_path}")
        else:
            print(f"✗ Token {token.token_id} does not have a log path")
    
    print("\nTest completed!")

if __name__ == "__main__":
    try:
        test_ap01m_fbc_detection()
        sys.exit(0)
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)