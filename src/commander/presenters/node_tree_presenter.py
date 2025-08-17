"""
Node Tree Presenter - Handles presentation logic for the node tree within the commander window
"""

from abc import ABC, abstractmethod
import logging
import os
import glob
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QTreeWidgetItem

from ..models import NodeToken
from ..node_manager import NodeManager
from ..session_manager import SessionManager
from ..log_writer import LogWriter
from ..command_queue import CommandQueue
from ..services.fbc_command_service import FbcCommandService
from ..services.rpc_command_service import RpcCommandService
from ..icons import get_node_online_icon, get_node_offline_icon, get_token_icon


class NodeTreePresenter(QObject):
    """
    Presenter for the Node Tree, handling presentation logic related to node tree operations
    """
    
    # Signals for UI updates
    status_message_signal = pyqtSignal(str, int)  # message, duration
    node_tree_updated_signal = pyqtSignal()  # emitted when node tree is updated
    
    def __init__(self, view, node_manager: NodeManager, session_manager: SessionManager,
                 log_writer: LogWriter, command_queue: CommandQueue,
                 fbc_service: FbcCommandService, rpc_service: RpcCommandService,
                 context_menu_service):
        """
        Initialize the NodeTreePresenter.

        Args:
            view: The view component (UI) this presenter is associated with
            node_manager: Manager for node operations
            session_manager: Manager for session operations
            log_writer: Writer for log operations
            command_queue: Queue for command execution
            fbc_service: Service for FBC command operations
            rpc_service: Service for RPC command operations
            context_menu_service: Service for context menu operations
        """
        super().__init__()
        self.view = view
        self.node_manager = node_manager
        self.session_manager = session_manager
        self.log_writer = log_writer
        self.command_queue = command_queue
        self.fbc_service = fbc_service
        self.rpc_service = rpc_service
        self.context_menu_service = context_menu_service
        
        # Connect view signals to presenter methods
        self.view.item_expanded.connect(self.handle_item_expanded)
        
        logging.debug("NodeTreePresenter initialized")
    
    def _report_error(self, message: str, exception: Optional[Exception] = None, duration: int = 5000):
        """
        Report an error to the UI.

        Args:
            message: Error message to display
            exception: Optional exception that occurred
            duration: Duration to display the message in milliseconds
        """
        error_msg = f"{message}: {str(exception)}" if exception else message
        logging.error(error_msg)
        self.status_message_signal.emit(error_msg, duration)
        
    def populate_node_tree(self):
        """Lazy-loading tree population - only loads top-level nodes initially"""
        self.view.clear()
        
        # Connect the item expanded signal if not already connected
        # This should be handled by the view, but we'll ensure it here
        self.node_tree_updated_signal.emit()
        
        for node in self.node_manager.get_all_nodes():
            node_item = self._create_node_item(node)
            if node_item:
                # Add placeholder child that will trigger loading when expanded
                placeholder = QTreeWidgetItem(["Click to load..."])
                placeholder.setData(0, Qt.ItemDataRole.UserRole, {"node": node.name, "type": "placeholder"})
                node_item.addChild(placeholder)
                self.view.add_top_level_item(node_item)
                logging.debug(f"Added node with placeholder: {node.name}")
    
    def _create_node_item(self, node):
        """Create node tree item with status icon"""
        node_item = QTreeWidgetItem([f"{node.name} ({node.ip_address})"])
        node_item.setIcon(0, get_node_online_icon() if node.status == "online"
                         else get_node_offline_icon())
        # Store node name in user data for later retrieval
        node_item.setData(0, Qt.ItemDataRole.UserRole, {
            "type": "node",
            "node_name": node.name
        })
        
        # Check log root
        log_root = self.node_manager.log_root
        if not log_root or not os.path.isdir(log_root):
            no_folder = QTreeWidgetItem(["Please set log root folder"])
            no_folder.setIcon(0, get_token_icon())  # Using token icon as warning icon
            node_item.addChild(no_folder)
            return node_item
            
        return node_item
        
    def handle_item_expanded(self, item):
        """Handle lazy loading of node children when expanded"""
        logging.debug(f"Item expanded: {item.text(0)}")
        data = item.data(0, Qt.ItemDataRole.UserRole)
        # Check if expanded item is a node with placeholder child
        if data and data.get("type") == "node":
            # Find placeholder child (if exists)
            for i in range(item.childCount()):
                child = item.child(i)
                child_data = child.data(0, Qt.ItemDataRole.UserRole)
                if child_data and child_data.get("type") == "placeholder":
                    item.removeChild(child)
                    logging.debug(f"Removed placeholder for node: {item.text(0)}")
                    self._load_node_children(item)
                    break  # Only remove first placeholder found
        else:
            logging.debug("Expanded item is not a node or has no placeholder")
    
    def _load_node_children(self, node_item):
        """Load actual children for a node"""
        # Get node name from stored user data
        data = node_item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("type") != "node":
            logging.debug("_load_node_children: Item is not a node")
            return
            
        node_name = data["node_name"]
        logging.debug(f"_load_node_children: Loading children for node: {node_name}")
        node = self.node_manager.get_node(node_name)
        if not node:
            logging.debug(f"_load_node_children: Node {node_name} not found")
            return
            
        added_sections = False
        
        # Create sections for each token type
        sections = [
            ("FBC", self._add_section("FBC", node, "FBC", ['.fbc', '.log', '.txt'])),
            ("RPC", self._add_section("RPC", node, "RPC", ['.rpc', '.log', '.txt'])),
            ("LOG", self._add_section("LOG", node, "LOG", ['.log'])),
            ("LIS", self._add_section("LIS", node, "LIS", ['.lis']))
        ]
        
        logging.debug(f"_load_node_children: Processing sections for node: {node.name}")
        for section_type, section_data in sections:
            logging.debug(f"_load_node_children: Processing {section_type} section")
            logging.debug(f"_load_node_children: Section data: items={len(section_data['items'])}")
            
            # Always create the section item even if no files are found
            section = QTreeWidgetItem([section_type])
            section.setIcon(0, get_token_icon() if section_type in ("FBC", "RPC")
                           else get_token_icon())
            # Store node name in section item's user data for reliable access
            section.setData(0, Qt.ItemDataRole.UserRole, {
                "node": node.name,
                "type": "section",
                "section_type": section_type
            })
            
            if section_data["items"]:
                logging.debug(f"_load_node_children: Adding {len(section_data['items'])} files to {section_type} section")
                for item in section_data["items"]:
                    section.addChild(item)
                logging.debug(f"_load_node_children: Added {section_type} section with {section_data['count']} items")
            else:
                # Add placeholder text if no files found
                placeholder = QTreeWidgetItem(["No files found"])
                placeholder.setIcon(0, get_token_icon())
                section.addChild(placeholder)
                logging.debug(f"_load_node_children: No items found for {section_type} section")
            
            node_item.addChild(section)
            added_sections = True
            logging.debug(f"_load_node_children: Added {section_type} subsection to node tree")
        
        if not added_sections:
            no_files = QTreeWidgetItem(["No files found for this node"])
            no_files.setIcon(0, get_token_icon())
            node_item.addChild(no_files)
            logging.debug(f"_load_node_children: No files found for node: {node_name}")
        
    def _add_section(self, section_type, node, dir_name, extensions):
        """Add file items to section using glob patterns for efficiency"""
        # For LOG files, directory is <log_root>/LOG/<node.name>
        # For others, it's <log_root>/<dir_name>/<node.name>
        if section_type == "LOG":
            section_dir = os.path.join(self.node_manager.log_root, "LOG")
        else:
            section_dir = os.path.join(self.node_manager.log_root, dir_name, node.name)
            
        items = []
        
        if not os.path.isdir(section_dir):
            logging.debug(f"Directory not found: {section_dir}")
            return {"items": items, "count": 0}
            
        # Process files matching patterns
        for ext in extensions:
            if section_type == "LOG":
                pattern = os.path.join(section_dir, f"{node.name}_*.log")
                logging.debug(f"LOG SECTION DEBUG: Scanning directory: {section_dir}")
                logging.debug(f"LOG SECTION DEBUG: Using pattern: {pattern}")
            else:
                pattern = os.path.join(section_dir, f"{node.name}_*{ext}")
                
            logging.debug(f"Scanning for {section_type} files with pattern: {pattern}")
            files_found = glob.glob(pattern)
            logging.debug(f"Found {len(files_found)} files matching pattern")
            
            for file_path in files_found:
                filename = os.path.basename(file_path)
                token_id = self._extract_token_id(filename, node.name, section_type)
                
                logging.debug(f"LOG SECTION DEBUG: Processing file: {filename} | Extracted token: {token_id}")
                
                if not token_id and section_type != "LOG":
                    continue  # Skip invalid tokens except for LOG
                
                file_item = self._create_file_item(
                    filename, file_path, node,
                    token_id, section_type
                )
                items.append(file_item)
                logging.debug(f"Found {section_type} file: {filename}")
                
        logging.debug(f"Total {section_type} files found: {len(items)}")
        if section_type == "LOG" and len(items) == 0:
            logging.warning("No LOG files found! Possible causes:")
            logging.warning(f"1. Directory doesn't exist: {section_dir}")
            logging.warning(f"2. Pattern mismatch: {pattern}")
            logging.warning(f"3. Token extraction failed for existing files")
        return {"items": items, "count": len(items)}
        
    def _extract_token_id(self, filename, node_name, section_type):
        """Extract token ID from filename based on section type"""
        # These patterns should match the ones in CommanderWindow
        FBC_TOKEN_PATTERN = r"^([\w-]+)_[\d\.-]+_([\w-]+)\."
        RPC_TOKEN_PATTERN = r"_([\d\w-]+)\.[^.]*$"  # Matches last _token.extension
        LIS_TOKEN_PATTERN = r"^([\w-]+)_[\d-]+_([\d\w-]+)\.lis$"
        
        if section_type == "LOG":
            # Use the filename without extension as token ID
            return os.path.splitext(filename)[0]
            
        try:
            import re
            if section_type == "FBC":
                match = re.match(FBC_TOKEN_PATTERN, filename)
                return match.group(2) if match and match.group(1) == node_name else None
            elif section_type == "RPC":
                match = re.search(RPC_TOKEN_PATTERN, filename)
                return match.group(1) if match else None
            elif section_type == "LIS":
                match = re.match(LIS_TOKEN_PATTERN, filename)
                return match.group(2) if match and match.group(1) == node_name else None
        except (IndexError, AttributeError):
            return None
            
        return None
        
    def _create_file_item(self, filename, file_path, node, token_id, token_type):
        """Create standardized file tree item"""
        file_item = QTreeWidgetItem([f" {filename}"])
        file_extension = os.path.splitext(file_path)[1][1:].upper()
        resolved_type = file_extension if file_extension in {'FBC','RPC','LOG','LIS'} else token_type
        
        file_item.setData(0, Qt.ItemDataRole.UserRole, {
            "log_path": file_path,
            "token": token_id,
            "token_type": resolved_type,
            "node": node.name,
            "ip_address": node.ip_address
        })
        file_item.setIcon(0, get_token_icon())
        return file_item
        
    def set_log_root_folder(self, folder_path):
        """Set the root folder for log files"""
        # This method is called by the view when the user selects a folder
        if folder_path:
            self.node_manager.set_log_root(folder_path)
            self.node_manager.scan_log_files()
            self.populate_node_tree()
            self.status_message_signal.emit("Log root folder set successfully", 3000)
        
    def load_configuration(self, file_path):
        """Load node configuration from selected file"""
        # This method is called by the view when the user selects a configuration file
        if file_path:
            self.node_manager.set_config_path(file_path)
            if self.node_manager.load_configuration():
                self.node_manager.scan_log_files()
                self.populate_node_tree()
                self.status_message_signal.emit("Configuration loaded successfully", 3000)
            else:
                self.status_message_signal.emit("Error loading node configuration", 5000)
        
    def show_context_menu(self, position):
        """
        Show context menu for the selected item in the node tree.

        Args:
            position: Position where the context menu should be shown
        """
        # Get the item at the mouse position
        item = self.view.itemAt(position)
        if not item:
            return
            
        # Get item data
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return
            
        # Create menu
        from PyQt6.QtWidgets import QMenu
        menu = QMenu()
        
        # Use context menu service to populate and show menu
        global_pos = self.view.viewport().mapToGlobal(position)
        self.context_menu_service.show_context_menu(menu, item_data, global_pos)
        
    def process_all_fbc_subgroup_commands(self, item):
        """
        Process all FBC commands for a subgroup.

        Args:
            item: The tree item representing the subgroup
        """
        if not item:
            self._report_error("No item selected for FBC subgroup processing")
            return
            
        # Get node name from item hierarchy
        section_item = item.parent()
        if not section_item:
            self._report_error("FBC subgroup has no parent section")
            return
        node_item = section_item.parent()
        if not node_item:
            self._report_error(f"Section {section_item.text(0)} has no parent node")
            return
        node_name = node_item.text(0).split(' ', 1)[0].strip()

        # Get tokens from item if available
        tokens = getattr(item, 'tokens', None)
        if not tokens:
            # Fallback to getting all FBC tokens from node
            node = self.node_manager.get_node(node_name)
            if not node:
                self.status_message_signal.emit(f"Node {node_name} not found", 3000)
                return
                
            # Find all FBC tokens in the node
            tokens = [t for t in node.tokens.values() if t.token_type == "FBC"]                
        if not tokens:
            self.status_message_signal.emit(f"No FBC tokens found in node {node_name}", 3000)
            return
            
        logging.info(f"Processing {len(tokens)} FBC tokens in node {node_name}...")
        self.status_message_signal.emit(f"Processing {len(tokens)} FBC tokens in node {node_name}...", 0)
        
        # Process each FBC token
        for token in tokens:
            # Pass active telnet client for reuse if available
            telnet_client = getattr(self, 'active_telnet_client', None)
            self.fbc_service.queue_fieldbus_command(node_name, token.token_id, telnet_client)            
        # Start processing the queue
        self.command_queue.start_processing()
        self.status_message_signal.emit(f"Queued {len(tokens)} commands for node {node_name}", 3000)
            
    def process_all_rpc_subgroup_commands(self, item):
        """
        Process all RPC commands for a subgroup.

        Args:
            item: The tree item representing the subgroup
        """
        if not item:
            self._report_error("No item selected for RPC subgroup processing")
            return
            
        # Get node name from item hierarchy
        section_item = item.parent()
        if not section_item:
            self._report_error("RPC subgroup has no parent section")
            return
        node_item = section_item.parent()
        if not node_item:
            self._report_error(f"Section {section_item.text(0)} has no parent node")
            return
        node_name = node_item.text(0).split(' ', 1)[0].strip()

        # Get tokens from item if available
        tokens = getattr(item, 'tokens', None)
        if not tokens:
            # Fallback to getting all RPC tokens from node
            node = self.node_manager.get_node(node_name)
            if not node:
                self.status_message_signal.emit(f"Node {node_name} not found", 3000)
                return
                
            # Find all RPC tokens in the node
            tokens = [t for t in node.tokens.values() if t.token_type == "RPC"]                
        if not tokens:
            self.status_message_signal.emit(f"No RPC tokens found in node {node_name}", 3000)
            return
            
        logging.info(f"Processing {len(tokens)} RPC tokens in node {node_name}...")
        self.status_message_signal.emit(f"Processing {len(tokens)} RPC tokens in node {node_name}...", 0)
        
        # Pass active telnet client for reuse if available
        telnet_client = getattr(self, 'active_telnet_client', None)
        
        # Queue commands for all RPC tokens using service method
        for token in tokens:
            self.rpc_service.queue_rpc_command(node_name, token.token_id, "print", telnet_client)
            
        self.status_message_signal.emit(f"Queued {len(tokens)} commands for node {node_name}", 3000)
        
    def process_fieldbus_command(self, token_id, node_name):
        """
        Process a single fieldbus command.

        Args:
            token_id: ID of the token to process
            node_name: Name of the node containing the token
        """
        logging.debug(f"Processing Fieldbus command: token_id={token_id}, node_name={node_name}")
        try:
            # Get token first to validate node exists before generating command
            token = self.fbc_service.get_token(node_name, token_id)
            
            # Emit status message before processing
            command = self.fbc_service.generate_fieldbus_command(token_id)
            self.status_message_signal.emit(f"Executing: {command}...", 3000)
            
            # Pass active telnet client for reuse
            telnet_client = getattr(self, 'active_telnet_client', None)
            self.fbc_service.queue_fieldbus_command(node_name, token_id, telnet_client)
            self.command_queue.start_processing()
        except ValueError as e:
            # Handle specific ValueError cases like "Node not found"
            if "not found" in str(e).lower():
                self.status_message_signal.emit(str(e), 3000)
            else:
                self._report_error("Error processing Fieldbus command", e)
        except Exception as e:
            self._report_error("Error processing Fieldbus command", e)
            
    def process_rpc_command(self, node_name, token_id, action_type):
        """
        Process RPC commands with token validation and auto-execute.

        Args:
            node_name: Name of the node containing the token
            token_id: ID of the token to process
            action_type: Type of action (print, clear)
        """
        if action_type not in ["print", "clear"]:
            return
            
        try:
            if not token_id or not isinstance(token_id, str):
                raise ValueError("Invalid token ID")
                
            # Extract token part from token_id (format: NODE_TOKEN)
            token_part = token_id.split('_')[-1] if '_' in token_id else token_id
            
            # Validate token
            token = self.rpc_service.get_token(node_name, token_part)
            if not self.session_manager.validate_token(token):
                self.status_message_signal.emit(f"Invalid token: {token_id}", 5000)
                return
            
            # Pass active telnet client for reuse
            telnet_client = getattr(self, 'active_telnet_client', None)
            
            # Queue command through service
            self.rpc_service.queue_rpc_command(node_name, token_part, action_type, telnet_client)
            self.command_queue.start_processing()
            
        except ValueError as e:
            self._report_error("Invalid RPC command parameters", e)
        except AttributeError as e:
            self._report_error("UI component access error", e)
        except Exception as e:
            logging.error(f"Unexpected error in RPC command setup: {str(e)}")
            self._report_error("RPC command setup failed", e)