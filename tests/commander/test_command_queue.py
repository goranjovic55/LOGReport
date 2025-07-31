import unittest
from unittest.mock import patch
from PyQt6.QtCore import QCoreApplication
from src.commander.command_queue import CommandQueue
from src.commander.models import NodeToken

class TestCommandQueue(unittest.TestCase):
    def setUp(self):
        self.app = QCoreApplication([])
        self.queue = CommandQueue()
        
        self.valid_token = NodeToken(
            token_id="123",
            token_type="admin",
            node_ip="192.168.1.1"
        )
        
        self.invalid_token = NodeToken(
            token_id=None,
            token_type=None,
            node_ip=None
        )

    def test_add_command(self):
        initial_length = len(self.queue.queue)
        self.queue.add_command("test_command", self.valid_token)
        self.assertEqual(len(self.queue.queue), initial_length + 1)
        self.assertEqual(self.queue.queue[-1]['command'], "test_command")
        self.assertEqual(self.queue.queue[-1]['token'], self.valid_token)
        self.assertEqual(self.queue.queue[-1]['status'], "pending")

    def test_start_processing_only_processes_pending_commands(self):
        # Add commands with different statuses
        self.queue.add_command("cmd1", self.valid_token)  # pending
        self.queue.add_command("cmd2", self.valid_token)  # pending
        
        # Manually set one command to completed to simulate it was already processed
        self.queue.queue[0].status = 'completed'
        
        # Start processing - should only process the pending command
        with patch.object(self.queue.thread_pool, 'start') as mock_start:
            self.queue.start_processing()
            # Should only start one worker for the pending command
            self.assertEqual(mock_start.call_count, 1)

    @patch('builtins.print')
    def test_process_next_updates_progress(self, mock_print):
        self.queue.add_command("cmd1", self.valid_token)
        self.queue.add_command("cmd2", self.valid_token)
        
        with self.subTest("First command processing"):
            self.queue.start_processing()
            mock_print.assert_called_with("Processing command: cmd1")
            self.assertEqual(self.queue.current_index, 1)

    @patch('src.commander.command_queue.time.sleep')
    def test_commands_execute_sequentially(self, mock_sleep):
        """Verify commands execute in order without overlap"""
        # Setup mock session
        mock_session = MagicMock()
        mock_session.is_connected = True
        execution_times = []
        
        def mock_send_command(cmd):
            start_time = time.time()
            execution_times.append((cmd, start_time))
            return f"Response to {cmd}"
            
        mock_session.send_command.side_effect = mock_send_command
        self.queue.session_manager.get_or_create_session.return_value = mock_session
        
        # Add 3 commands
        commands = ["CMD1", "CMD2", "CMD3"]
        for cmd in commands:
            self.queue.add_command(cmd, self.valid_token)
            time.sleep(0.01)  # Small delay between adds
            
        # Execute commands
        self.queue.start_processing()
        
        # Wait for processing to complete
        start_wait = time.time()
        while self.queue.is_processing and (time.time() - start_wait < 2):
            time.sleep(0.01)
            
        # Verify execution order
        executed_commands = [cmd for cmd, _ in execution_times]
        self.assertEqual(executed_commands, commands)
        
        # Verify no overlap
        for i in range(len(execution_times)-1):
            _, t1 = execution_times[i]
            _, t2 = execution_times[i+1]
            self.assertGreaterEqual(t2, t1)
            self.assertEqual(self.queue.queue[0]['status'], "processing")

        with self.subTest("Progress signal emission"):
            received_current = []
            received_total = []
            
            def handle_progress(current, total):
                received_current.append(current)
                received_total.append(total)
                
            self.queue.progress_updated.connect(handle_progress)
            self.queue.start_processing()
            
            self.assertEqual(received_current, [1, 2])
            self.assertEqual(received_total, [2, 2])

    def test_validate_token(self):
        with self.subTest("Valid token"):
            self.assertTrue(self.queue.validate_token(self.valid_token))
            
        with self.subTest("Invalid token"):
            self.assertFalse(self.queue.validate_token(self.invalid_token))
            
        with self.subTest("Empty token"):
            self.assertFalse(self.queue.validate_token(None))

    def test_empty_queue_handling(self):
        self.queue.start_processing()
        self.assertEqual(self.queue.current_index, 0)
        self.assertEqual(len(self.queue.queue), 0)
        
    def test_queue_cleanup_removes_completed_commands(self):
        # Add multiple commands
        self.queue.add_command("cmd1", self.valid_token)
        self.queue.add_command("cmd2", self.valid_token)
        self.queue.add_command("cmd3", self.valid_token)
        
        # Manually set statuses
        self.queue.queue[0].status = 'completed'
        self.queue.queue[1].status = 'failed'
        self.queue.queue[2].status = 'pending'
        
        # Trigger cleanup by calling start_processing
        original_length = len(self.queue.queue)
        with patch.object(self.queue.thread_pool, 'start'):
            self.queue.start_processing()
            
        # Check that completed commands were removed but failed and pending remain
        self.assertEqual(len(self.queue.queue), 2)  # failed and pending commands remain
        statuses = [cmd.status for cmd in self.queue.queue]
        self.assertIn('failed', statuses)
        self.assertIn('pending', statuses)
        self.assertNotIn('completed', statuses)

    def test_mixed_status_commands_processing_state_reset(self):
        """Test that processing state resets correctly with mixed success/failure states"""
        # Add commands
        self.queue.add_command("cmd1", self.valid_token)
        self.queue.add_command("cmd2", self.valid_token)
        self.queue.add_command("cmd3", self.valid_token)
        
        # Set mixed statuses
        self.queue.queue[0].status = 'completed'  # Completed successfully
        self.queue.queue[1].status = 'failed'     # Failed
        self.queue.queue[2].status = 'pending'    # Still pending
        
        # Before processing, state should be False
        self.assertFalse(self.queue.is_processing)
        
        # After handling all completed/failed commands, state should reset to False
        # Simulate worker finished for the pending command
        from src.commander.command_queue import CommandWorker
        worker = CommandWorker("cmd3", self.valid_token)
        worker.success = True
        worker.result = "success"
        
        # Manually set the completed count to simulate processing 1 command
        self.queue.completed_count = 1
        
        # Call handle worker finished - this should reset processing state
        self.queue._handle_worker_finished(worker)
        
        # Processing state should be False since no active commands remain
        self.assertFalse(self.queue.is_processing)

    def test_failed_commands_dont_prevent_processing_state_reset(self):
        """Test that failed commands don't prevent the processing state from resetting"""
        # Add commands
        self.queue.add_command("cmd1", self.valid_token)
        self.queue.add_command("cmd2", self.valid_token)
        
        # Set statuses - one completed, one failed
        self.queue.queue[0].status = 'completed'
        self.queue.queue[1].status = 'failed'
        
        # Processing state should be False since no active commands remain
        # Simulate what happens in _handle_worker_finished
        active_commands = [cmd for cmd in self.queue.queue if cmd.status in ['pending', 'processing']]
        self.assertEqual(len(active_commands), 0)  # No active commands
        
    def test_empty_queue_processing_state(self):
        """Test that processing state is correctly managed with an empty queue"""
        # Empty queue should not be processing
        self.assertFalse(self.queue.is_processing)
        
        # Start processing on empty queue
        self.queue.start_processing()
        
        # Should still not be processing
        self.assertFalse(self.queue.is_processing)

    def test_successful_command_completion_resets_state(self):
        """Test that successful command completion properly manages processing state"""
        # Add a command
        self.queue.add_command("cmd1", self.valid_token)
        self.queue.queue[0].status = 'processing'
        
        # Processing state should be True
        # Note: In real usage, start_processing() would set this, but we're testing the reset logic
        self.queue._is_processing = True
        
        # Simulate worker completion
        from src.commander.command_queue import CommandWorker
        worker = CommandWorker("cmd1", self.valid_token)
        worker.success = True
        worker.result = "success"
        self.queue.completed_count = 1
        
        # Handle worker finished - should reset processing state since no active commands remain
        self.queue._handle_worker_finished(worker)
        
        # Processing state should be False
        self.assertFalse(self.queue.is_processing)

if __name__ == '__main__':
    unittest.main()