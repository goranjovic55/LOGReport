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

if __name__ == '__main__':
    unittest.main()