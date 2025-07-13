from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool
from typing import List, Dict, Optional
from .models import NodeToken

class CommandWorker(QRunnable):
    """Worker for executing a single command in a thread"""
    
    def __init__(self, command: str, token: NodeToken):
        super().__init__()
        self.command = command
        self.token = token
        self.result = None
        self.success = False
        
    def run(self):
        """Execute the command and store the result"""
        try:
            # TODO: Implement actual command execution
            # For now, simulate execution
            print(f"Executing command: {self.command}")
            self.result = f"Result for {self.command}"
            self.success = True
        except Exception as e:
            self.result = str(e)
            self.success = False

class CommandQueue(QObject):
    """Manages a queue of commands to execute with progress tracking"""
    
    command_completed = pyqtSignal(str, bool)  # command, success
    progress_updated = pyqtSignal(int, int)    # current, total
    
    def __init__(self):
        super().__init__()
        self.queue: List[Dict] = []
        self.thread_pool = QThreadPool.globalInstance()
        self.completed_count = 0
        
    def add_command(self, command: str, token: NodeToken):
        """Add a command to the queue with associated token"""
        self.queue.append({
            'command': command,
            'token': token,
            'status': 'pending'
        })
        
    def start_processing(self):
        """Start processing all commands in the queue"""
        self.completed_count = 0
        total = len(self.queue)
        if total == 0:
            return
            
        # Update all commands to processing status
        for item in self.queue:
            item['status'] = 'processing'
            
        # Create and start workers for each command
        for item in self.queue:
            worker = CommandWorker(item['command'], item['token'])
            worker.signals = self
            worker.setAutoDelete(True)
            worker.finished.connect(lambda w=worker: self._handle_worker_finished(w))
            self.thread_pool.start(worker)
        
    def _handle_worker_finished(self, worker: CommandWorker):
        """Handle completion of a worker thread"""
        self.completed_count += 1
        success = worker.success
        command = worker.command
        
        # Update command status
        for item in self.queue:
            if item['command'] == command:
                item['status'] = 'completed' if success else 'failed'
                break
        
        # Emit progress update
        self.progress_updated.emit(self.completed_count, len(self.queue))
        
        # Emit command completion
        self.command_completed.emit(command, success)
        
    def validate_token(self, token: NodeToken) -> bool:
        """Validate token has required fields"""
        return bool(token and token.token_id and token.token_type)