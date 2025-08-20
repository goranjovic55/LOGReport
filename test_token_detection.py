import sys
import os
import logging
from src.commander.node_manager import NodeManager
from src.commander.services.context_menu_service import ContextMenuService
from src.commander.services.context_menu_filter import ContextMenuFilterService

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Initialize components
node_manager = NodeManager()
context_menu_filter = ContextMenuFilterService()
context_menu_service = ContextMenuService(node_manager, context_menu_filter)

# Simulate right-click on AP01m FBC subgroup
item_data = {
    "section_type": "FBC",
    "node": "AP01m"
}

# Get tokens for AP01m FBC subgroup
tokens = context_menu_service.get_node_tokens("AP01m", "FBC")
token_ids = [t.token_id for t in tokens]

print(f"Detected FBC tokens for AP01m: {token_ids}")

# Verify all expected tokens are present
expected_tokens = {'162', '163', '164'}
if set(token_ids) == expected_tokens:
    print("SUCCESS: All tokens detected")
else:
    missing = expected_tokens - set(token_ids)
    print(f"FAILURE: Missing tokens {missing}")
    sys.exit(1)