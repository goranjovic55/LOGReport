from ..models import NodeToken
from ..node_manager import NodeManager
from ..command_queue import CommandQueue
from PyQt6.QtCore import QObject, pyqtSignal
import os
import logging

class RpcCommandService(QObject):
    # Define signals for communication
    set_command_text = pyqtSignal(str)
    switch_to_telnet_tab = pyqtSignal()
    focus_command_input = pyqtSignal()
    status_message = pyqtSignal(str, int)  # message, duration
    report_error = pyqtSignal(str)         # error message
    
    def __init__(self, node_manager: NodeManager, command_queue: CommandQueue, parent=None):
        super().__init__(parent)
        self.node_manager = node_manager
        self.command_queue = command_queue
        
    def generate_rpc_command(self, token_id: str, action: str = "print") -> str:
        """Generate RPC command text for a token ID"""
        normalized_token = self.normalize_token(token_id)
        action_map = {
            "print": "print from fbc rupi counters",
            "clear": "clear fbc rupi counters"
        }
        return f"{action_map[action]} {normalized_token}0000"
    
    def normalize_token(self, token_id: str) -> str:
        """Normalize token ID to 3-digit format"""
        token_str = str(token_id).strip()
        return token_str.zfill(3) if token_str.isdigit() else token_str
    
    def get_token(self, node_name: str, token_id: str) -> NodeToken:
        """Retrieve token from node manager with multiple lookup attempts"""
        node = self.node_manager.get_node(node_name)
        if not node:
            raise ValueError(f"Node {node_name} not found")
        
        token_formats = [token_id, str(int(token_id)) if token_id.isdigit() else token_id]
        for fmt in token_formats:
            if token := node.tokens.get(fmt):
                return token
        
        # Create temporary token if not found
        return NodeToken(
            token_id=token_id,
            token_type="RPC",
            name=node_name,
            ip_address="0.0.0.0"
        )
    
    def queue_rpc_command(self, node_name: str, token_id: str, action: str = "print", telnet_client=None):
        """Queue RPC command for execution"""
        try:
            token = self.get_token(node_name, token_id)
            command = self.generate_rpc_command(token_id, action)
            
            # Emit signals to update UI
            self.set_command_text.emit(command)
            self.switch_to_telnet_tab.emit()
            self.focus_command_input.emit()
            self.status_message.emit(f"Queued RPC command for token {token_id}", 3000)
            
            self.command_queue.add_command(command, token, telnet_client)
        except Exception as e:
            self.report_error.emit(str(e))
            self.status_message.emit(f"Error queuing command: {str(e)}", 5000)