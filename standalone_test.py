import sys
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QCoreApplication

# Minimal NodeToken class
class NodeToken:
    def __init__(self, token_id, token_type):
        self.token_id = token_id
        self.token_type = token_type

# Minimal SequentialCommandProcessor implementation
class SequentialCommandProcessor(QObject):
    status_message = pyqtSignal(str, int)
    progress_updated = pyqtSignal(int, int)
    processing_finished = pyqtSignal(int, int)

    def __init__(self, command_queue, logging_service, parent=None):
        super().__init__(parent)
        self.command_queue = command_queue
        self.logging_service = logging_service
        self._is_processing = False
        self._total_commands = 0
        self._completed_commands = 0
        self._success_count = 0
        self._current_token_index = 0
        self._tokens = []
        
        self.command_queue.command_completed.connect(self._on_command_completed)

    def process_tokens_sequentially(self, node_name, tokens):
        if self._is_processing:
            print("Already processing commands")
            return
            
        self._is_processing = True
        self._total_commands = len(tokens)
        self._completed_commands = 0
        self._success_count = 0
        self._current_token_index = 0
        self._tokens = tokens

        if not tokens:
            print("No tokens to process")
            self._finish_processing()
            return

        print(f"Starting sequential processing of {len(tokens)} tokens")
        self._process_next_token()

    def _process_next_token(self):
        if self._current_token_index >= len(self._tokens):
            self._finish_processing()
            return

        token = self._tokens[self._current_token_index]
        self._current_token_index += 1
        print(f"Processing token: {token.token_id}")

        # Simulate adding command to queue
        self.command_queue.add_command(f"Command for {token.token_id}", token)

    def _on_command_completed(self, command, result, success, token):
        print(f"Command completed: {command} | Success: {success} | Token: {token.token_id}")
        self._completed_commands += 1
        if success:
            self._success_count += 1
            
        print(f"Progress: {self._completed_commands}/{self._total_commands} | "
              f"Success: {self._success_count}")
        
        if self._current_token_index >= len(self._tokens):
            print("No more tokens - finishing processing")
        else:
            print("Processing next token")
            
        self._process_next_token()

    def _finish_processing(self):
        print(f"Processing finished: {self._success_count} successes, {self._total_commands} total")
        self._is_processing = False
        self.processing_finished.emit(self._success_count, self._total_commands)

# Mock command queue
class MockCommandQueue(QObject):
    command_completed = pyqtSignal(str, str, bool, object)
    
    def add_command(self, command, token):
        # Simulate command completion after short delay
        QTimer.singleShot(100, lambda: self.command_completed.emit(
            command, "Simulated result", True, token
        ))

# Mock logging service
class MockLoggingService:
    def log_debug(self, message):
        print(f"[DEBUG] {message}")

# Main test
if __name__ == "__main__":
    app = QCoreApplication(sys.argv)
    
    # Create services
    command_queue = MockCommandQueue()
    logging_service = MockLoggingService()
    
    # Create processor
    processor = SequentialCommandProcessor(command_queue, logging_service)
    
    # Create sample tokens
    tokens = [
        NodeToken("162", "FBC"),
        NodeToken("163", "RPC"),
        NodeToken("164", "FBC")
    ]
    
    # Process tokens
    processor.process_tokens_sequentially("AP01m", tokens)
    
    # Connect finish signal to quit application
    processor.processing_finished.connect(app.quit)
    
    sys.exit(app.exec())