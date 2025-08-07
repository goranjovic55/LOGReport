import pytest
from unittest.mock import MagicMock, patch, call
from PyQt6.QtCore import QCoreApplication
from commander.models import NodeToken
from commander.services.sequential_command_processor import SequentialCommandProcessor, CommandResult
from commander.services.logging_service import LoggingService
from commander.command_queue import CommandQueue
from commander.services.fbc_command_service import FbcCommandService
from commander.services.rpc_command_service import RpcCommandService
from commander.session_manager import SessionManager
import uuid
import os
import threading

@pytest.fixture
def mock_services():
    """Fixture providing mocked dependencies"""
    command_queue = MagicMock(spec=CommandQueue)
    fbc_service = MagicMock(spec=FbcCommandService)
    rpc_service = MagicMock(spec=RpcCommandService)
    session_manager = MagicMock(spec=SessionManager)
    logging_service = MagicMock(spec=LoggingService)
    
    # Mock logging service methods
    logging_service.open_log_for_token.return_value = "/mock/log/path.log"
    logging_service.close_log_for_token.return_value = None
    
    return {
        'command_queue': command_queue,
        'fbc_service': fbc_service,
        'rpc_service': rpc_service,
        'session_manager': session_manager,
        'logging_service': logging_service
    }

@pytest.fixture
def processor(mock_services):
    """Fixture providing a processor instance with mocked dependencies"""
    proc = SequentialCommandProcessor(
        command_queue=mock_services['command_queue'],
        fbc_service=mock_services['fbc_service'],
        rpc_service=mock_services['rpc_service'],
        session_manager=mock_services['session_manager'],
        logging_service=mock_services['logging_service']
    )
    return proc

@pytest.fixture
def sample_tokens():
    """Fixture providing sample tokens for testing"""
    return [
        NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),
        NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11"),
        NodeToken(token_id="164", token_type="FBC", node_ip="192.168.0.11")
    ]

def test_batch_id_generation(processor):
    """Verify unique batch IDs are generated for each processing run"""
    batch_ids = set()
    for _ in range(100):
        processor.process_tokens_sequentially("AP01m", [])
        batch_ids.add(processor._batch_id)
    
    assert len(batch_ids) == 100, "All batch IDs should be unique"

def test_per_token_logging(processor, mock_services, sample_tokens):
    """Confirm each token gets its own log file"""
    processor.process_tokens_sequentially("AP01m", sample_tokens)
    
    # Verify logging service was called for each token
    assert mock_services['logging_service'].open_log_for_token.call_count == 3
    assert mock_services['logging_service'].close_log_for_token.call_count == 3
    
    # Verify different tokens were logged
    calls = [call(token_id=t.token_id, node_name="AP01m", node_ip=t.node_ip, 
                protocol=t.token_type, batch_id=processor._batch_id)
            for t in sample_tokens]
    mock_services['logging_service'].open_log_for_token.assert_has_calls(calls, any_order=True)

def test_batch_markers(processor, mock_services, sample_tokens):
    """Validate BATCH START and BATCH END markers in logs"""
    processor.process_tokens_sequentially("AP01m", sample_tokens)
    
    # Verify batch start/end logging
    mock_services['logging_service'].start_batch_logging.assert_called_once_with(
        batch_id=processor._batch_id,
        node_name="AP01m",
        token_count=3
    )
    mock_services['logging_service'].end_batch_logging.assert_called_once_with(
        batch_id=processor._batch_id,
        node_name="AP01m",
        success_count=0,  # Mocked processing doesn't complete commands
        total_count=3
    )

def test_partial_failure_handling(processor, mock_services, sample_tokens):
    """Test processing continues after token failure"""
    # Setup failure on second token
    mock_services['session_manager'].process_rpc_token.side_effect = [
        None,  # First token success
        Exception("Simulated failure"),  # Second token failure
        None   # Third token success
    ]
    
    results = processor.process_sequential_batch(sample_tokens, "FBC", {})
    
    assert len(results) == 3
    assert results[0].success is True
    assert results[1].success is False
    assert "Simulated failure" in results[1].error
    assert results[2].success is True

