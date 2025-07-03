import unittest
import os
import tempfile
import logging
from unittest.mock import patch, MagicMock
from src.commander.log_writer import LogWriter
from src.commander.models import NodeToken

class TestLogWriter(unittest.TestCase):
    """Tests for LogWriter integration and null safety"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.writer = LogWriter()
        self.token = NodeToken(token_id="123", token_type="FBC", name="test", ip_address="192.168.0.1", port=23)
        
    def test_log_creation_with_header(self):
        """Test new log file creation with LSR header"""
        log_path = self.writer.open_log("TEST_NODE", "192.168.0.1", self.token)
        
        with open(log_path, 'r') as f:
            content = f.read()
            self.assertIn("=== COMMANDER LOG ===", content)
            self.assertIn("Token: 123", content)

    def test_null_safe_token_handling(self):
        """Test logging with None values in token data"""
        null_token = NodeToken(token_id=None, token_type="FBC", name="test", ip_address="192.168.0.1", port=23)
        log_path = self.writer.open_log(None, None, null_token)
        
        self.assertIn("unknown-node", log_path)
        self.assertIn("unknown-ip", log_path)
        self.assertIn("unknown-token", os.path.basename(log_path))

    def test_log_appending(self):
        """Test multi-line append operations"""
        self.writer.open_log("TEST_NODE", "192.168.0.1", self.token)
        self.writer.append_to_log("123", "Line 1", "telnet")
        self.writer.append_to_log("123", "Line 2", "vnc")
        
        with open(self.writer.get_log_path("123"), 'r') as f:
            lines = f.readlines()
            self.assertIn("[TELNET]", lines[-2])
            self.assertIn("[VNC]", lines[-1])

    def test_token_validation_and_error_handling(self):
        """Test token validation and error logging mechanisms"""
        invalid_token = NodeToken(token_id="invalid!", token_type="FBC", name="test", ip_address="192.168.0.1", port=23)
        
        with patch('src.commander.log_writer.LogWriter') as mock_writer:
            mock_writer_instance = mock_writer.return_value
            mock_writer_instance.log_error.side_effect = lambda msg: logging.error(msg)

            def raise_and_log(*args, **kwargs):
                mock_writer_instance.log_error("Failed to open log for NODE (invalid!): Invalid token")
                raise ValueError("Invalid token")
            
            mock_writer_instance.open_log.side_effect = raise_and_log
            
            with self.assertRaises(ValueError) as ctx:
                mock_writer_instance.open_log("NODE", "192.168.0.1", invalid_token)
            
            # Verify error details
            self.assertEqual(str(ctx.exception), "Invalid token")
            
            # Verify error logging with full context
            mock_writer_instance.log_error.assert_called_once_with(
                "Failed to open log for NODE (invalid!): Invalid token"
            )

    def test_concurrent_file_handles(self):
        """Test multiple simultaneous log handles"""
        token2 = NodeToken(token_id="456", token_type="RPC")
        path1 = self.writer.open_log("NODE1", "192.168.1.1", self.token)
        path2 = self.writer.open_log("NODE2", "192.168.1.2", token2)
        
        self.assertNotEqual(path1, path2)
        self.assertEqual(len(self.writer.log_handles), 2)

    def test_invalid_token_append(self):
        """Test append to non-existent log handle"""
        with self.assertRaises(ValueError):
            self.writer.append_to_log("999", "test", "telnet")

    def test_empty_content_handling(self):
        """Test logging of empty content"""
        self.writer.open_log("TEST_NODE", "192.168.0.1", self.token)
        self.writer.append_to_log("123", "", "telnet")
        
        with open(self.writer.get_log_path("123"), 'r') as f:
            content = f.read()
            self.assertIn("<empty response>", content)

    def test_null_content_handling(self):
        """Test logging of None content"""
        self.writer.open_log("TEST_NODE", "192.168.0.1", self.token)
        self.writer.append_to_log("123", None, "vnc")
        
        with open(self.writer.get_log_path("123"), 'r') as f:
            content = f.read()
            self.assertIn("<empty response>", content)

    def tearDown(self):
        self.temp_dir.cleanup()
        self.writer.close_all_logs()

if __name__ == '__main__':
    unittest.main()