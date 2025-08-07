import sys
import os
# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

import unittest
from unittest.mock import MagicMock, patch
from commander.services.sequential_command_processor import SequentialCommandProcessor
from commander.models import Token, TokenProcessor
from commander.log_writer import LogWriter

class TestTokenProcessing(unittest.TestCase):
    """Test cases for token processing functionality"""
    
    def setUp(self):
        self.processor = SequentialCommandProcessor()
        self.log_writer = LogWriter()
        self.processor.log_writer = self.log_writer
        
        # Mock the token execution method
        self.processor.execute_token = MagicMock()
        
        # Mock the log writing method
        self.log_writer.write_log = MagicMock()
        
        # Create sample tokens with subclasses
        self.token1 = Token("Subclass1", "Token1", "path1")
        self.token2 = Token("Subclass1", "Token2", "path2")
        self.token3 = Token("Subclass2", "Token3", "path3")
        self.token4 = Token("Subclass2", "Token4", "path4")
        
        # Create a token sequence with subclasses
        self.token_sequence = [
            self.token1,
            self.token2,
            self.token3,
            self.token4
        ]
    
    def test_tokens_processed_in_subclass_sequence(self):
        """Test tokens are processed sequentially within subclasses"""
        self.processor.process_tokens(self.token_sequence)
        
        # Verify tokens were executed in correct order
        expected_calls = [
            unittest.mock.call(self.token1),
            unittest.mock.call(self.token2),
            unittest.mock.call(self.token3),
            unittest.mock.call(self.token4)
        ]
        self.processor.execute_token.assert_has_calls(expected_calls)
    
    def test_token_execution_simulates_right_click(self):
        """Test each token execution simulates a right-click action"""
        self.processor.process_tokens([self.token1])
        
        # Verify execute_token was called with simulate_click=True
        self.processor.execute_token.assert_called_once_with(self.token1, simulate_click=True)
    
    def test_log_entries_written_for_each_token(self):
        """Test log entries are written for each token processed"""
        self.processor.process_tokens(self.token_sequence)
        
        # Verify log entries were written for each token
        self.assertEqual(self.log_writer.write_log.call_count, len(self.token_sequence))
        
        # Verify log content contains token information
        for call in self.log_writer.write_log.call_args_list:
            args, _ = call
            log_content = args[0]
            self.assertIn("Processed token", log_content)
            self.assertIn("subclass", log_content.lower())
    
    def test_log_format_correct(self):
        """Test log entries have the correct format"""
        self.processor.process_tokens([self.token1])
        
        # Verify log format contains required information
        args, _ = self.log_writer.write_log.call_args
        log_content = args[0]
        self.assertIn("Subclass1", log_content)
        self.assertIn("Token1", log_content)
        self.assertIn("path1", log_content)
        self.assertIn("simulated right-click", log_content.lower())

if __name__ == "__main__":
    unittest.main()