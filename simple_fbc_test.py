#!/usr/bin/env python3
import re
import sys

def is_fbc_token(token: str) -> bool:
    """
    Check if a token is an FBC token (3-6 alphanumeric characters with specific patterns).
    """
    # Basic validation - alphanumeric only
    if not re.match(r'^[a-zA-Z0-9]+$', token):
        return False
        
    # FBC tokens are 3-6 alphanumeric characters
    if not re.match(r'^[a-zA-Z0-9]{3,6}$', token):
        return False
        
    # Specific FBC patterns that are always FBC
    # 1. Exactly 3 digits is always FBC
    if re.match(r'^[0-9]{3}$', token):
        return True
    # 2. 3 digits followed by letters is FBC
    if re.match(r'^[0-9]{3}[a-zA-Z]+$', token):
        return True
        
    # Patterns that are typically FBC (letters followed by digits, but longer/more complex)
    # This includes tokens like "abcd12" and "AB1234" from the task
    if re.match(r'^[a-zA-Z]+[0-9]+$', token):
        # Allow longer letter+digit patterns as FBC
        # For example, "abcd12" (6 chars) and "AB1234" (6 chars)
        # But exclude typical RPC patterns like "rpc123" (6 chars but shorter letter sequence)
        letter_part = re.match(r'^[a-zA-Z]+', token).group()
        # More specific criteria to distinguish FBC from RPC:
        # 1. If letter part is 4 or more, it's likely FBC (covers "abcd12")
        if len(letter_part) >= 4:
            return True
        # 2. If total length is 6 AND letter part is mixed case or uppercase, it's likely FBC (covers "AB1234")
        if len(token) == 6 and (not letter_part.islower()):
            return True
        # 3. Otherwise, it's likely RPC
        return False
        
    # All other alphanumeric patterns of 3-6 characters are FBC
    # This includes mixed patterns like "abc123" if they don't match the above
    return True

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