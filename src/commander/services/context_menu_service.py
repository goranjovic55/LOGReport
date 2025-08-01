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
        self.presenter = None
        logging.debug("ContextMenuService initialized")
    
    def set_presenter(self, presenter):
        """
        Set the presenter for handling context menu actions.
        
        Args:
            presenter: The presenter to handle context menu actions
        """
        self.presenter = presenter
    
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
                if self.presenter:
                    # Connect action to presenter method
                    if section_type == "FBC":
                        print_action.triggered.connect(
                            lambda: self.presenter.process_all_fbc_subgroup_commands(
                                self._get_current_item_from_data(item_data)
                            )
                        )
                    elif section_type == "RPC":
                        print_action.triggered.connect(
                            lambda: self.presenter.process_all_rpc_subgroup_commands(
                                self._get_current_item_from_data(item_data)
                            )
                        )
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
                        if self.presenter:
                            # Connect action to presenter method
                            action.triggered.connect(
                                lambda: self._handle_fbc_token_action(node_name, token_id)
                            )
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
                        if self.presenter:
                            # Connect actions to presenter methods
                            print_action.triggered.connect(
                                lambda: self._handle_rpc_token_action(node_name, token_id, "print")
                            )
                            clear_action.triggered.connect(
                                lambda: self._handle_rpc_token_action(node_name, token_id, "clear")
                            )
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
    
    def _get_current_item_from_data(self, item_data: Dict[str, Any]):
        """
        Create a mock item from item data for compatibility with existing methods.
        
        Args:
            item_data: Data associated with the tree item
            
        Returns:
            Mock item with parent hierarchy
        """
        # This is a simplified approach - in a real implementation, we would need
        # to properly reconstruct the item hierarchy or modify the presenter methods
        # to accept item data directly
        class MockItem:
            def __init__(self, data):
                self.data = data
                self._parent = None
            
            def parent(self):
                return self._parent
            
            def text(self, column):
                if "node" in self.data:
                    return self.data["node"]
                return ""
        
        # Create mock item hierarchy
        mock_item = MockItem(item_data)
        if "section_type" in item_data:
            # For subgroup items, create parent section and node items
            section_item = MockItem({"node": item_data.get("node")})
            section_item._parent = mock_item
            mock_item._parent = section_item
            
        return mock_item
    
    def _handle_fbc_token_action(self, node_name: str, token_id: str):
        """
        Handle FBC token context menu action.
        
        Args:
            node_name: Name of the node
            token_id: ID of the token
        """
        if self.presenter:
            # Use presenter method instead of window method
            self.presenter.process_fieldbus_command(token_id, node_name)
    
    def _handle_rpc_token_action(self, node_name: str, token_id: str, action_type: str):
        """
        Handle RPC token context menu action.
        
        Args:
            node_name: Name of the node
            token_id: ID of the token
            action_type: Type of action (print, clear)
        """
        if self.presenter:
            # Use presenter method instead of window method
            token_part = token_id.split('_')[-1] if '_' in token_id else token_id
            self.presenter.process_rpc_command(node_name, token_id, action_type)
    
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