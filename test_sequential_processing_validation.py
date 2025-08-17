#!/usr/bin/env python3
"""
Validation test for sequential token processing fix implementation
This test specifically validates:
1. Sequential execution of mixed FBC/RPC tokens
2. Error handling between tokens
3. Command queue synchronization
"""
import sys
import os
import logging
import time
import unittest
from unittest.mock import MagicMock, patch, call
from PyQt6.QtCore import QCoreApplication, QTimer

# Add src to path so we can import commander modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.commander.services.sequential_command_processor import SequentialCommandProcessor
from src.commander.models import NodeToken
from src.commander.command_queue import CommandQueue

class TestSequentialProcessingValidation(unittest.TestCase):
    """Test sequential processing functionality validation"""
    
    def setUp(self):
        """Set up test environment"""
        # Create mock services
        self.mock_command_queue = MagicMock(spec=CommandQueue)
        self.mock_fbc_service = MagicMock()
        self.mock_rpc_service = MagicMock()
        self.mock_session_manager = MagicMock()
        self.mock_logging_service = MagicMock()
        
        # Create processor instance
        self.processor = SequentialCommandProcessor(
            command_queue=self.mock_command_queue,
            fbc_service=self.mock_fbc_service,
            rpc_service=self.mock_rpc_service,
            session_manager=self.mock_session_manager,
            logging_service=self.mock_logging_service
        )
        
        # Mock internal methods like in existing tests
        self.processor._generate_batch_id = MagicMock(return_value="test_batch_123")
        self.processor._normalize_token = MagicMock(side_effect=lambda token, protocol: token)
        self.processor._release_telnet_client = MagicMock()
        self.processor._perform_periodic_cleanup = MagicMock()
        
        # Mock node managers
        self.mock_fbc_node_manager = MagicMock()
        self.mock_rpc_node_manager = MagicMock()
        self.mock_fbc_service.node_manager = self.mock_fbc_node_manager
        self.mock_rpc_service.node_manager = self.mock_rpc_node_manager
        
        # Mock node retrieval
        self.mock_fbc_node = MagicMock()
        self.mock_rpc_node = MagicMock()
        self.mock_fbc_node_manager.get_node.return_value = self.mock_fbc_node
        self.mock_rpc_node_manager.get_node.return_value = self.mock_rpc_node
        
        # Mock token normalization
        self.mock_fbc_service.normalize_token = MagicMock(side_effect=lambda token: token)
        self.mock_rpc_service.normalize_token = MagicMock(side_effect=lambda token: token)
        
    def test_mixed_fbc_rpc_sequential_execution_order(self):
        """Test that FBC and RPC tokens are processed sequentially in order"""
        print("Testing mixed FBC/RPC sequential execution order...")
        
        # Create mixed tokens
        tokens = [
            NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),
            NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11"),
            NodeToken(token_id="164", token_type="FBC", node_ip="192.168.0.11"),
            NodeToken(token_id="165", token_type="RPC", node_ip="192.168.0.11")
        ]
        
        # Track the order of processing
        processing_order = []
        
        # Mock the command queue to track processing order
        def track_add_command(command, token, telnet_client=None):
            processing_order.append((token.token_id, token.token_type))
            # Simulate immediate command completion
            QTimer.singleShot(1, lambda: self.mock_command_queue.command_completed.emit(
                command, "Success", True, token
            ))
            
        self.mock_command_queue.add_command = track_add_command
        
        # Process tokens sequentially
        self.processor.process_tokens_sequentially("AP01m", tokens)
        
        # Process Qt events to allow signals to be handled
        start_time = time.time()
        while self.processor._is_processing and (time.time() - start_time) < 2:
            QCoreApplication.processEvents()
            time.sleep(0.01)
            
        # Verify processing order
        expected_order = [
            ("162", "FBC"),
            ("163", "RPC"), 
            ("164", "FBC"),
            ("165", "RPC")
        ]
        self.assertEqual(processing_order, expected_order, 
                        f"Expected processing order {expected_order}, but got {processing_order}")
        
        print("✓ Mixed FBC/RPC tokens processed sequentially in correct order")
        
    def test_error_handling_does_not_stop_processing(self):
        """Test that errors in one token don't prevent processing of subsequent tokens"""
        print("Testing error handling between tokens...")
        
        # Create tokens with one that will fail
        tokens = [
            NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),
            NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11"),  # This will fail
            NodeToken(token_id="164", token_type="FBC", node_ip="192.168.0.11")
        ]
        
        # Track which tokens were processed
        processed_tokens = []
        
        # Mock the command queue to simulate failure on second token
        def mock_add_command(command, token, telnet_client=None):
            processed_tokens.append(token.token_id)
            
            # Simulate failure for the second token (163)
            if token.token_id == "163":
                QTimer.singleShot(1, lambda: self.mock_command_queue.command_completed.emit(
                    command, "Connection failed", False, token
                ))
            else:
                QTimer.singleShot(1, lambda: self.mock_command_queue.command_completed.emit(
                    command, "Success", True, token
                ))
                
        self.mock_command_queue.add_command = mock_add_command
        
        # Process tokens sequentially
        self.processor.process_tokens_sequentially("AP01m", tokens)
        
        # Process Qt events to allow signals to be handled
        start_time = time.time()
        while self.processor._is_processing and (time.time() - start_time) < 2:
            QCoreApplication.processEvents()
            time.sleep(0.01)
            
        # Verify all tokens were processed despite the error
        expected_processed = ["162", "163", "164"]
        self.assertEqual(processed_tokens, expected_processed,
                        f"Expected all tokens to be processed {expected_processed}, but got {processed_tokens}")
        
        # Verify processing completed successfully
        self.assertFalse(self.processor._is_processing, "Processing should be complete")
        self.assertEqual(self.processor._current_token_index, 3, "All tokens should be processed")
        
        print("✓ Error in one token doesn't prevent processing of subsequent tokens")
        
    def test_command_queue_single_thread_synchronization(self):
        """Test that command queue processes one command at a time"""
        print("Testing command queue synchronization...")
        
        # Check that command queue is configured for single-threaded execution
        queue = CommandQueue()
        max_threads = queue.thread_pool.maxThreadCount()
        
        self.assertEqual(max_threads, 1, 
                        f"Command queue should use single thread, but has {max_threads} threads")
        
        print("✓ Command queue configured for single-threaded execution")
        
    def test_resource_cleanup_between_tokens(self):
        """Test that resources are properly cleaned up between tokens"""
        print("Testing resource cleanup between tokens...")
        
        # Create tokens
        tokens = [
            NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),
            NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11")
        ]
        
        # Track cleanup calls
        cleanup_count = 0
        
        # Mock the cleanup method
        def track_cleanup():
            nonlocal cleanup_count
            cleanup_count += 1
            
        self.processor._release_telnet_client = track_cleanup
        
        # Mock the command queue
        def mock_add_command(command, token, telnet_client=None):
            # Simulate command completion
            QTimer.singleShot(1, lambda: self.mock_command_queue.command_completed.emit(
                command, "Success", True, token
            ))
            
        self.mock_command_queue.add_command = mock_add_command
        
        # Process tokens sequentially
        self.processor.process_tokens_sequentially("AP01m", tokens)
        
        # Process Qt events to allow signals to be handled
        start_time = time.time()
        while self.processor._is_processing and (time.time() - start_time) < 2:
            QCoreApplication.processEvents()
            time.sleep(0.01)
            
        # Verify cleanup was called for each token
        self.assertEqual(cleanup_count, 2,
                        f"Expected 2 cleanup calls, but got {cleanup_count}")
        
        print("✓ Resources properly cleaned up between tokens")

def run_validation_tests():
    """Run all validation tests for sequential processing"""
    print("Sequential Token Processing Validation Test")
    print("=" * 50)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSequentialProcessingValidation)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("All validation tests passed!")
        print("✓ Sequential processing of mixed FBC/RPC tokens validated")
        print("✓ Error handling between tokens verified")
        print("✓ Command queue synchronization confirmed")
        print("✓ Resource cleanup between tokens confirmed")
        return True
    else:
        print("Some tests failed:")
        for failure in result.failures:
            print(f"  {failure[0]}: {failure[1]}")
        for error in result.errors:
            print(f"  {error[0]}: {error[1]}")
        return False

if __name__ == "__main__":
    success = run_validation_tests()
    sys.exit(0 if success else 1)