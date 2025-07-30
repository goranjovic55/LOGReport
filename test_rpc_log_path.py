import os
import unittest
from src.commander.node_manager import NodeManager

class TestRPCLogPath(unittest.TestCase):
    def test_rpc_log_path_generation(self):
        node_manager = NodeManager()
        node_manager.log_root = "test_logs"
        
        # Test with sample data
        node_name = "AP01m"
        token_id = "162"
        ip_address = "192.168.0.11"
        log_type = "RPC"
        
        path = node_manager._generate_log_path(node_name, token_id, log_type, ip_address)
        
        # Verify directory structure
        self.assertIn(f"RPC{os.sep}{node_name}", path)
        
        # Verify filename format
        self.assertIn(f"{node_name}_{token_id}_192-168-0-11_{token_id}.rpc", path)
        
        print("Test passed: RPC log path generation is correct")

if __name__ == "__main__":
    unittest.main()