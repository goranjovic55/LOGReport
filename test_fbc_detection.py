#!/usr/bin/env python3
"""
Test script to verify FBC token detection for both filename formats
"""
import sys
import os

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from commander.presenters.node_tree_presenter import NodeTreePresenter
from commander.models import Node

def test_fbc_token_extraction():
    """Test FBC token extraction with both filename formats"""
    print("Testing FBC token extraction...")
    
    # Create a mock NodeTreePresenter (we won't actually use its functionality)
    presenter = NodeTreePresenter.__new__(NodeTreePresenter)
    
    # Test case 1: Original format (node_name_ip_address_token_id.extension)
    print("\n1. Testing original format (node_name_ip_address_token_id.extension):")
    filename1 = "AP01m_192-168-0-11_162.fbc"
    node_name1 = "AP01m"
    token_id1 = presenter._extract_token_id(filename1, node_name1, "FBC")
    print(f"   Filename: {filename1}")
    print(f"   Extracted token ID: {token_id1}")
    if token_id1 == "162":
        print("   ✓ PASS: Correctly extracted token ID from original format")
    else:
        print(f"   ❌ FAIL: Expected '162', got '{token_id1}'")
    
    # Test case 2: New format (token_id_token_type.log)
    print("\n2. Testing new format (token_id_token_type.log):")
    filename2 = "162_FBC.log"
    node_name2 = "AP01m"  # Node name doesn't matter for this format
    token_id2 = presenter._extract_token_id(filename2, node_name2, "FBC")
    print(f"   Filename: {filename2}")
    print(f"   Extracted token ID: {token_id2}")
    if token_id2 == "162":
        print("   ✓ PASS: Correctly extracted token ID from new format")
    else:
        print(f"   ❌ FAIL: Expected '162', got '{token_id2}'")
    
    # Test case 3: Other FBC tokens (163, 164)
    print("\n3. Testing other FBC tokens:")
    for token in ["163", "164"]:
        filename = f"{token}_FBC.log"
        extracted = presenter._extract_token_id(filename, "AP01m", "FBC")
        print(f"   Filename: {filename} -> Extracted: {extracted}")
        if extracted == token:
            print(f"   ✓ PASS: Correctly extracted token {token}")
        else:
            print(f"   ❌ FAIL: Expected '{token}', got '{extracted}'")
    
    # Test case 4: Invalid FBC token
    print("\n4. Testing invalid FBC token:")
    filename4 = "invalid_FBC.log"
    token_id4 = presenter._extract_token_id(filename4, "AP01m", "FBC")
    print(f"   Filename: {filename4}")
    print(f"   Extracted token ID: {token_id4}")
    if token_id4 is None:
        print("   ✓ PASS: Correctly rejected invalid token")
    else:
        print(f"   ❌ FAIL: Expected None, got '{token_id4}'")
    
    print("\n🎉 FBC token extraction test completed!")

if __name__ == "__main__":
    try:
        test_fbc_token_extraction()
        sys.exit(0)
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)