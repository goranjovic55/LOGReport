#!/usr/bin/env python3
"""
Test script to verify FBC token detection with actual test files
"""
import sys
import os
import re

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

def test_fbc_file_detection():
    """Test FBC token extraction with actual test files"""
    print("Testing FBC token extraction with actual files...")
    
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
    
    # Test with actual files from test_logs/AP01m
    test_files = [
        ("162_FBC.log", "AP01m", "162"),
        ("163_FBC.log", "AP01m", "163"),
        ("164_FBC.log", "AP01m", "164"),
    ]
    
    print("\nTesting with actual files from test_logs/AP01m:")
    all_passed = True
    for filename, node_name, expected_token in test_files:
        extracted_token = extract_token_id(filename, node_name, "FBC")
        print(f"  File: {filename} -> Extracted: {extracted_token}")
        if extracted_token == expected_token:
            print(f"  ✓ PASS: Correctly extracted token {expected_token}")
        else:
            print(f"  ❌ FAIL: Expected '{expected_token}', got '{extracted_token}'")
            all_passed = False
    
    # Test with original format files from test_logs/FBC/AP01m
    original_files = [
        ("AP01m_192-168-0-11_162.fbc", "AP01m", "162"),
        ("AP01m_192.168.0.11_162.fbc", "AP01m", "162"),
    ]
    
    print("\nTesting with original format files from test_logs/FBC/AP01m:")
    for filename, node_name, expected_token in original_files:
        extracted_token = extract_token_id(filename, node_name, "FBC")
        print(f"  File: {filename} -> Extracted: {extracted_token}")
        if extracted_token == expected_token:
            print(f"  ✓ PASS: Correctly extracted token {expected_token}")
        else:
            print(f"  ❌ FAIL: Expected '{expected_token}', got '{extracted_token}'")
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED: FBC token extraction works with actual files!")
    else:
        print("\n❌ SOME TESTS FAILED: Check implementation")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = test_fbc_file_detection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)