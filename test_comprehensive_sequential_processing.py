#!/usr/bin/env python3
"""
Comprehensive test for sequential token processing fix implementation
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
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import QCoreApplication, QTimer

# Add src to path so we can import commander modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.commander.services.sequential_command_processor import SequentialCommandProcessor
from src.commander.models import NodeToken
from src.commander.command_queue import CommandQueue
from src.commander.services.fbc_command_service import FbcCommandService
from src.commander.services.rpc_command_service import RpcCommandService
from src.commander.session_manager import SessionManager

class TestComprehensiveSequentialProcessing(unittest.TestCase):
    """Test comprehensive sequential processing functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = QCoreApplication.instance() or QCoreApplication([])
        
        # Create mock services
        self.mock_command_queue = MagicMock(spec=CommandQueue)
        self.mock_fbc_service = MagicMock(spec=FbcCommandService)
        self.mock_rpc_service = MagicMock(spec=RpcCommandService)
        self.mock_session_manager = MagicMock(spec=SessionManager)
        self.mock_logging_service = MagicMock()
        
        # Create processor instance
        self.processor = SequentialCommandProcessor(
            command_queue=self.mock_command_queue,
            fbc_service=self.mock_fbc_service,
            rpc_service=self.mock_rpc_service,
            session_manager=self.mock_session_manager,
            logging_service=self.mock_logging_service
        )
        
        # Mock internal methods
        self.processor._generate_batch_id = MagicMock(return_value="test_batch_123")
        
    def test_mixed_fbc_rpc_sequential_execution(self):
        """Test that FBC and RPC tokens are processed sequentially in order"""
        print("Testing mixed FBC/RPC sequential execution...")
        
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
        original_add_command = self.processor.command_queue.add_command
        
        def track_add_command(command, token, telnet_client=None):
            processing_order.append(token.token_type)
            # Simulate command completion after a short delay
            QTimer.singleShot(10, lambda: self.processor.command_queue.command_completed.emit(
                command, "Success", True, token
            ))
            return original_add_command(command, token, telnet_client)
            
        self.processor.command_queue.add_command = track_add_command
        
        # Process tokens sequentially
        self.processor.process_tokens_sequentially("AP01m", tokens)
        
        # Process Qt events to allow signals to be handled
        start_time = time.time()
        while self.processor._is_processing and (time.time() - start_time) < 5:
            QCoreApplication.processEvents()
            time.sleep(0.01)
            
        # Verify processing order
        expected_order = ["FBC", "RPC", "FBC", "RPC"]
        self.assertEqual(processing_order, expected_order, 
                        f"Expected processing order {expected_order}, but got {processing_order}")
        
        print("✓ Mixed FBC/RPC tokens processed sequentially in correct order")
        
    def test_error_handling_between_tokens(self):
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
        error_occurred = False
        
        # Mock the command queue to simulate failure on second token
        def mock_add_command(command, token, telnet_client=None):
            processed_tokens.append(token.token_id)
            
            # Simulate failure for the second token (163)
            if token.token_id == "163":
                QTimer.singleShot(10, lambda: self.processor.command_queue.command_completed.emit(
                    command, "Connection failed", False, token
                ))
            else:
                QTimer.singleShot(10, lambda: self.processor.command_queue.command_completed.emit(
                    command, "Success", True, token
                ))
                
        self.processor.command_queue.add_command = mock_add_command
        
        # Process tokens sequentially
        self.processor.process_tokens_sequentially("AP01m", tokens)
        
        # Process Qt events to allow signals to be handled
        start_time = time.time()
        while self.processor._is_processing and (time.time() - start_time) < 5:
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
        
    def test_command_queue_synchronization(self):
        """Test that command queue processes one command at a time"""
        print("Testing command queue synchronization...")
        
        # Check that command queue is configured for single-threaded execution
        queue = CommandQueue()
        max_threads = queue.thread_pool.maxThreadCount()
        
        self.assertEqual(max_threads, 1, 
                        f"Command queue should use single thread, but has {max_threads} threads")
        
        # Create tokens to test sequential processing
        tokens = [
            NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),
            NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11")
        ]
        
        # Track concurrent processing
        active_commands = 0
        max_concurrent = 0
        processing_sequence = []
        
        # Mock the command queue to track concurrent processing
        def mock_add_command(command, token, telnet_client=None):
            nonlocal active_commands, max_concurrent
            active_commands += 1
            max_concurrent = max(max_concurrent, active_commands)
            processing_sequence.append(token.token_id)
            
            # Simulate command completion
            QTimer.singleShot(50, lambda: self.processor.command_queue.command_completed.emit(
                command, "Success", True, token
            ))
            
        self.processor.command_queue.add_command = mock_add_command
        
        # Process tokens sequentially
        self.processor.process_tokens_sequentially("AP01m", tokens)
        
        # Process Qt events to allow signals to be handled
        start_time = time.time()
        while self.processor._is_processing and (time.time() - start_time) < 5:
            QCoreApplication.processEvents()
            time.sleep(0.01)
            
        # Verify only one command was processed at a time
        self.assertEqual(max_concurrent, 1,
                        f"Maximum concurrent commands should be 1, but was {max_concurrent}")
        
        # Verify processing sequence
        expected_sequence = ["162", "163"]
        self.assertEqual(processing_sequence, expected_sequence,
                        f"Expected processing sequence {expected_sequence}, but got {processing_sequence}")
        
        print("✓ Command queue processes one command at a time")
        print("✓ Commands processed in correct sequence")
        
    def test_batch_processing_with_mixed_tokens(self):
        """Test batch processing with mixed FBC/RPC tokens"""
        print("Testing batch processing with mixed tokens...")
        
        # Create mixed tokens
        tokens = [
            NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),
            NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11"),
            NodeToken(token_id="164", token_type="FBC", node_ip="192.168.0.11"),
            NodeToken(token_id="165", token_type="RPC", node_ip="192.168.0.11")
        ]
        
        # Track processing order
        processing_order = []
        
        # Mock the command queue to track processing
        def mock_add_command(command, token, telnet_client=None):
            processing_order.append(token.token_type)
            
            # Simulate command completion
            QTimer.singleShot(10, lambda: self.processor.command_queue.command_completed.emit(
                command, "Success", True, token
            ))
            
        self.processor.command_queue.add_command = mock_add_command
        
        # Process tokens using batch method
        command_spec = {"node_name": "AP01m"}
        results = self.processor.process_sequential_batch(tokens, "FBC", command_spec)
        
        # Process Qt events to allow signals to be handled
        start_time = time.time()
        while self.processor._is_processing and (time.time() - start_time) < 5:
            QCoreApplication.processEvents()
            time.sleep(0.01)
            
        # Verify processing order
        expected_order = ["FBC", "RPC", "FBC", "RPC"]
        self.assertEqual(processing_order, expected_order,
                        f"Expected processing order {expected_order}, but got {processing_order}")
        
        print("✓ Batch processing handles mixed tokens sequentially")
        
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
        original_cleanup = self.processor._release_telnet_client
        def track_cleanup():
            nonlocal cleanup_count
            cleanup_count += 1
            return original_cleanup()
            
        self.processor._release_telnet_client = track_cleanup
        
        # Mock the command queue
        def mock_add_command(command, token, telnet_client=None):
            # Simulate command completion
            QTimer.singleShot(10, lambda: self.processor.command_queue.command_completed.emit(
                command, "Success", True, token
            ))
            
        self.processor.command_queue.add_command = mock_add_command
        
        # Process tokens sequentially
        self.processor.process_tokens_sequentially("AP01m", tokens)
        
        # Process Qt events to allow signals to be handled
        start_time = time.time()
        while self.processor._is_processing and (time.time() - start_time) < 5:
            QCoreApplication.processEvents()
            time.sleep(0.01)
            
        # Verify cleanup was called for each token
        self.assertEqual(cleanup_count, 2,
                        f"Expected 2 cleanup calls, but got {cleanup_count}")
        
        print("✓ Resources properly cleaned up between tokens")
        
    def test_progress_tracking(self):
        """Test that progress is properly tracked during sequential processing"""
        print("Testing progress tracking...")
        
        # Create tokens
        tokens = [
            NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),
            NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11"),
            NodeToken(token_id="164", token_type="FBC", node_ip="192.168.0.11")
        ]
        
        # Track progress updates
        progress_updates = []
        
        # Connect to progress signal
        def track_progress(current, total):
            progress_updates.append((current, total))
            
        self.processor.progress_updated.connect(track_progress)
        
        # Mock the command queue
        def mock_add_command(command, token, telnet_client=None):
            # Simulate command completion
            QTimer.singleShot(10, lambda: self.processor.command_queue.command_completed.emit(
                command, "Success", True, token
            ))
            
        self.processor.command_queue.add_command = mock_add_command
        
        # Process tokens sequentially
        self.processor.process_tokens_sequentially("AP01m", tokens)
        
        # Process Qt events to allow signals to be handled
        start_time = time.time()
        while self.processor._is_processing and (time.time() - start_time) < 5:
            QCoreApplication.processEvents()
            time.sleep(0.01)
            
        # Verify progress updates
        expected_updates = [(1, 3), (2, 3), (3, 3)]
        self.assertEqual(progress_updates, expected_updates,
                        f"Expected progress updates {expected_updates}, but got {progress_updates}")
        
        print("✓ Progress properly tracked during sequential processing")

def run_comprehensive_tests():
    """Run all comprehensive sequential processing tests"""
    print("Comprehensive Sequential Token Processing Test")
    print("=" * 50)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestComprehensiveSequentialProcessing)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("All comprehensive tests passed!")
        print("✓ Sequential processing of mixed FBC/RPC tokens validated")
        print("✓ Error handling between tokens verified")
        print("✓ Command queue synchronization confirmed")
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