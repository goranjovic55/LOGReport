import os
import sys
import logging

# Add parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.commander.node_manager import NodeManager

# Configure logging to see debug output
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

def test_alphanumeric_token_matching():
    # Create NodeManager
    manager = NodeManager()
    
    # Set log root to the test_logs directory in the project
    test_logs_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "test_logs"
    )
    manager.set_log_root(test_logs_path)
    
    # Create a test node AP03m with token 1A2 (FBC)
    node_data = {
        "name": "AP03m",
        "ip_address": "192.168.0.13",
        "tokens": [
            {
                "token_id": "1A2",
                "token_type": "FBC",
                "port": 23,
                "protocol": "telnet"
            }
        ]
    }
    manager.add_node(node_data)
    
    # Now scan the log files
    manager.scan_log_files()
    
    # Verify FBC token was found with correct alphanumeric ID
    node = manager.get_node("AP03m")
    assert node is not None
    assert "1A2" in node.tokens
    token = node.tokens["1A2"]
    assert token.token_type == "FBC"
    print("Test passed: FBC token with alphanumeric ID found for AP03m")

if __name__ == '__main__':
    test_alphanumeric_token_matching()