"""
Context Menu Service - Handles context menu operations and actions
"""
import logging
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction

from .context_menu_filter import ContextMenuFilterService
from ..models import NodeToken
from ..node_manager import NodeManager


class ContextMenuService:
    """Service for handling context menu operations and actions"""
    
    def __init__(self, node_manager: NodeManager, context_menu_filter: ContextMenuFilterService):
        """
        Initialize the context menu service.
        
        Args:
            node_manager: Manager for node operations
            context_menu_filter: Service for filtering context menu items
        """
        self.node_manager = node_manager
        self.context_menu_filter = context_menu_filter
        logging.debug("ContextMenuService initialized")
    
    def show_context_menu(self, menu: QMenu, item_data: Dict[str, Any], position) -> bool:
        """
        Show context menu for a tree item.
        
        Args:
            menu: The menu to populate and show
            item_data: Data associated with the tree item
            position: Position to show the menu
            
        Returns:
            True if menu was shown, False otherwise
        """
        added_actions = False
        logging.debug(f"Context menu processing item data: {item_data}")
        
        # Handle section items (FBC/RPC subgroups)
        if item_data and isinstance(item_data, dict) and 'section_type' in item_data:
            section_type = item_data.get("section_type")
            node_name = item_data.get("node")
            
            if section_type in ["FBC", "RPC"] and node_name:
                # Use context menu filter service to determine visibility
                if not self.context_menu_filter.should_show_command(
                    node_name=node_name,
                    section_type=section_type,
                    command_type="all",
                    command_category="subgroup"
                ):
                    logging.debug(f"Context menu filtered out for {section_type} subgroup of {node_name}")
                    return False
                
                logging.debug(f"Context menu processing {section_type} subgroup for node {node_name}")
                
                # Create action for printing all tokens (simplified to only this command)
                print_action = QAction(f"Print All {section_type} Tokens for {node_name}", menu)
                menu.addAction(print_action)
                added_actions = True
        
        # Handle token items (individual token files)
        elif item_data and isinstance(item_data, dict) and 'token' in item_data:
            token_type = item_data.get("token_type", "UNKNOWN").upper()
            token_id = item_data.get("token")
            node_name = item_data.get("node", "Unknown")
            
            if token_id:
                logging.debug(f"Context menu processing token item: type={token_type}, id={token_id}, node={node_name}")
                
                if token_type == "FBC":
                    # Check if FBC token commands should be shown
                    if not self.context_menu_filter.should_show_command(
                        node_name=node_name,
                        section_type=token_type,
                        command_type="all",
                        command_category="token"
                    ):
                        logging.debug(f"Context menu filtered out FBC token command for {token_id}")
                    else:
                        token_str = str(token_id)
                        action = QAction(f"Print FieldBus Structure (Token {token_str})", menu)
                        menu.addAction(action)
                        added_actions = True
                    
                elif token_type == "RPC":
                    # Check if RPC token commands should be shown
                    if not self.context_menu_filter.should_show_command(
                        node_name=node_name,
                        section_type=token_type,
                        command_type="all",
                        command_category="token"
                    ):
                        logging.debug(f"Context menu filtered out RPC token command for {token_id}")
                    else:
                        display_token = token_id.split('_')[-1] if '_' in token_id else token_id
                        print_action = QAction(f"Print Rupi counters Token '{display_token}'", menu)
                        clear_action = QAction(f"Clear Rupi counters '{display_token}'", menu)
                        menu.addAction(print_action)
                        menu.addAction(clear_action)
                        added_actions = True
        
        if added_actions:
            # Show menu at cursor position
            menu.exec(position)
            logging.debug(f"Context menu displayed with {len(menu.actions())} actions")
        else:
            logging.debug("Context menu - no applicable actions for this item")
            
        return added_actions
    
    def get_node_tokens(self, node_name: str, token_type: str) -> List[NodeToken]:
        """
        Get tokens of a specific type for a node.
        
        Args:
            node_name: Name of the node
            token_type: Type of tokens to retrieve (FBC, RPC, etc.)
            
        Returns:
            List of tokens of the specified type
        """
        node = self.node_manager.get_node(node_name)
        if not node:
            return []
            
        return [t for t in node.tokens.values() if t.token_type == token_type]
    
    def validate_node_structure(self, item_data: Dict[str, Any]) -> Optional[str]:
        """
        Validate node structure before processing context menu actions.
        
        Args:
            item_data: Data associated with the tree item
            
        Returns:
            Node name if valid, None otherwise
        """
        if not item_data or "node" not in item_data:
            logging.error("Invalid node structure in context menu data")
            return None
            
        return item_data["node"]