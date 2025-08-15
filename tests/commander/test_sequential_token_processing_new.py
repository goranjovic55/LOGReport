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

def test_sequential_processing_order(processor, mock_services, sample_tokens):
    """Verify tokens are processed in the correct sequential order"""
    # Mock the command queue to simulate sequential processing
    processed_commands = []
    
    def mock_add_command(command, token, telnet_client):
        processed_commands.append((command, token.token_id, token.token_type))
        # Simulate command completion
        processor._on_command_completed(command, "success", True, token)
    
    mock_services['command_queue'].add_command.side_effect = mock_add_command
    
    # Process tokens sequentially
    processor.process_tokens_sequentially("AP01m", sample_tokens)
    
    # Verify commands were processed in order
    assert len(processed_commands) == 3
    assert processed_commands[0][1] == "162"  # First token
    assert processed_commands[1][1] == "163"  # Second token
    assert processed_commands[2][1] == "164"  # Third token

def test_sequential_processing_with_failure(processor, mock_services, sample_tokens):
    """Test that processing continues after a token failure"""
    processed_commands = []
    call_count = 0
    
    def mock_add_command(command, token, telnet_client):
        nonlocal call_count
        processed_commands.append((command, token.token_id, token.token_type))
        call_count += 1
        
        # Simulate failure on second token
        if call_count == 2:
            processor._on_command_completed(command, "failure", False, token)
        else:
            processor._on_command_completed(command, "success", True, token)
    
    mock_services['command_queue'].add_command.side_effect = mock_add_command
    
    # Process tokens sequentially
    processor.process_tokens_sequentially("AP01m", sample_tokens)
    
    # Verify all commands were processed despite failure
    assert len(processed_commands) == 3
    assert processed_commands[0][1] == "162"  # First token (success)
    assert processed_commands[1][1] == "163"  # Second token (failure)
    assert processed_commands[2][1] == "164"  # Third token (success)

def test_sequential_processing_logging(processor, mock_services, sample_tokens):
    """Verify proper logging during sequential processing"""
    def mock_add_command(command, token, telnet_client):
        # Simulate command completion
        processor._on_command_completed(command, "success", True, token)
    
    mock_services['command_queue'].add_command.side_effect = mock_add_command
    
    # Process tokens sequentially
    processor.process_tokens_sequentially("AP01m", sample_tokens)
    
    # Verify batch logging was called
    mock_services['logging_service'].start_batch_logging.assert_called_once()
    mock_services['logging_service'].end_batch_logging.assert_called_once()
    
    # Verify individual token logging
    assert mock_services['logging_service'].open_log_for_token.call_count == 3
    assert mock_services['logging_service'].close_log_for_token.call_count == 3

def test_sequential_processing_progress_updates(processor, mock_services, sample_tokens):
    """Verify progress updates are emitted correctly"""
    progress_updates = []
    
    def progress_callback(current, total):
        progress_updates.append((current, total))
    
    processor.progress_updated.connect(progress_callback)
    
    def mock_add_command(command, token, telnet_client):
        # Simulate command completion
        processor._on_command_completed(command, "success", True, token)
    
    mock_services['command_queue'].add_command.side_effect = mock_add_command
    
    # Process tokens sequentially
    processor.process_tokens_sequentially("AP01m", sample_tokens)
    
    # Verify progress updates
    assert len(progress_updates) == 3
    assert progress_updates[0] == (1, 3)  # First token completed
    assert progress_updates[1] == (2, 3)  # Second token completed
    assert progress_updates[2] == (3, 3)  # Third token completed

def test_sequential_processing_completion_signal(processor, mock_services, sample_tokens):
    """Verify completion signal is emitted correctly"""
    completion_results = []
    
    def completion_callback(success_count, total_count):
        completion_results.append((success_count, total_count))
    
    processor.processing_finished.connect(completion_callback)
    
    def mock_add_command(command, token, telnet_client):
        # Simulate command completion
        processor._on_command_completed(command, "success", True, token)
    
    mock_services['command_queue'].add_command.side_effect = mock_add_command
    
    # Process tokens sequentially
    processor.process_tokens_sequentially("AP01m", sample_tokens)
    
    # Verify completion signal
    assert len(completion_results) == 1
    assert completion_results[0] == (3, 3)  # All tokens successful

def test_sequential_processing_mixed_token_types(processor, mock_services):
    """Test processing with mixed FBC and RPC token types"""
    mixed_tokens = [
        NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),
        NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11"),
        NodeToken(token_id="164", token_type="FBC", node_ip="192.168.0.11"),
        NodeToken(token_id="165", token_type="RPC", node_ip="192.168.0.11")
    ]
    
    processed_commands = []
    
    def mock_add_command(command, token, telnet_client):
        processed_commands.append((command, token.token_id, token.token_type))
        # Simulate command completion
        processor._on_command_completed(command, "success", True, token)
    
    mock_services['command_queue'].add_command.side_effect = mock_add_command
    
    # Process tokens sequentially
    processor.process_tokens_sequentially("AP01m", mixed_tokens)
    
    # Verify all token types were processed
    assert len(processed_commands) == 4
    assert processed_commands[0][2] == "FBC"  # First token type
    assert processed_commands[1][2] == "RPC"  # Second token type
    assert processed_commands[2][2] == "FBC"  # Third token type
    assert processed_commands[3][2] == "RPC"  # Fourth token type

def test_sequential_processing_empty_token_list(processor, mock_services):
    """Test processing with empty token list"""
    # Process empty token list
    processor.process_tokens_sequentially("AP01m", [])
    
    # Verify no commands were added
    mock_services['command_queue'].add_command.assert_not_called()
    
    # Verify proper cleanup
    assert not processor._is_processing

def test_sequential_processing_already_processing(processor, mock_services, sample_tokens):
    """Test processing when already processing"""
    # Set processing flag to simulate ongoing processing
    processor._is_processing = True
    
    # Process tokens
    processor.process_tokens_sequentially("AP01m", sample_tokens)
    
    # Verify no commands were added
    mock_services['command_queue'].add_command.assert_not_called()
    
    # Verify status message was emitted
    # (This would be tested with a signal connection in a real test)