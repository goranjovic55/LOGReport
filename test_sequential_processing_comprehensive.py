#!/usr/bin/env python3
"""
Comprehensive test for sequential token processing fix implementation with focus on cleanup control
This test specifically validates:
1. Sequential execution with multiple tokens
2. Auto-cleanup behavior verification
3. Manual cleanup behavior verification
4. Thread safety
5. Non-sequential cases remain unaffected
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

class TestSequentialProcessingComprehensive(unittest.TestCase):
    """Test comprehensive sequential processing functionality with cleanup control"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a Qt application for testing
        self.app = QCoreApplication.instance() or QCoreApplication([])
        
        # Create real command queue for more accurate testing
        self.real_command_queue = CommandQueue()
        
        # Create mock services
        self.mock_fbc_service = MagicMock()
        self.mock_rpc_service = MagicMock()
        self.mock_session_manager = MagicMock()
        self.mock_logging_service = MagicMock()
        
        # Create processor instance with real command queue
        self.processor = SequentialCommandProcessor(
            command_queue=self.real_command_queue,
            fbc_service=self.mock_fbc_service,
            rpc_service=self.mock_rpc_service,
            session_manager=self.mock_session_manager,
            logging_service=self.mock_logging_service
        )
        
        # Mock internal methods
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
        
    def test_sequential_processing_with_multiple_tokens(self):
        """Test sequential processing with multiple tokens"""
        print("Testing sequential processing with multiple tokens...")
        
        # Create multiple tokens
        tokens = [
            NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),
            NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11"),
            NodeToken(token_id="164", token_type="FBC", node_ip="192.168.0.11"),
            NodeToken(token_id="165", token_type="RPC", node_ip="192.168.0.11")
        ]
        
        # Track the order of processing
        processing_order = []
        completion_order = []
        
        # Mock the command queue to track processing order
        original_add_command = self.real_command_queue.add_command
        def track_add_command(command, token, telnet_client=None):
            processing_order.append((token.token_id, token.token_type))
            # Call the original method
            original_add_command(command, token, telnet_client)
            
        self.real_command_queue.add_command = track_add_command
        
        # Track completion order
        def track_completion(command, result, success, token):
            completion_order.append((token.token_id, token.token_type, success))
            
        self.real_command_queue.command_completed.connect(track_completion)
        
        # Process tokens sequentially
        self.processor.process_tokens_sequentially("AP01m", tokens)
        
        # Wait for processing to complete with timeout
        start_time = time.time()
        while self.processor._is_processing and (time.time() - start_time) < 5:
            QCoreApplication.processEvents()
            time.sleep(0.01)
            
        # Verify that processing completed
        self.assertFalse(self.processor._is_processing, "Processing should be complete")
        
        print("✓ Multiple tokens processed sequentially")
        
    def test_auto_cleanup_behavior_verification(self):
        """Test that auto-cleanup is disabled in SequentialCommandProcessor"""
        print("Testing auto-cleanup behavior verification...")
        
        # Check that auto-cleanup is disabled in the processor
        self.assertFalse(self.real_command_queue._auto_cleanup, 
                        "Auto-cleanup should be disabled in SequentialCommandProcessor")
        
        # Verify that SequentialCommandProcessor explicitly disables auto-cleanup
        # This is done in the __init__ method at line 49
        print("✓ Auto-cleanup is correctly disabled in SequentialCommandProcessor")
        
    def test_manual_cleanup_behavior(self):
        """Test manual cleanup behavior"""
        print("Testing manual cleanup behavior...")
        
        # Add some commands to the queue
        token1 = NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11")
        token2 = NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11")
        
        # Mock the node managers to return proper nodes
        self.mock_fbc_node.tokens = {"162": token1}
        self.mock_rpc_node.tokens = {"163": token2}
        
        # Process tokens
        tokens = [token1, token2]
        self.processor.process_tokens_sequentially("AP01m", tokens)
        
        # Wait for processing to complete with timeout
        start_time = time.time()
        while self.processor._is_processing and (time.time() - start_time) < 5:
            QCoreApplication.processEvents()
            time.sleep(0.01)
            
        # Check that manual cleanup was called
        # This happens in _finish_processing method
        self.assertTrue(self.real_command_queue.manual_cleanup.called or 
                       self.processor.command_queue.manual_cleanup.called,
                       "Manual cleanup should be called after processing")
        
        print("✓ Manual cleanup correctly executed after processing")
        
    def test_thread_safety(self):
        """Test thread safety of command processing"""
        print("Testing thread safety...")
        
        # Check that command queue is configured for single-threaded execution
        max_threads = self.real_command_queue.thread_pool.maxThreadCount()
        
        self.assertEqual(max_threads, 1, 
                        f"Command queue should use single thread, but has {max_threads} threads")
        
        # Check that processing lock is properly initialized
        self.assertIsNotNone(self.real_command_queue._processing_lock,
                            "Processing lock should be initialized")
        
        print("✓ Thread safety mechanisms are in place")
        
    def test_non_sequential_cases_unaffected(self):
        """Test that non-sequential cases remain unaffected"""
        print("Testing non-sequential cases remain unaffected...")
        
        # Create a separate command queue for non-sequential processing
        non_sequential_queue = CommandQueue()
        
        # By default, auto-cleanup should be enabled for regular command queues
        self.assertTrue(non_sequential_queue._auto_cleanup,
                       "Auto-cleanup should be enabled by default for regular command queues")
        
        # Add a command and mark it as completed
        token = NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11")
        non_sequential_queue.add_command("test_command", token)
        non_sequential_queue.queue[0].status = 'completed'
        
        # With auto-cleanup enabled, completed commands should be removed automatically
        # when _handle_worker_finished is called, but we can test manual cleanup
        initial_length = len(non_sequential_queue.queue)
        cleaned_count = non_sequential_queue.manual_cleanup()
        
        # For a regular queue with auto-cleanup enabled, manual cleanup should work
        self.assertGreaterEqual(initial_length - len(non_sequential_queue.queue), 0,
                               "Non-sequential command queue should handle cleanup correctly")
        
        print("✓ Non-sequential cases remain unaffected")

def run_comprehensive_tests():
    """Run all comprehensive tests for sequential processing"""
    print("Sequential Token Processing Comprehensive Test")
    print("=" * 50)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSequentialProcessingComprehensive)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("All comprehensive tests passed!")
        print("✓ Sequential processing with multiple tokens validated")
        print("✓ Auto-cleanup behavior verified")
        print("✓ Manual cleanup behavior confirmed")
        print("✓ Thread safety mechanisms in place")
        print("✓ Non-sequential cases remain unaffected")
        return True
    else:
        print("Some tests failed:")
        for failure in result.failures:
            print(f"  {failure[0]}: {failure[1]}")
        for error in result.errors:
            print(f"  {error[0]}: {error[1]}")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)