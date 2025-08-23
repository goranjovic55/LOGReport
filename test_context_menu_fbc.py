#!/usr/bin/env python3
"""
Test script to verify that the context menu displays all 3 FBC tokens (162, 163, 164)
for AP01m node using the real NodeManager implementation with consistent token normalization.
"""

import sys
import os
import json

# Add src to path to import real classes
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from commander.node_manager import NodeManager
from commander.services.context_menu_service import ContextMenuService
from commander.services.context_menu_filter import ContextMenuFilterService

def main():
    """Main function to run the context menu verification"""
    print("Testing context menu FBC token display for AP01m using real NodeManager implementation...")
    
    try:
        # Create real node manager with test configuration
        manager = NodeManager()
        
        # Check if AP01m node exists
        node = manager.get_node("AP01m")
        if not node:
            print("ERROR: AP01m node not found")
            return 1
            
        print(f"AP01m node found with {len(node.tokens)} total tokens")
        
        # Create context menu service with real dependencies
        context_menu_filter = ContextMenuFilterService()
        context_menu_service = ContextMenuService(manager, context_menu_filter)
        
        # Test the get_node_tokens method (used by context menu service)
        fbc_tokens = context_menu_service.get_node_tokens("AP01m", "FBC")
        print(f"Context menu would display {len(fbc_tokens)} FBC tokens:")
        for token in fbc_tokens:
            print(f"  - Token ID: {token.token_id}")
            
        # Check for required tokens
        required_tokens = {"162", "163", "164"}
        found_tokens = {t.token_id for t in fbc_tokens}
        
        missing_tokens = required_tokens - found_tokens
        if missing_tokens:
            print(f"ERROR: Missing FBC tokens: {missing_tokens}")
            return 1
            
        print("SUCCESS: Context menu will display all required FBC tokens (162, 163, 164) for AP01m")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())