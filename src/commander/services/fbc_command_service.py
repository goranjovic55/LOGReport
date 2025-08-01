from ..models import NodeToken
from ..node_manager import NodeManager
from ..command_queue import CommandQueue
from PyQt6.QtCore import QObject, pyqtSignal
import os
import logging

class FbcCommandService(QObject):
    logger = logging.getLogger(__name__)

    # Define signals for communication
    set_command_text = pyqtSignal(str)
    switch_to_telnet_tab = pyqtSignal()
    focus_command_input = pyqtSignal()
    status_message = pyqtSignal(str, int)  # message, duration
    report_error = pyqtSignal(str)         # error message
    
    def __init__(self, node_manager: NodeManager, command_queue: CommandQueue, log_writer=None, parent=None):
        super().__init__(parent)
        self.node_manager = node_manager
        self.command_queue = command_queue
        self.log_writer = log_writer
        self.logger = logging.getLogger(__name__)
        
    def generate_fieldbus_command(self, token_id: str) -> str:
        """Generate FBC command text for a token ID"""
        normalized_token = self.normalize_token(token_id)
        return f"print from fbc io structure {normalized_token}0000"
    
    def normalize_token(self, token_id: str) -> str:
        """Normalize token ID to 3-digit format"""
        token_str = str(token_id).strip()
        return token_str.zfill(3) if token_str.isdigit() else token_str
    
    def _initialize_log_file(self, token: NodeToken):
        """Initialize log file for the token if not already initialized"""
        try:
            # Use provided log_writer or get reference from parent (CommanderWindow)
            log_writer = self.log_writer
            if log_writer is None and hasattr(self.parent(), 'log_writer'):
                log_writer = self.parent().log_writer
                
                # Check if log is already initialized for this token
                if token.token_id not in log_writer.loggers:
                    # Get node from node manager
                    node = self.node_manager.get_node_by_token(token)
                    if not node:
                        # Fallback to creating a temporary node with token's name
                        from ..models import Node
                        node = Node(name=token.name, ip_address=token.ip_address)
                    
                    # Generate log path using shared utility
                    log_path = log_writer.get_node_log_path(node, token.token_id, token.token_type.lower())
                    
                    # Open log file
                    log_writer.open_log(node.name, node.ip_address, token, log_path)
                    self.logger.debug(f"Initialized log file for token {token.token_id} at {log_path}")
        except Exception as e:
            self.logger.warning(f"Failed to initialize log file for token {token.token_id}: {str(e)}")
            # Don't fail the command if log initialization fails
    
    def get_token(self, node_name: str, token_id: str) -> NodeToken:
        """Retrieve token from node manager with multiple lookup attempts"""
        node = self.node_manager.get_node(node_name)
        if not node:
            raise ValueError(f"Node {node_name} not found")
        
        # First try to find existing FBC token with matching ID
        token_formats = [token_id, str(int(token_id)) if token_id.isdigit() else token_id]
        for fmt in token_formats:
            if token := node.tokens.get(fmt):
                # Only return token if it's an FBC token
                if token.token_type == "FBC":
                    return token
        
        # Create temporary FBC token if not found
        # Extract base node name (before space) for directory path consistency with FBC pattern
        base_node_name = node_name.split()[0] if " " in node_name else node_name
        return NodeToken(
            token_id=token_id,
            token_type="FBC",
            name=base_node_name,
            ip_address="0.0.0.0"
        )
    
    def queue_fieldbus_command(self, node_name: str, token_id: str, telnet_client=None):
        """Queue FBC command for execution with optional telnet client"""
        self.logger.info(f"FbcCommandService.queue_fieldbus_command: Starting command queue for node '{node_name}' token '{token_id}'")
        try:
            token = self.get_token(node_name, token_id)
            self.logger.debug(f"FbcCommandService.queue_fieldbus_command: Retrieved token - ID: {token.token_id}, Type: {token.token_type}, Node: {token.name}, IP: {token.ip_address}")
            
            # Ensure log file is initialized before queuing command
            self._initialize_log_file(token)
            
            command = self.generate_fieldbus_command(token_id)
            self.logger.debug(f"FbcCommandService.queue_fieldbus_command: Generated command: {command}")
            self.logger.debug(f"FbcCommandService.queue_fieldbus_command: Full token details: {vars(token)}")
            
            # Emit signals to update UI
            self.logger.debug("FbcCommandService.queue_fieldbus_command: Emitting UI update signals")
            self.set_command_text.emit(command)
            self.switch_to_telnet_tab.emit()
            self.focus_command_input.emit()
            self.status_message.emit(f"Queued FBC command for token {token_id}", 3000)
            
            self.logger.info(f"FbcCommandService.queue_fieldbus_command: Adding command to queue - Command: '{command}', Token: {token.token_id}")
            self.command_queue.add_command(command, token, telnet_client)
            self.logger.info("FbcCommandService.queue_fieldbus_command: Command added to queue")
        except Exception as e:
            self.logger.error(f"Error queuing FBC command: {str(e)}", exc_info=True)
            self.report_error.emit(f"Error queuing command: {str(e)}")
            self.status_message.emit(f"Error queuing command: {str(e)}", 5000)