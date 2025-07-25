"""
Service for handling context menu operations in the Commander application.
"""
import logging
from typing import Dict, List, Optional
from PyQt6.QtWidgets import QTreeWidgetItem, QMenu
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

from ..models import NodeToken
from ..node_manager import NodeManager
from ..session_manager import SessionManager
from ..command_queue import CommandQueue
from ..services.fbc_command_service import FbcCommandService
from ..services.rpc_command_service import RpcCommandService
from ..services.context_menu_filter import ContextMenuFilterService


class ContextMenuService:
    """Service for handling context menu operations and command execution."""
    
    def __init__(self, node_manager: NodeManager, session_manager: SessionManager,
                 command_queue: CommandQueue, fbc_service: FbcCommandService,
                 rpc_service: RpcCommandService, context_menu_filter: ContextMenuFilterService):
        """
        Initialize the ContextMenuService.
        
        Args:
            node_manager: Manager for node operations
            session_manager: Manager for session operations
            command_queue: Queue for command execution
            fbc_service: Service for FBC command operations
            rpc_service: Service for RPC command operations
            context_menu_filter: Service for filtering context menu items
        """
        self.node_manager = node_manager
        self.session_manager = session_manager
        self.command_queue = command_queue
        self.fbc_service = fbc_service
        self.rpc_service = rpc_service
        self.context_menu_filter = context_menu_filter
        
        logging.debug("ContextMenuService initialized")
    
    def create_context_menu(self, item: QTreeWidgetItem, position) -> Optional[QMenu]:
        """
        Create context menu for node tree items with detailed logging.
        
        Args:
            item: The tree item for which to create the context menu
            position: The position where the menu should be shown
            
        Returns:
            QMenu object or None if no menu should be shown
        """
        logging.debug("Context menu received create_context_menu request")
        logging.debug(f"Context menu shown at position: {position}")
        
        if not item:
            logging.debug("Context menu - no item at position")
            return None
            
        data = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu()
        added_actions = False
        logging.debug(f"DEBUG: Context menu item data: {data}")

        # Handle section items (FBC/RPC subgroups)
        if data and isinstance(data, dict) and 'section_type' in data:
            section_type = data.get("section_type")
            node_name = data.get("node")
            
            if section_type in ["FBC", "RPC"] and node_name:
                # Use context menu filter service to determine visibility
                if not self.context_menu_filter.should_show_command(
                    node_name=node_name,
                    section_type=section_type,
                    command_type="all",
                    command_category="subgroup"
                ):
                    logging.debug(f"Context menu filtered out for {section_type} subgroup of {node_name}")
                    return None
                
                logging.debug(f"Context menu processing {section_type} subgroup for node {node_name}")
                
                # Create actions for printing and executing all tokens
                print_action = QAction(f"Print All {section_type} Tokens for {node_name}")
                execute_action = QAction(f"Execute All {section_type} Commands")
                
                # Connect actions to appropriate handlers (will be connected by caller)
                print_action.setProperty("action_type", "print_all")
                print_action.setProperty("item", item)
                execute_action.setProperty("action_type", "execute_all")
                execute_action.setProperty("item", item)
                
                menu.addAction(print_action)
                menu.addAction(execute_action)
                
                # Add submenu for individual tokens
                tokens_submenu = QMenu(f"{section_type} Token Actions")
                
                # Print submenu
                print_submenu = QMenu("Print Tokens")
                added_print = False
                
                # Execute submenu
                execute_submenu = QMenu("Execute Commands")
                added_execute = False
                
                node = self.node_manager.get_node(node_name)
                if node:
                    for token in node.tokens.values():
                        if token.token_type == section_type:
                            token_id = token.token_id
                            
                            # Check if token commands should be shown
                            if not self.context_menu_filter.should_show_command(
                                node_name=node_name,
                                section_type=section_type,
                                command_type="all",
                                command_category="token"
                            ):
                                logging.debug(f"Context menu filtered out {section_type} token command for {token_id}")
                                continue
                            
                            # Print action
                            print_token_action = QAction(f"Print Token {token_id}")
                            print_token_action.setProperty("action_type", "print_token")
                            print_token_action.setProperty("token_id", token_id)
                            print_token_action.setProperty("node_name", node_name)
                            print_token_action.setProperty("section_type", section_type)
                            print_submenu.addAction(print_token_action)
                            added_print = True
                            
                            # Execute action
                            execute_token_action = QAction(f"Execute Token {token_id}")
                            execute_token_action.setProperty("action_type", "execute_token")
                            execute_token_action.setProperty("token_id", token_id)
                            execute_token_action.setProperty("node_name", node_name)
                            execute_token_action.setProperty("section_type", section_type)
                            execute_submenu.addAction(execute_token_action)
                            added_execute = True
                
                if added_print:
                    tokens_submenu.addMenu(print_submenu)
                if added_execute:
                    tokens_submenu.addMenu(execute_submenu)
                
                if added_print or added_execute:
                    menu.addMenu(tokens_submenu)
                    added_actions = True
                    logging.debug(f"Added {section_type} token actions menu")
        
        # Handle token items (individual token files)
        elif data and isinstance(data, dict) and 'token' in data:
            token_type = data.get("token_type", "UNKNOWN").upper()
            token_id = data.get("token")
            node_name = data.get("node", "Unknown")
            
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
                        action = QAction(f"Print FieldBus Structure (Token {token_str})")
                        action.setProperty("action_type", "process_fieldbus")
                        action.setProperty("token_id", token_str)
                        action.setProperty("node_name", node_name)
                        menu.addAction(action)
                        added_actions = True
                        logging.debug(f"Added FBC token action for token {token_id}")
                    
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
                        # Extract token number from the end of token_id
                        token_parts = token_id.split('_')
                        token_num = token_parts[-1] if token_parts else token_id
                        
                        print_action = QAction(f"Print Rupi counters Token '{token_num}'")
                        print_action.setProperty("action_type", "process_rpc")
                        print_action.setProperty("token_id", token_id)
                        print_action.setProperty("rpc_action", "print")
                        
                        clear_action = QAction(f"Clear Rupi counters '{token_num}'")
                        clear_action.setProperty("action_type", "process_rpc")
                        clear_action.setProperty("token_id", token_id)
                        clear_action.setProperty("rpc_action", "clear")
                        
                        menu.addAction(print_action)
                        menu.addAction(clear_action)
                        added_actions = True
                        logging.debug(f"Added RPC token actions for token {token_id}")
        
        # Handle LOG token items
        elif token_type == "LOG":
            # Check if LOG token commands should be shown
            if not self.context_menu_filter.should_show_command(
                node_name=node_name,
                section_type=token_type,
                command_type="all",
                command_category="token"
            ):
                logging.debug(f"Context menu filtered out LOG token command for {token_id}")
            else:
                # Action: Open Log File
                open_action = QAction("Open Log File")
                open_action.setProperty("action_type", "open_log")
                open_action.setProperty("log_path", data.get("log_path"))
                # Action: Clear Log
                clear_action = QAction("Clear Log")
                clear_action.setProperty("action_type", "clear_log")
                clear_action.setProperty("log_path", data.get("log_path"))
                menu.addAction(open_action)
                menu.addAction(clear_action)
                added_actions = True

        # Handle FBC/RPC subgroup selection
        elif item.text(0) in ["FBC", "RPC"]:
            logging.debug(f"Context menu processing {item.text(0)} subgroup")
            try:
                # First try to get node name from item data (most reliable)
                data = item.data(0, Qt.ItemDataRole.UserRole)
                node_name = None
                if data and "node" in data:
                    node_name = data["node"]
                else:
                    # Fallback to parent hierarchy if user data not available
                    node_item = item.parent()
                    if not node_item:
                        raise ValueError(f"{item.text(0)} subgroup has no parent node")
                    # Extract node name from node item text (before space and IP)
                    node_name = node_item.text(0).split(' ', 1)[0].strip()
                    if not node_name:
                        raise ValueError("Node item text is empty")
                
                section_type = item.text(0)
                
                # Use context menu filter service to determine visibility
                if not self.context_menu_filter.should_show_command(
                    node_name=node_name,
                    section_type=section_type,
                    command_type="all",
                    command_category="subgroup"
                ):
                    logging.debug(f"Context menu filtered out for {section_type} subgroup of {node_name}")
                    return None
                
                logging.debug(f"Context menu valid structure detected:")
                logging.debug(f"  Node: {node_name}")
                logging.debug(f"  Subgroup: {item.text(0)}")

                # Create context menu action after validation
                action_text = f"Print All {item.text(0)} Tokens for {node_name}"
                action = QAction(action_text)
                action.setProperty("action_type", "print_all_subgroup")
                action.setProperty("item", item)
                menu.addAction(action)
                
                # Add new Print Tokens submenu
                tokens_submenu = QMenu(f"Print {item.text(0)} Tokens")
                added_tokens = False
                
                # Get node tokens
                node = self.node_manager.get_node(node_name)
                if node:
                    section_type = item.text(0)
                    for token in node.tokens.values():
                        if token.token_type == section_type:
                            token_id = token.token_id
                            
                            # Check if token commands should be shown
                            if not self.context_menu_filter.should_show_command(
                                node_name=node_name,
                                section_type=section_type,
                                command_type="all",
                                command_category="token"
                            ):
                                logging.debug(f"Context menu filtered out {section_type} token command for {token_id}")
                                continue
                            
                            token_action = QAction(f"Token {token_id}")
                            token_action.setProperty("action_type", "print_token_sequential")
                            token_action.setProperty("token_id", token_id)
                            token_action.setProperty("node_name", node_name)
                            token_action.setProperty("section_type", section_type)
                            tokens_submenu.addAction(token_action)
                            added_tokens = True
                
                if added_tokens:
                    menu.addMenu(tokens_submenu)
                    added_actions = True

            except Exception as e:
                logging.error(f"Context menu structure validation failed: {str(e)}")
                return None
                
        if added_actions:
            logging.debug(f"Context menu created with {len(menu.actions())} actions")
            return menu
        else:
            # Add detailed debug info to diagnose missing actions
            logging.debug(f"Context menu - no actions added for item data: {data}")
            logging.debug(f"Item type: {type(item)}")
            logging.debug(f"Token type: {data.get('token_type') if data else 'N/A'}")
            return None
    
    def process_all_fbc_subgroup_commands(self, item):
        """
        Process all FBC commands using command queue.
        
        Args:
            item: The tree item representing the FBC subgroup
        """
        try:
            # First try to get node name from item's user data (most reliable)
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and "node" in data:
                node_name = data["node"]
            else:
                # Fallback to parent hierarchy if user data not available
                section_item = item.parent()
                if not section_item:
                    raise ValueError("FBC subgroup has no parent section")
                node_item = section_item.parent()
                if not node_item:
                    raise ValueError(f"Section {section_item.text(0)} has no parent node")
                # Extract node name from node item text (before space and IP)
                node_name = node_item.text(0).split(' ', 1)[0].strip()
            
            node = self.node_manager.get_node(node_name)
            if not node:
                logging.error(f"Node {node_name} not found")
                return
                
            # Find all FBC tokens in the node
            fbc_tokens = [t for t in node.tokens.values() if t.token_type == "FBC"]
            if not fbc_tokens:
                logging.warning(f"No FBC tokens found in node {node_name}")
                return
                
            logging.info(f"Processing {len(fbc_tokens)} FBC tokens in node {node_name}")
            
            # Queue commands for all FBC tokens
            for token in fbc_tokens:
                command_text = f"print from fbc io structure {token.token_id}0000"
                self.command_queue.add_command(command_text, token)
                
            logging.info(f"Queued {len(fbc_tokens)} commands for node {node_name}")
            self.command_queue.start_processing()
            logging.info(f"Started processing {len(fbc_tokens)} FBC commands")
            
        except Exception as e:
            logging.error(f"Error processing FBC commands: {str(e)}")
    
    def process_all_rpc_subgroup_commands(self, item):
        """
        Process all RPC commands using command queue.
        
        Args:
            item: The tree item representing the RPC subgroup
        """
        try:
            # Get node name from item hierarchy
            section_item = item.parent()
            if not section_item:
                raise ValueError("RPC subgroup has no parent section")
            node_item = section_item.parent()
            if not node_item:
                raise ValueError(f"Section {section_item.text(0)} has no parent node")
            node_name = node_item.text(0).split(' ', 1)[0].strip()
            
            node = self.node_manager.get_node(node_name)
            if not node:
                logging.error(f"Node {node_name} not found")
                return
                
            # Find all RPC tokens in the node
            rpc_tokens = [t for t in node.tokens.values() if t.token_type == "RPC"]
            if not rpc_tokens:
                logging.warning(f"No RPC tokens found in node {node_name}")
                return
                
            logging.info(f"Processing {len(rpc_tokens)} RPC tokens in node {node_name}")
            
            # Queue commands for all RPC tokens
            for token in rpc_tokens:
                command_text = f"print from fbc rupi counters {token.token_id}0000"
                self.command_queue.add_command(command_text, token)
                
            logging.info(f"Queued {len(rpc_tokens)} commands for node {node_name}")
            self.command_queue.start_processing()
            
        except Exception as e:
            logging.error(f"Error processing RPC commands: {str(e)}")
    
    def process_fieldbus_command(self, token_id: str, node_name: str):
        """
        Process fieldbus command with optimized error handling.
        
        Args:
            token_id: The ID of the token to process
            node_name: The name of the node containing the token
        """
        logging.debug(f"Processing Fieldbus command: token_id={token_id}, node_name={node_name}")
        try:
            # Get token and let LogWriter handle path resolution
            token = self.fbc_service.get_token(node_name, token_id)
            # Pass active telnet client for reuse (None for now, will be handled by service)
            self.fbc_service.queue_fieldbus_command(node_name, token_id, None)
            self.command_queue.start_processing()
        except Exception as e:
            logging.error(f"Error processing fieldbus command: {str(e)}")
            
    def process_rpc_command(self, token_id: str, action_type: str):
        """
        Process RPC commands with token validation.
        
        Args:
            token_id: The ID of the token to process
            action_type: The type of action to perform ("print" or "clear")
        """
        if action_type not in ["print", "clear"]:
            return
            
        try:
            if not token_id or not isinstance(token_id, str):
                raise ValueError("Invalid token ID")
                
            token_num = token_id.split('_')[-1]  # Extract token number after last underscore
            command_text = (
                f"print from fbc rupi counters {token_num}0000"
                if action_type == "print"
                else f"clear fbc rupi counters {token_num}0000"
            )
            
            # Log context menu command initiation
            logging.debug(f"Context menu command: {action_type} for token {token_id}")
            
            # Queue the command
            # Note: In the original implementation, this would also set UI elements
            # For now, we'll just queue the command
            node = self.node_manager.get_node_by_token_id(token_id)
            if node:
                token = node.tokens.get(token_id)
                if token:
                    self.command_queue.add_command(command_text, token)
                    self.command_queue.start_processing()
                else:
                    logging.error(f"Token {token_id} not found in node {node.name}")
            else:
                logging.error(f"Node not found for token {token_id}")
                
        except Exception as e:
            logging.error(f"Error processing RPC command: {str(e)}")
    
    def print_tokens_sequentially(self, token_id: str, node_name: str, token_type: str):
        """
        Print token values sequentially for the given token.
        
        Args:
            token_id: The ID of the token to print
            node_name: The name of the node containing the token
            token_type: The type of token (FBC or RPC)
        """
        try:
            # Get node IP from node manager to ensure session reuse
            node = self.node_manager.get_node(node_name)
            if not node:
                raise ValueError(f"Node {node_name} not found")
                
            # Get existing active session if available
            session = None
            for active_session in self.session_manager.get_active_sessions():
                if active_session.config.host == node.ip_address:
                    session = active_session
                    logging.debug(f"Reusing existing session to {node.ip_address}")
                    break
            
            # If no active session found, create a new one
            if not session:
                logging.debug(f"Creating new session to {node.ip_address}")
                # Note: In the original implementation, this would create a telnet session
                # For now, we'll let the services handle session creation
                pass
                
            if token_type == "FBC":
                self.fbc_service.queue_fieldbus_command(node_name, token_id, session)
            else:
                self.rpc_service.queue_rpc_command(node_name, token_id, "print", session)
                
            self.command_queue.start_processing()
        except Exception as e:
            logging.error(f"Error processing {token_type} command: {str(e)}")