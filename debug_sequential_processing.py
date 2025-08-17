import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication
import time
from unittest.mock import MagicMock

# Import the classes we need
from src.commander.services.sequential_command_processor import SequentialCommandProcessor
from src.commander.models import NodeToken
from src.commander.command_queue import CommandQueue
from src.commander.services.fbc_command_service import FbcCommandService
from src.commander.services.rpc_command_service import RpcCommandService
from src.commander.session_manager import SessionManager

def main():
    # Create a Qt application
    app = QApplication(sys.argv)
    
    # Create real command queue
    command_queue = CommandQueue()
    
    # Create mock services
    mock_fbc_service = MagicMock()
    mock_rpc_service = MagicMock()
    mock_session_manager = MagicMock()
    mock_logging_service = MagicMock()
    
    # Create the processor
    processor = SequentialCommandProcessor(
        command_queue=command_queue,
        fbc_service=mock_fbc_service,
        rpc_service=mock_rpc_service,
        session_manager=mock_session_manager,
        logging_service=mock_logging_service
    )
    
    # Mock internal methods
    processor._generate_batch_id = MagicMock(return_value="test_batch")
    processor._normalize_token = MagicMock(side_effect=lambda token, _: token)
    processor._release_telnet_client = MagicMock()
    processor._perform_periodic_cleanup = MagicMock()
    
    # Create a test token
    token = NodeToken(token_id="123", token_type="FBC")
    
    print("Before processing:")
    print(f"  _is_processing: {processor._is_processing}")
    print(f"  _total_commands: {processor._total_commands}")
    print(f"  _current_token_index: {processor._current_token_index}")
    
    # Process the token
    processor.process_fbc_commands("test_node", [token])
    
    print("After calling process_fbc_commands:")
    print(f"  _is_processing: {processor._is_processing}")
    print(f"  _total_commands: {processor._total_commands}")
    print(f"  _current_token_index: {processor._current_token_index}")
    
    # Simulate command completion after a short delay
    from PyQt6.QtCore import QTimer
    def emit_completion():
        print("Emitting command completion signal")
        # Create a mock token for the completion signal
        mock_token = NodeToken(token_id="123", token_type="FBC")
        command_queue.command_completed.emit(
            "print from fbc io structure 1230000", "Success", True, mock_token
        )
    
    QTimer.singleShot(100, emit_completion)
    
    # Process events to allow completion
    timeout = 2000  # 2 seconds
    start_time = time.time()
    while processor._is_processing and (time.time() - start_time) * 1000 < timeout:
        QCoreApplication.processEvents()
        time.sleep(0.01)  # Small delay to prevent busy waiting
    
    print("After processing events:")
    print(f"  _is_processing: {processor._is_processing}")
    print(f"  _total_commands: {processor._total_commands}")
    print(f"  _current_token_index: {processor._current_token_index}")
    print(f"  _completed_commands: {processor._completed_commands}")

if __name__ == "__main__":
    main()