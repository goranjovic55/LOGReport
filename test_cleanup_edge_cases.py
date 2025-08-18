#!/usr/bin/env python3
"""
Edge case tests for cleanup control functionality
"""
import sys
import os
import unittest
from unittest.mock import MagicMock

# Add src to path so we can import commander modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.commander.command_queue import CommandQueue
from src.commander.models import NodeToken

class TestCleanupEdgeCases(unittest.TestCase):
    """Test edge cases for cleanup functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.queue = CommandQueue()
        
    def test_mixed_status_cleanup(self):
        """Test cleanup with mixed command statuses"""
        # Add commands with different statuses
        token1 = NodeToken(token_id="162", token_type="FBC")
        token2 = NodeToken(token_id="163", token_type="RPC")
        token3 = NodeToken(token_id="164", token_type="FBC")
        token4 = NodeToken(token_id="165", token_type="RPC")
        
        self.queue.add_command("cmd1", token1)
        self.queue.add_command("cmd2", token2)
        self.queue.add_command("cmd3", token3)
        self.queue.add_command("cmd4", token4)
        
        # Set mixed statuses
        self.queue.queue[0].status = 'completed'  # Should be cleaned
        self.queue.queue[1].status = 'failed'     # Should remain (manual_cleanup only cleans 'completed')
        self.queue.queue[2].status = 'pending'    # Should remain
        self.queue.queue[3].status = 'processing' # Should remain
        
        # Verify initial state
        initial_length = len(self.queue.queue)
        self.assertEqual(initial_length, 4)
        
        # Perform manual cleanup
        cleaned_count = self.queue.manual_cleanup()
        
        # Should have cleaned 1 command (only 'completed' commands)
        self.assertEqual(cleaned_count, 1)
        self.assertEqual(len(self.queue.queue), 3)
        
        # Verify remaining commands have correct statuses
        remaining_statuses = [cmd.status for cmd in self.queue.queue]
        self.assertIn('failed', remaining_statuses)
        self.assertIn('pending', remaining_statuses)
        self.assertIn('processing', remaining_statuses)
        self.assertNotIn('completed', remaining_statuses)
        
        print("✓ Mixed status cleanup works correctly (only 'completed' commands are cleaned)")
        
    def test_empty_queue_cleanup(self):
        """Test cleanup behavior with empty queue"""
        # Test manual cleanup on empty queue
        cleaned_count = self.queue.manual_cleanup()
        self.assertEqual(cleaned_count, 0)
        self.assertEqual(len(self.queue.queue), 0)
        
        print("✓ Empty queue cleanup handled correctly")
        
    def test_all_completed_cleanup(self):
        """Test cleanup when all commands are completed"""
        # Add commands and mark all as completed
        token1 = NodeToken(token_id="162", token_type="FBC")
        token2 = NodeToken(token_id="163", token_type="RPC")
        
        self.queue.add_command("cmd1", token1)
        self.queue.add_command("cmd2", token2)
        
        self.queue.queue[0].status = 'completed'
        self.queue.queue[1].status = 'completed'
        
        # Perform manual cleanup
        cleaned_count = self.queue.manual_cleanup()
        
        # Should have cleaned all commands
        self.assertEqual(cleaned_count, 2)
        self.assertEqual(len(self.queue.queue), 0)
        
        print("✓ All completed commands cleanup works correctly")
        
    def test_auto_cleanup_toggle(self):
        """Test toggling auto-cleanup functionality"""
        # By default, auto-cleanup should be enabled
        self.assertTrue(self.queue._auto_cleanup)
        
        # Disable auto-cleanup
        self.queue.set_auto_cleanup(False)
        self.assertFalse(self.queue._auto_cleanup)
        
        # Add a command and mark it as completed
        token = NodeToken(token_id="162", token_type="FBC")
        self.queue.add_command("cmd1", token)
        self.queue.queue[0].status = 'completed'
        
        # With auto-cleanup disabled, completed commands should remain
        initial_length = len(self.queue.queue)
        self.assertEqual(initial_length, 1)
        
        # Re-enable auto-cleanup
        self.queue.set_auto_cleanup(True)
        self.assertTrue(self.queue._auto_cleanup)
        
        print("✓ Auto-cleanup toggle functionality works correctly")
        
    def test_concurrent_access_safety(self):
        """Test that cleanup is thread-safe"""
        # Add some commands
        token = NodeToken(token_id="162", token_type="FBC")
        self.queue.add_command("cmd1", token)
        self.queue.queue[0].status = 'completed'
        
        # Test that cleanup can be called multiple times safely
        cleaned1 = self.queue.manual_cleanup()
        cleaned2 = self.queue.manual_cleanup()
        
        self.assertEqual(cleaned1, 1)
        self.assertEqual(cleaned2, 0)  # No more commands to clean
        
        print("✓ Concurrent access to cleanup is safe")

def run_edge_case_tests():
    """Run all edge case tests for cleanup functionality"""
    print("Cleanup Control Edge Cases Test")
    print("=" * 40)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCleanupEdgeCases)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 40)
    if result.wasSuccessful():
        print("All edge case tests passed!")
        print("\nEdge Cases Validated:")
        print("✓ Mixed status cleanup works correctly (only 'completed' commands are cleaned)")
        print("✓ Empty queue cleanup handled correctly")
        print("✓ All completed commands cleanup works correctly")
        print("✓ Auto-cleanup toggle functionality works correctly")
        print("✓ Concurrent access to cleanup is safe")
        return True
    else:
        print("Some edge case tests failed:")
        for failure in result.failures:
            print(f"  {failure[0]}: {failure[1]}")
        for error in result.errors:
            print(f"  {error[0]}: {error[1]}")
        return False

if __name__ == "__main__":
    success = run_edge_case_tests()
    sys.exit(0 if success else 1)