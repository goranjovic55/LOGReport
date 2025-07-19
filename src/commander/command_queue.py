from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool
from typing import List, Optional
from .models import NodeToken

@dataclass
class QueuedCommand:
    """Represents a command in the execution queue"""
    command: str
    token: NodeToken
    status: str = 'pending'  # pending|processing|completed|failed

class CommandWorker(QRunnable):
    """Worker for executing a single command in a thread"""
    
    def __init__(self, command: str, token: NodeToken, telnet_session=None):
        super().__init__()
        self.command = command
        self.token = token
        self.telnet_session = telnet_session
        self.result = None
        self.success = False
        
    def run(self):
        """Execute the command and store the result"""
        try:
            if not self.telnet_session or not self.telnet_session.is_connected:
                error_msg = (
                    f"Telnet session not connected for command: {self.command}\n"
                    f"Token: {self.token.token_id} ({self.token.token_type})\n"
                    f"Node: {self.token.node_name} ({self.token.node_ip})"
                )
                raise ConnectionError(error_msg)
                
            # Execute command via Telnet session
            self.result = self.telnet_session.send_command(self.command)
            self.success = True
            
        except Exception as e:
            import traceback
            error_details = (
                f"Command failed: {self.command}\n"
                f"Token: {self.token.token_id} ({self.token.token_type})\n"
                f"Node: {self.token.node_name} ({self.token.node_ip})\n"
                f"Error: {str(e)}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            logging.error(error_details)
            self.result = f"Command failed: {str(e)}"
            self.success = False

class CommandQueue(QObject):
    """Manages a queue of commands to execute with progress tracking"""
    
    command_completed = pyqtSignal(str, bool)  # command, success
    progress_updated = pyqtSignal(int, int)    # current, total
    
    def __init__(self, session_manager=None):
        super().__init__()
        self.queue: List[QueuedCommand] = []
        self.thread_pool = QThreadPool.globalInstance()
        self.completed_count = 0
        self.session_manager = session_manager
        
    def add_command(self, command: str, token: NodeToken):
        """Add a command to the queue with associated token"""
        self.queue.append(QueuedCommand(
            command=command,
            token=token
        ))
        
    def start_processing(self):
        """Start processing all commands in the queue"""
        self.completed_count = 0
        total = len(self.queue)
        if total == 0:
            return
            
        # Update all commands to processing status
        for item in self.queue:
            item.status = 'processing'
            
        # Create and start workers for each command
        for item in self.queue:
            # Get telnet session from directly injected session manager
            session_key = f"{item.token.node_name}_{item.token.token_type}"
            telnet_session = self.session_manager.get_or_create_session(
                session_key,
                SessionType.TELNET,
                SessionConfig(host=item.token.node_ip)
            )

            worker = CommandWorker(item.command, item.token, telnet_session)
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
            if item.command == command:
                item.status = 'completed' if success else 'failed'
                break
        
        # Emit progress update
        self.progress_updated.emit(self.completed_count, len(self.queue))
        
        # Emit command completion
        self.command_completed.emit(command, success)
        
    def validate_token(self, token: NodeToken) -> bool:
        """Validate token has required fields"""
        return bool(token and token.token_id and token.token_type)