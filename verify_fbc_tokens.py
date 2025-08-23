#!/usr/bin/env python3
"""
Simple test script to verify that all FBC tokens (162, 163, 164) are properly loaded
for AP01m node with the fixed NodeManager._parse_config method.
"""

import sys
import os

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Main function to run the verification"""
    print("Testing FBC token loading for AP01m with fixed NodeManager...")
    
    try:
        # Import the actual NodeManager from commander module
        from commander.node_manager import NodeManager
        
        # Create node manager with test configuration
        manager = NodeManager()
        
        # Check if AP01m node exists
        node = manager.get_node("AP01m")
        if not node:
            print("ERROR: AP01m node not found")
            return 1
            
        print(f"AP01m node found with {len(node.tokens)} total tokens")
        
        # Filter FBC tokens
        fbc_tokens = [t for t in node.tokens.values() if t.token_type == "FBC"]
        print(f"Found {len(fbc_tokens)} FBC tokens:")
        for token in fbc_tokens:
            print(f"  - Token ID: {token.token_id}, Path: {token.log_path}")
            
        # Check for required tokens
        required_tokens = {"162", "163", "164"}
        found_tokens = {t.token_id for t in fbc_tokens}
        
        missing_tokens = required_tokens - found_tokens
        if missing_tokens:
            print(f"ERROR: Missing FBC tokens: {missing_tokens}")
            return 1
            
        print("SUCCESS: All required FBC tokens (162, 163, 164) loaded correctly for AP01m")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())