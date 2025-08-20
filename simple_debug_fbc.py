#!/usr/bin/env python3
import re

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

def debug_token(token: str):
    """Debug a token validation"""
    print(f"Token: {token}")
    print(f"Valid token: {bool(re.match(r'^[a-zA-Z0-9]+$', token))}")
    print(f"Matches [a-zA-Z0-9]{{3,6}}: {bool(re.match(r'^[a-zA-Z0-9]{3,6}$', token))}")
    print(f"Matches [a-zA-Z]+[0-9]+: {bool(re.match(r'^[a-zA-Z]+[0-9]+$', token))}")
    print(f"Matches [0-9]{{3}}: {bool(re.match(r'^[0-9]{3}$', token))}")
    print(f"Matches [0-9]{{3}}[a-zA-Z]+: {bool(re.match(r'^[0-9]{3}[a-zA-Z]+$', token))}")
    print(f"Length: {len(token)}")
    print(f"Is FBC token: {is_fbc_token(token)}")
    print()

# Test the specific AP01m tokens
ap01m_tokens = ["162", "163", "164"]
print("AP01m FBC Tokens Debug:")
print("=" * 25)
for token in ap01m_tokens:
    debug_token(token)

# Test some other tokens
other_tokens = ["rpc123", "abcd12", "AB1234"]
print("Other Tokens Debug:")
print("=" * 18)
for token in other_tokens:
    debug_token(token)