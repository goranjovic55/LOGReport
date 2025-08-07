"""
Unit tests for the SequentialCommandProcessor class.
"""
import unittest
import time
from unittest.mock import MagicMock, patch, call
from src.commander.services.sequential_command_processor import SequentialCommandProcessor
from src.commander.models import NodeToken
from PyQt6.QtCore import QCoreApplication, QTimer

class TestSequentialCommandProcessor(unittest.TestCase):
    def setUp(self):
        self.mock_logger = MagicMock()
        self.mock_rpc_service = MagicMock()
        self.mock_logging_service = MagicMock()
        self.mock_command_queue = MagicMock()
        self.mock_fbc_service = MagicMock()
        self.mock_session_manager = MagicMock()
        
        self.processor = SequentialCommandProcessor(
            rpc_service=self.mock_rpc_service,
            logging_service=self.mock_logging_service,
            command_queue=self.mock_command_queue,
            fbc_service=self.mock_fbc_service,
            session_manager=self.mock_session_manager
        )
        self.processor.logger = self.mock_logger
        
        # Mock internal methods
        self.processor._generate_batch_id = MagicMock(return_value="test_batch")
        self.processor._normalize_token = MagicMock(side_effect=lambda token, _: token)
        self.processor._execute_token = MagicMock()
        self.processor._release_telnet_client = MagicMock()
        self.processor._perform_periodic_cleanup = MagicMock()
        self.processor.progress_updated = MagicMock()
        
    def test_single_token_success(self):
        """Test processing a single token successfully"""
        # Setup
        token = NodeToken(token_id="123", token_type="FBC")
        self.processor._execute_token.return_value = (True, None)
        
        # Execute
        results = self.processor.process_sequential_batch(
            tokens=[token],
            protocol="FBC",
            command_spec={"node_name": "test_node"}
        )
        
        # Verify
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].success)
        self.assertIsNone(results[0].error)
        self.mock_logging_service.open_log_for_token.assert_called_once()
        self.mock_logging_service.close_log_for_token.assert_called_once()
        self.processor.progress_updated.emit.assert_called_with(1, 1)

    def test_partial_failure_scenario(self):
        """Test processing multiple tokens with partial failures"""
        # Setup
        tokens = [
            NodeToken(token_id="1", token_type="FBC"),
            NodeToken(token_id="2", token_type="FBC"),
            NodeToken(token_id="3", token_type="FBC")
        ]
        self.processor._execute_token.side_effect = [
            (True, None),
            (False, "Timeout error"),
            (True, None)
        ]
        
        # Execute
        results = self.processor.process_sequential_batch(
            tokens=tokens,
            protocol="FBC",
            command_spec={"node_name": "test_node"}
        )
        
        # Verify
        self.assertEqual(len(results), 3)
        self.assertTrue(results[0].success)
        self.assertFalse(results[1].success)
        self.assertEqual(results[1].error, "Timeout error")
        self.assertTrue(results[2].success)
        self.assertEqual(self.mock_logging_service.open_log_for_token.call_count, 3)
        self.assertEqual(self.mock_logging_service.close_log_for_token.call_count, 3)

    def test_circuit_breaker_activation(self):
        """Test circuit breaker activation after 3 consecutive failures"""
        # Setup
        tokens = [NodeToken(token_id=str(i), token_type="FBC") for i in range(5)]
        self.processor._execute_token.return_value = (False, "Error")
        
        # Execute
        results = self.processor.process_sequential_batch(
            tokens=tokens,
            protocol="FBC",
            command_spec={"node_name": "test_node"}
        )
        
        # Verify
        self.assertEqual(len(results), 3)  # Should stop after 3 failures
        for result in results:
            self.assertFalse(result.success)
        # Replace assert_called_with with call_count check
        self.assertEqual(self.mock_logger.error.call_count, 2)

    def test_per_token_log_isolation(self):
        """Verify that each token gets its own log file"""
        # Setup
        tokens = [
            NodeToken(token_id="A", token_type="FBC"),
            NodeToken(token_id="B", token_type="FBC")
        ]
        self.processor._execute_token.return_value = (True, None)
        
        # Execute
        self.processor.process_sequential_batch(
            tokens=tokens,
            protocol="FBC",
            command_spec={"node_name": "test_node"}
        )
        
        # Verify log calls
        self.mock_logging_service.open_log_for_token.assert_any_call("A", "FBC", "test_batch")
        self.mock_logging_service.open_log_for_token.assert_any_call("B", "FBC", "test_batch")
        self.mock_logging_service.close_log_for_token.assert_any_call("A", "FBC", "test_batch")
        self.mock_logging_service.close_log_for_token.assert_any_call("B", "FBC", "test_batch")

    def test_token_specific_error_handling(self):
        """Test that token-specific errors don't abort the entire batch"""
        # Setup
        tokens = [
            NodeToken(token_id="OK", token_type="FBC"),
            NodeToken(token_id="ERR", token_type="FBC"),
            NodeToken(token_id="OK2", token_type="FBC")
        ]
        self.processor._execute_token.side_effect = [
            (True, None),
            Exception("Token specific error"),
            (True, None)
        ]
        
        # Execute
        results = self.processor.process_sequential_batch(
            tokens=tokens,
            protocol="FBC",
            command_spec={"node_name": "test_node"}
        )
        
        # Verify
        self.assertEqual(len(results), 3)
        self.assertTrue(results[0].success)
        self.assertFalse(results[1].success)
        self.assertIn("Token specific error", results[1].error)
        self.assertTrue(results[2].success)

    def test_multiple_tokens_success(self):
        """Test processing multiple tokens successfully with resource cleanup"""
        # Setup
        tokens = [
            NodeToken(token_id="1", token_type="FBC"),
            NodeToken(token_id="2", token_type="FBC"),
            NodeToken(token_id="3", token_type="FBC")
        ]
        self.processor._execute_token.return_value = (True, None)
        
        # Execute
        results = self.processor.process_sequential_batch(
            tokens=tokens,
            protocol="FBC",
            command_spec={"node_name": "test_node"}
        )
        
        # Verify all tokens processed
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertTrue(result.success)
        
        # Verify resource cleanup
        self.assertEqual(self.processor._release_telnet_client.call_count, 3)
        
        # Verify batch ID preservation
        batch_ids = set()
        for call_args in self.mock_logging_service.open_log_for_token.call_args_list:
            batch_ids.add(call_args[0][2])
        self.assertEqual(len(batch_ids), 1, "All tokens should have same batch ID")
        
        # Verify progress tracking
        self.processor.progress_updated.emit.assert_any_call(1, 3)
        self.processor.progress_updated.emit.assert_any_call(2, 3)
        self.processor.progress_updated.emit.assert_any_call(3, 3)

    def test_multi_token_processing_state_transitions(self):
        """Test state transitions during multi-token processing"""
        # Create processor instance
        processor = SequentialCommandProcessor(
            command_queue=MagicMock(),
            fbc_service=MagicMock(),
            rpc_service=MagicMock(),
            session_manager=MagicMock(),
            logging_service=MagicMock()
        )
        
        # Create 3 test tokens
        tokens = [
            NodeToken(token_id="T1", token_type="FBC", name="Node1", ip_address="192.168.1.1"),
            NodeToken(token_id="T2", token_type="FBC", name="Node1", ip_address="192.168.1.1"),
            NodeToken(token_id="T3", token_type="FBC", name="Node1", ip_address="192.168.1.1")
        ]
        
        # Mock queue_fieldbus_command to immediately emit completion
        def mock_queue_command(node_name, token_id, telnet_client):
            QTimer.singleShot(10, lambda: processor.command_queue.command_completed.emit(
                f"Command for {token_id}", 
                "Success", 
                True, 
                NodeToken(token_id=token_id, token_type="FBC")
            ))
        processor.fbc_service.queue_fieldbus_command = MagicMock(side_effect=mock_queue_command)
        
        # Verify initial state is idle
        self.assertFalse(processor._is_processing)
        
        # Start processing
        processor.process_fbc_commands("Node1", tokens)
        
        # Verify processing state is active
        self.assertTrue(processor._is_processing)
        
        # Process events until all tokens are completed
        def check_completion():
            return not processor._is_processing
            
        # Wait for processing to complete with timeout
        timeout = 5000  # 5 seconds
        start_time = time.time()
        while processor._is_processing and (time.time() - start_time) * 1000 < timeout:
            QCoreApplication.processEvents()
        
        # Verify final state is idle
        self.assertFalse(processor._is_processing)
        
        # Verify all tokens were processed
        self.assertEqual(processor._completed_commands, 3)
        self.assertEqual(processor._success_count, 3)
        self.assertEqual(processor._current_token_index, 3)
        
        # Verify state transitions in log
        log_calls = processor.logging_service.log.call_args_list
        self.assertIn("Starting processing of 3 FBC commands for node Node1", str(log_calls))
        self.assertIn("Executing token: T1", str(log_calls))
        self.assertIn("Executing token: T2", str(log_calls))
        self.assertIn("Executing token: T3", str(log_calls))
        self.assertIn("Finished processing 3/3 commands", str(log_calls))

if __name__ == '__main__':
    unittest.main()