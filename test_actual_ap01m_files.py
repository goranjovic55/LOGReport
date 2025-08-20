import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.commander.node_manager import NodeManager
from src.commander.models import Node, NodeToken

def test_actual_ap01m_files():
    """Test NodeManager with actual files in test_logs/AP01m directory"""
    print("=== Testing NodeManager with actual AP01m files ===")
    
    # Initialize NodeManager
    manager = NodeManager()
    
    # Set log root to the test_logs directory
    manager.set_log_root("test_logs")
    
    # Get the AP01m node
    ap01m_node = manager.get_node("AP01m")
    
    if ap01m_node is None:
        print("❌ AP01m node not found")
        return False
    
    print(f"Found AP01m node with IP: {ap01m_node.ip_address}")
    print(f"AP01m has {len(ap01m_node.tokens)} tokens")
    
    # Check for specific tokens
    token_162 = ap01m_node.tokens.get("162")
    token_163 = ap01m_node.tokens.get("163")
    token_164 = ap01m_node.tokens.get("164")
    
    print(f"\nToken 162: {token_162}")
    print(f"Token 163: {token_163}")
    print(f"Token 164: {token_164}")
    
    # Check if tokens have log paths
    success = True
    
    if token_162 and token_162.log_path:
        print(f"✓ Token 162 log path: {token_162.log_path}")
    else:
        print("✗ Token 162 log path not found")
        success = False
        
    if token_163 and token_163.log_path:
        print(f"✓ Token 163 log path: {token_163.log_path}")
    else:
        print("✗ Token 163 log path not found")
        success = False
        
    if token_164 and token_164.log_path:
        print(f"✓ Token 164 log path: {token_164.log_path}")
    else:
        print("✗ Token 164 log path not found")
        success = False
    
    # Scan log files to update paths
    print("\nScanning log files...")
    manager.scan_log_files()
    
    # Check updated paths
    ap01m_node = manager.get_node("AP01m")
    if ap01m_node:
        token_162 = ap01m_node.tokens.get("162")
        token_163 = ap01m_node.tokens.get("163")
        token_164 = ap01m_node.tokens.get("164")
        
        print(f"\nAfter scanning:")
        if token_162 and token_162.log_path:
            print(f"✓ Token 162 log path: {token_162.log_path}")
        if token_163 and token_163.log_path:
            print(f"✓ Token 163 log path: {token_163.log_path}")
        if token_164 and token_164.log_path:
            print(f"✓ Token 164 log path: {token_164.log_path}")
    
    if success:
        print("\n🎉 Test passed! All AP01m tokens have log paths.")
    else:
        print("\n❌ Test failed! Some tokens are missing log paths.")
        
    return success

if __name__ == "__main__":
    test_actual_ap01m_files()