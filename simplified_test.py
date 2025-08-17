import sys
import os
import logging
from PyQt6.QtCore import QCoreApplication, QTimer
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from commander.services.sequential_command_processor import SequentialCommandProcessor
from commander.models import NodeToken

class MockLoggingService:
    def start_batch_logging(self, batch_id, node_name, token_count):
        print(f"Started batch logging: {batch_id} for {node_name} with {token_count} tokens")
    
    def log_debug(self, message):
        print(f"[DEBUG] {message}")
    
    def end_batch_logging(self, batch_id):
        print(f"Ended batch logging: {batch_id}")

class MockCommandQueue:
    command_completed = pyqtSignal(str, str, bool, object)
    
    def add_command(self, command, token, callback):
        # Simulate command completion after short delay
        QTimer.singleShot(100, lambda: self.command_completed.emit(
            command, "Simulated result", True, token
        ))

# Setup minimal application
app = QCoreApplication(sys.argv)

# Create mock services
logging_service = MockLoggingService()
command_queue = MockCommandQueue()

# Create processor with minimal dependencies
processor = SequentialCommandProcessor(
    command_queue,
    None,  # fbc_service
    None,  # rpc_service
    None,  # session_manager
    logging_service
)

# Create sample tokens
tokens = [
    NodeToken(token_id="162", token_type="FBC"),
    NodeToken(token_id="163", token_type="RPC"),
    NodeToken(token_id="164", token_type="FBC")
]

# Process tokens
processor.process_tokens_sequentially("AP01m", tokens)

# Run application to process events
sys.exit(app.exec())