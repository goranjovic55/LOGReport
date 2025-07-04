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

    def test_start_processing_resets_index(self):
        self.queue.add_command("cmd1", self.valid_token)
        self.queue.add_command("cmd2", self.valid_token)
        self.queue.current_index = 2
        self.queue.start_processing()
        self.assertEqual(self.queue.current_index, 0)

    @patch('builtins.print')
    def test_process_next_updates_progress(self, mock_print):
        self.queue.add_command("cmd1", self.valid_token)
        self.queue.add_command("cmd2", self.valid_token)
        
        with self.subTest("First command processing"):
            self.queue.start_processing()
            mock_print.assert_called_with("Processing command: cmd1")
            self.assertEqual(self.queue.current_index, 1)
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

if __name__ == '__main__':
    unittest.main()