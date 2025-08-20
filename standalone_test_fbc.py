#!/usr/bin/env python3
"""
Standalone test script to verify FBC token detection improvements.
"""

def token_distance(token1: str, token2: str) -> int:
    """Calculates similarity distance between two token IDs"""
    # Normalize tokens to lowercase for case-insensitive comparison
    token1 = token1.lower()
    token2 = token2.lower()
    
    # If tokens are exactly the same, distance is 0
    if token1 == token2:
        return 0
        
    # If one token is a prefix of the other, distance is 1
    if token1.startswith(token2) or token2.startswith(token1):
        return 1
        
    # For numeric tokens, calculate numeric difference if both are numeric
    if token1.isdigit() and token2.isdigit():
        try:
            diff = abs(int(token1) - int(token2))
            # Return a distance based on the difference, capped at 10
            return min(diff, 10)
        except ValueError:
            pass  # Fall back to string comparison if conversion fails
            
    # For general string comparison, use Levenshtein distance
    return levenshtein_distance(token1, token2)
    
def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein distance between two strings"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
        
    if len(s2) == 0:
        return len(s1)
        
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
        
    return previous_row[-1]

def test_token_distance():
    """Test the improved token distance calculation."""
    print("Testing numeric token distances:")
    print(f"Distance between '162' and '162': {token_distance('162', '162')}")
    print(f"Distance between '162' and '163': {token_distance('162', '163')}")
    print(f"Distance between '162' and '164': {token_distance('162', '164')}")
    print(f"Distance between '163' and '164': {token_distance('163', '164')}")
    
    # Test string token distances
    print("\nTesting string token distances:")
    print(f"Distance between 'abc' and 'abc': {token_distance('abc', 'abc')}")
    print(f"Distance between 'abc' and 'abd': {token_distance('abc', 'abd')}")
    print(f"Distance between 'abc' and 'xyz': {token_distance('abc', 'xyz')}")

def normalize_fbc_token_id(token_id: str) -> str:
    """Normalize FBC token ID by padding numeric IDs to 3 digits."""
    if token_id.isdigit():
        return token_id.zfill(3)
    return token_id.upper()

def test_token_normalization():
    """Test FBC token ID normalization."""
    print("\nTesting FBC token ID normalization:")
    test_tokens = ["162", "163", "164", "abc", "XYZ", "12", "1234"]
    for token in test_tokens:
        normalized = normalize_fbc_token_id(token)
        print(f"Token '{token}' normalized to '{normalized}'")

if __name__ == "__main__":
    test_token_distance()
    test_token_normalization()