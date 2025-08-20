import sys
import os
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock the required imports
import builtins
import unittest.mock as mock

# Mock telnetlib
sys.modules['telnetlib'] = mock.MagicMock()

# Mock PyQt6
sys.modules['PyQt6'] = mock.MagicMock()
sys.modules['PyQt6.QtCore'] = mock.MagicMock()
sys.modules['PyQt6.QtWidgets'] = mock.MagicMock()

# Now we can import the NodeManager
from commander.node_manager import NodeManager

def test_extract_token_id():
    """Test the _extract_token_id_from_filename method"""
    manager = NodeManager()
    
    test_cases = [
        ("AP01m_162_FBC", "FBC", "162"),
        ("AP01m_163_RPC", "RPC", "163"),
        ("162_FBC", "FBC", "162"),
        ("163_RPC", "RPC", "163"),
        ("AP01m_192-168-0-11_162", "FBC", "162"),
        ("AP01m_192.168.0.11_162", "FBC", "162"),
        ("TEST_NODE_192.168.0.1_123", "FBC", "123"),
    ]
    
    print("Testing _extract_token_id_from_filename method:")
    for base_name, token_type, expected in test_cases:
        result = manager._extract_token_id_from_filename(base_name, token_type)
        status = "PASS" if result == expected else "FAIL"
        print(f"  {status}: {base_name} -> {result} (expected: {expected})")

if __name__ == "__main__":
    test_extract_token_id()