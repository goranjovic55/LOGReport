import unittest
import logging
import time
from PyQt6.QtCore import QCoreApplication, QObject, pyqtSignal, QEventLoop, QTimer
from src.commander.command_queue import CommandQueue
from src.commander.models import NodeToken
from unittest.mock import MagicMock, patch

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class TestCommandQueueReprocessing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize QApplication for Qt objects
        cls.app = QCoreApplication.instance()
        if cls.app is None:
            cls.app = QCoreApplication([])
            
    def setUp(self):
        # Create mock session manager
        self.session_manager = MagicMock()
        self.session_manager.get_debugger_session.return_value = None
        self.session_manager.get_or_create_session.return_value = MagicMock(is_connected=True)
        
        # Create command queue
        self.queue = CommandQueue(session_manager=self.session_manager)
        
        # Create test tokens
        self.token1 = NodeToken(token_id="T1", token_type="FBC", name="Node1", ip_address="192.168.1.1")
        self.token2 = NodeToken(token_id="T2", token_type="RPC", name="Node2", ip_address="192.168.1.2")
        self.token3 = NodeToken(token_id="T3", token_type="FBC", name="Node3", ip_address="192.168.1.3")
        
        # Track processed commands
        self.processed_commands = []
        
        # Create event loop for test synchronization
        self.loop = QEventLoop()
        
        # Connect to command_completed signal
        self.queue.command_completed.connect(self.on_command_completed)
        
    def on_command_completed(self, command, result, success, token):
        self.processed_commands.append((command, result, success, token))
        if len(self.processed_commands) >= 3:
            self.loop.quit()
            
    @patch('src.commander.command_queue.time.sleep', return_value=None)
    def test_reprocessing_behavior(self, mock_sleep):
        """Test that the queue properly reprocesses pending commands"""
        # Add commands to the queue
        self.queue.add_command("command1", self.token1)
        self.queue.add_command("command2", self.token2)
        self.queue.add_command("command3", self.token3)
        
        # Start processing
        self.queue.start_processing()
        
        # Set timeout for test
        QTimer.singleShot(5000, self.loop.quit)  # 5 second timeout
        
        # Wait for commands to be processed
        self.loop.exec()
        
        # Verify all commands were processed
        self.assertEqual(len(self.processed_commands), 3, "All commands should be processed")
        
        # Check command order
        self.assertEqual(self.processed_commands[0][0], "command1", "First command should be processed first")
        self.assertEqual(self.processed_commands[1][0], "command2", "Second command should be processed second")
        self.assertEqual(self.processed_commands[2][0], "command3", "Third command should be processed last")
        
        # Verify token states
        logging.debug(f"Processed commands: {self.processed_commands}")

    @patch('src.commander.command_queue.time.sleep', return_value=None)
    def test_thread_safety(self, mock_sleep):
        """Test thread safety when adding commands while processing"""
        # Add initial command
        self.queue.add_command("command1", self.token1)
        
        # Start processing
        self.queue.start_processing()
        
        # Add more commands while processing
        self.queue.add_command("command2", self.token2)
        self.queue.add_command("command3", self.token3)
        
        # Set timeout for test
        QTimer.singleShot(5000, self.loop.quit)  # 5 second timeout
        
        # Wait for commands to be processed
        self.loop.exec()
        
        # Verify all commands were processed
        self.assertEqual(len(self.processed_commands), 3, "All commands should be processed even when added during processing")
        
        # Check processing order
        self.assertEqual(self.processed_commands[0][0], "command1", "Initial command should be processed first")
        self.assertIn("command2", [cmd[0] for cmd in self.processed_commands], "Second command should be processed")
        self.assertIn("command3", [cmd[0] for cmd in self.processed_commands], "Third command should be processed")

if __name__ == "__main__":
    unittest.main()