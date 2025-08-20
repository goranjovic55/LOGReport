#!/usr/bin/env python3
"""
Simple test script to verify FBC token detection improvements.
"""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import required modules directly
from commander.models import Node, NodeToken

class SimpleNodeManager:
    def __init__(self):
        self.nodes = {}
        self.log_root = "test_logs"
        
    def _token_distance(self, token1: str, token2: str) -> int:
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
        return self._levenshtein_distance(token1, token2)
        
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate the Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
            
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
    manager = SimpleNodeManager()
    
    # Test numeric token distances
    print("Testing numeric token distances:")
    print(f"Distance between '162' and '162': {manager._token_distance('162', '162')}")
    print(f"Distance between '162' and '163': {manager._token_distance('162', '163')}")
    print(f"Distance between '162' and '164': {manager._token_distance('162', '164')}")
    print(f"Distance between '163' and '164': {manager._token_distance('163', '164')}")
    
    # Test string token distances
    print("\nTesting string token distances:")
    print(f"Distance between 'abc' and 'abc': {manager._token_distance('abc', 'abc')}")
    print(f"Distance between 'abc' and 'abd': {manager._token_distance('abc', 'abd')}")
    print(f"Distance between 'abc' and 'xyz': {manager._token_distance('abc', 'xyz')}")

if __name__ == "__main__":
    test_token_distance()