def test_context_menu_integration(processor, mock_services):
    """Verify menu actions trigger sequential processing"""
    from commander.services.context_menu_service import ContextMenuService
    menu_service = ContextMenuService(processor)
    
    tokens = [NodeToken(token_id="162", token_type="FBC")]
    with patch.object(processor, 'process_tokens_sequentially') as mock_process:
        menu_service.process_tokens("AP01m", tokens, "print")
        mock_process.assert_called_once_with("AP01m", tokens, "print")

def test_log_file_naming(processor, mock_services, tmp_path):
    """Confirm log naming follows existing conventions"""
    # Configure real logging service for this test
    real_logging = LoggingService(log_dir=str(tmp_path))
    processor.logging_service = real_logging
    
    tokens = [NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11")]
    processor.process_tokens_sequentially("AP01m", tokens)
    
    # Verify log file was created with expected pattern
    log_files = list(tmp_path.glob("AP01m_162_FBC*.log"))
    assert len(log_files) == 1, "Expected exactly one matching log file"
    assert "AP01m_162_FBC" in str(log_files[0])

def test_thread_safety(processor, mock_services, sample_tokens):
    """Validate resource handling in concurrent scenarios"""
    results = []
    errors = []
    
    def run_processing():
        try:
            result = processor.process_sequential_batch(sample_tokens, "FBC", {})
            results.append(result)
        except Exception as e:
            errors.append(e)
    
    # Create multiple threads
    threads = [threading.Thread(target=run_processing) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    assert not errors, f"Encountered errors in threaded execution: {errors}"
    assert len(results) == 5, "All threads should complete processing"

def test_empty_token_list(processor, mock_services):
    """Handle empty token list gracefully"""
    processor.process_tokens_sequentially("AP01m", [])
    
    # Verify appropriate logging and no processing attempts
    mock_services['logging_service'].start_batch_logging.assert_not_called()
    mock_services['command_queue'].queue_field_bus_command.assert_not_called()
    mock_services['rpc_service'].queue_rpc_command.assert_not_called()

def test_single_token_processing(processor, mock_services):
    """Verify backward compatibility with single token processing"""
    token = NodeToken(token_id="162", token_type="FBC")
    processor.process_tokens_sequentially("AP01m", [token])
    
    # Verify same core processing as batch
    mock_services['logging_service'].open_log_for_token.assert_called_once()
    mock_services['fbc_service'].queue_field_bus_command.assert_called_once()

def test_circuit_breaker(processor, mock_services):
    """Verify processing stops after 3 consecutive failures"""
    # Create failing tokens
    tokens = [NodeToken(token_id=f"16{i}", token_type="FBC") for i in range(5)]
    mock_services['fbc_service'].queue_field_bus_command.side_effect = Exception("Simulated failure")
    
    results = processor.process_sequential_batch(tokens, "FBC", {})
    
    assert len(results) == 3, "Processing should stop after 3 failures"
    assert all(not r.success for r in results), "All results should be failures"

def test_token_normalization(processor, mock_services):
    """Verify tokens are normalized according to protocol rules"""
    from commander.utils.token_utils import normalize_token
    token = NodeToken(token_id=" 162 ", token_type="FBC")
    
    with patch('commander.utils.token_utils.normalize_token') as mock_normalize:
        mock_normalize.side_effect = normalize_token
        processor.process_tokens_sequentially("AP01m", [token])
        
        mock_normalize.assert_called_with(" 162 ", "FBC")
        mock_services['fbc_service'].queue_field_bus_command.assert_called_with(
            "AP01m", "162", None
        )

# Required to handle Qt event loop in tests
def test_cleanup(qapp):
    QCoreApplication.processEvents()