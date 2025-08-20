import sys
import os
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from commander.node_manager import NodeManager

def test_node_manager_fixes():
    """Test the fixes for FBC token detection issues"""
    print("Testing NodeManager fixes for FBC token detection...")
    
    # Create a NodeManager instance
    manager = NodeManager()
    
    # Load the test configuration
    test_config_path = os.path.join(os.path.dirname(__file__), 'nodes_test.json')
    if os.path.exists(test_config_path):
        print(f"Loading test configuration from: {test_config_path}")
        manager.set_config_path(test_config_path)
        success = manager.load_configuration()
        print(f"Configuration load result: {success}")
    else:
        print("Test configuration not found, using default configuration")
    
    # Print loaded nodes and tokens
    print("\nLoaded nodes:")
    for node_name, node in manager.nodes.items():
        print(f"  Node: {node_name} (IP: {node.ip_address})")
        for token_id, token in node.tokens.items():
            print(f"    Token: {token_id} (Type: {token.token_type}, Port: {token.port})")
    
    # Test the _extract_token_id_from_filename method
    print("\nTesting _extract_token_id_from_filename method:")
    test_cases = [
        ("AP01m_162_FBC", "FBC"),
        ("AP01m_163_RPC", "RPC"),
        ("162_FBC", "FBC"),
        ("163_RPC", "RPC"),
        ("AP01m_192-168-0-11_162", "FBC"),
        ("AP01m_192.168.0.11_162", "FBC"),
    ]
    
    for base_name, token_type in test_cases:
        token_id = manager._extract_token_id_from_filename(base_name, token_type)
        print(f"  {base_name} -> {token_id}")
    
    # Test scanning log files
    print("\nTesting scan_log_files method:")
    test_logs_path = os.path.join(os.path.dirname(__file__), 'test_logs')
    if os.path.exists(test_logs_path):
        print(f"Scanning log files in: {test_logs_path}")
        manager.set_log_root(test_logs_path)
        manager.scan_log_files()
    else:
        print("Test logs directory not found")
    
    print("\nTest completed.")

if __name__ == "__main__":
    test_node_manager_fixes()