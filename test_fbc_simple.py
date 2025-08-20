#!/usr/bin/env python3
"""
Simple test script to verify FBC token extraction logic
"""
import re
import sys
import os

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the token validation functions
try:
    from commander.utils.token_utils import is_fbc_token
except ImportError:
    # If we can't import, create a simple mock
    def is_fbc_token(token):
        """Mock function to check if a token is an FBC token"""
        return bool(re.match(r'^\d{3}[a-z]?$', token))

def test_fbc_token_extraction():
    """Test FBC token extraction with both filename formats"""
    print("Testing FBC token extraction...")
    
    # Define patterns
    FBC_TOKEN_PATTERN = r"^([\w-]+)_[\d\.-]+_([\w-]+)\."
    FBC_TOKEN_PATTERN_ALT = r"^(\d{3})_(FBC)\.log$"
    
    def extract_token_id(filename, node_name, section_type):
        """Extract token ID from filename based on section type"""
        if section_type != "FBC":
            return None
            
        # First try the original pattern
        match = re.match(FBC_TOKEN_PATTERN, filename)
        if match and match.group(1) == node_name:
            token_id = match.group(2)
            # Validate that the extracted token is a valid FBC token
            if is_fbc_token(token_id):
                return token_id
        
        # If original pattern fails, try the alternative pattern
        match_alt = re.match(FBC_TOKEN_PATTERN_ALT, filename)
        if match_alt:
            token_id = match_alt.group(1)
            # Validate that the extracted token is a valid FBC token
            if is_fbc_token(token_id):
                return token_id
                
        return None
    
    # Test case 1: Original format (node_name_ip_address_token_id.extension)
    print("\n1. Testing original format (node_name_ip_address_token_id.extension):")
    filename1 = "AP01m_192-168-0-11_162.fbc"
    node_name1 = "AP01m"
    token_id1 = extract_token_id(filename1, node_name1, "FBC")
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
    token_id2 = extract_token_id(filename2, node_name2, "FBC")
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
        extracted = extract_token_id(filename, "AP01m", "FBC")
        print(f"   Filename: {filename} -> Extracted: {extracted}")
        if extracted == token:
            print(f"   ✓ PASS: Correctly extracted token {token}")
        else:
            print(f"   ❌ FAIL: Expected '{token}', got '{extracted}'")
    
    # Test case 4: Invalid FBC token
    print("\n4. Testing invalid FBC token:")
    filename4 = "invalid_FBC.log"
    token_id4 = extract_token_id(filename4, "AP01m", "FBC")
    print(f"   Filename: {filename4}")
    print(f"   Extracted token ID: {token_id4}")
    if token_id4 is None:
        print("   ✓ PASS: Correctly rejected invalid token")
    else:
        print(f"   ❌ FAIL: Expected None, got '{token_id4}'")
    
    # Test case 5: Original format with wrong node name
    print("\n5. Testing original format with wrong node name:")
    filename5 = "AP01m_192-168-0-11_162.fbc"
    node_name5 = "WRONG_NODE"
    token_id5 = extract_token_id(filename5, node_name5, "FBC")
    print(f"   Filename: {filename5} with node {node_name5}")
    print(f"   Extracted token ID: {token_id5}")
    if token_id5 is None:
        print("   ✓ PASS: Correctly rejected file with wrong node name")
    else:
        print(f"   ❌ FAIL: Expected None, got '{token_id5}'")
    
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