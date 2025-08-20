import sys
import os
import json
import re
from typing import Dict, List, Optional

# Mock the required imports
import unittest.mock as mock

# Mock telnetlib
sys.modules['telnetlib'] = mock.MagicMock()

# Mock PyQt6
sys.modules['PyQt6'] = mock.MagicMock()
sys.modules['PyQt6.QtCore'] = mock.MagicMock()
sys.modules['PyQt6.QtWidgets'] = mock.MagicMock()
sys.modules['PyQt6.QtGui'] = mock.MagicMock()

# Define a simple NodeToken class for testing
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

# Define a simple Node class for testing
class Node:
    def __init__(self, name: str, ip_address: str = "0.0.0.0"):
        self.name = name
        self.ip_address = ip_address
        self.tokens: Dict[str, NodeToken] = {}
        self.status = "disconnected"
        
    def add_token(self, token: NodeToken):
        self.tokens[token.token_id] = token

# Now let's implement the _extract_token_id_from_filename method directly
def _extract_token_id_from_filename(base_name: str, token_type: str) -> str:
    """
    Extract token ID from filename using improved parsing for various naming conventions.
    Handles patterns like:
    - AP01m_162_FBC
    - AP01m_163_RPC
    - 162_FBC
    - 163_RPC
    - AP01m_192-168-0-11_162
    - TEST_NODE_192.168.0.1_123
    """
    parts = base_name.split('_')
    if not parts:
        return ""
        
    # If the last part is a token type, use the part before it as token ID
    if len(parts) >= 2 and parts[-1].upper() in ["FBC", "RPC", "LOG", "LIS", "VNC", "FTP"]:
        return parts[-2]
        
    # If we have multiple parts, try to identify the token ID
    # Look for numeric/alphanumeric part that could be token ID
    # Usually it's the last part or second to last part
    if len(parts) >= 2:
        # Check if the last part is a number (likely the token ID)
        if parts[-1].isdigit():
            return parts[-1]
        # Check if the second to last part is a number (likely the token ID)
        elif len(parts) >= 3 and parts[-2].isdigit():
            return parts[-2]
        # For alphanumeric tokens, check the last part
        elif parts[-1].isalnum() and not parts[-1].isdigit():
            # Additional check to avoid IP-like parts
            if '.' not in parts[-1] and '-' not in parts[-1]:
                return parts[-1]
                
    # If we have at least one part, use the last one as token ID
    return parts[-1] if parts else ""

def test_extract_token_id():
    """Test the _extract_token_id_from_filename method"""
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
        result = _extract_token_id_from_filename(base_name, token_type)
        status = "PASS" if result == expected else "FAIL"
        print(f"  {status}: {base_name} -> {result} (expected: {expected})")

if __name__ == "__main__":
    test_extract_token_id()