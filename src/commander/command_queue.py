from PyQt6.QtCore import QObject, pyqtSignal
from typing import List, Dict, Optional
from .models import NodeToken

class CommandQueue(QObject):
    """Manages a queue of commands to execute with progress tracking"""
    
    command_completed = pyqtSignal(str, bool)  # command, success
    progress_updated = pyqtSignal(int, int)    # current, total
    
    def __init__(self):
        super().__init__()
        self.queue: List[Dict] = []
        self.current_index = 0
        
    def add_command(self, command: str, token: NodeToken):
        """Add a command to the queue with associated token"""
        self.queue.append({
            'command': command,
            'token': token,
            'status': 'pending'
        })
        
    def start_processing(self):
        """Start processing the queue"""
        self.current_index = 0
        self._process_next()
        
    def _process_next(self):
        """Process next command in queue"""
        if self.current_index >= len(self.queue):
            return
            
        current = self.queue[self.current_index]
        current['status'] = 'processing'
        
        # TODO: Implement actual command execution
        print(f"Processing command: {current['command']}")
        
        self.current_index += 1
        self.progress_updated.emit(self.current_index, len(self.queue))
        self._process_next()
        
    def validate_token(self, token: NodeToken) -> bool:
        """Validate token has required fields"""
        return bool(token and token.token_id and token.token_type)