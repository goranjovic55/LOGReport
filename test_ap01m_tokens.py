#!/usr/bin/env python3
"""
Test script to verify that AP01m tokens (162, 163, 164) work with the updated FBC token validation regex.
"""

import sys
import os

# Add the src directory to the path so we can import the token utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from commander.utils.token_utils import is_fbc_token

def test_ap01m_tokens():
    """Test that AP01m tokens are correctly identified as FBC tokens."""
    # Test the specific AP01m tokens mentioned in the task
    ap01m_tokens = ["162", "163", "164"]
    
    print("Testing AP01m tokens with updated FBC validation regex:")
    all_passed = True
    
    for token in ap01m_tokens:
        result = is_fbc_token(token)
        status = "PASS" if result else "FAIL"
        print(f"  Token '{token}': {status}")
        if not result:
            all_passed = False
    
    # Test some additional valid tokens with the new pattern
    print("\nTesting additional valid tokens with new pattern:")
    valid_tokens = ["abc", "XYZ", "1234", "abcd12", "AB1234"]
    
    for token in valid_tokens:
        result = is_fbc_token(token)
        status = "PASS" if result else "FAIL"
        print(f"  Token '{token}': {status}")
        if not result:
            all_passed = False
    
    # Test some invalid tokens
    print("\nTesting invalid tokens with new pattern:")
    invalid_tokens = ["12", "1234567", "!@#", "abc-123"]
    
    for token in invalid_tokens:
        result = is_fbc_token(token)
        status = "PASS" if not result else "FAIL"
        print(f"  Token '{token}': {status}")
        if result:
            all_passed = False
    
    print(f"\nOverall result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    return all_passed

if __name__ == "__main__":
    success = test_ap01m_tokens()
    sys.exit(0 if success else 1)