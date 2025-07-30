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
        # Mock node_manager for log path generation
        self.writer.node_manager = MagicMock()
        self.writer.node_manager.log_root = self.temp_dir.name
        self.token = NodeToken(token_id="123", token_type="FBC", name="test", ip_address="192.168.0.1", port=23)
        
    def test_log_creation_with_header(self):
        """Test new log file creation with LSR header"""
        log_path = self.writer.get_log_path("TEST_NODE", "192.168.0.1", self.token)
        log_path = self.writer.open_log("TEST_NODE", "192.168.0.1", self.token, log_path)
        
        with open(log_path, 'r') as f:
            content = f.read()
            self.assertIn("=== COMMANDER LOG ===", content)
            self.assertIn("Token: 123", content)

    def test_null_safe_token_handling(self):
        """Test logging with None values in token data"""
        null_token = NodeToken(token_id=None, token_type="FBC", name="test", ip_address="192.168.0.1", port=23)
        log_path = self.writer.get_log_path(None, None, null_token)
        log_path = self.writer.open_log(None, None, null_token, log_path)
        
        self.assertIn("unknown-node", log_path)
        self.assertIn("unknown-ip", log_path)
        self.assertIn("unknown-token", os.path.basename(log_path))

    def test_log_appending(self):
        """Test multi-line append operations"""
        log_path = self.writer.get_log_path("TEST_NODE", "192.168.0.1", self.token)
        self.writer.open_log("TEST_NODE", "192.168.0.1", self.token, log_path)
        self.writer.append_to_log("123", "Line 1", "telnet")
        self.writer.append_to_log("123", "Line 2", "vnc")
        
        with open(log_path, 'r') as f:
            lines = f.readlines()
            self.assertIn("[TELNET] Line 1", lines[-2])
            self.assertIn("[VNC] Line 2", lines[-1])

    def test_token_validation_and_error_handling(self):
        """Test token validation and error logging mechanisms"""
        # Create a token with FBC type but try to open it as LOG log
        # This should trigger a ValueError for type mismatch (FBC->LOG not allowed)
        fbc_token = NodeToken(token_id="123", token_type="FBC", name="test", ip_address="192.168.0.1", port=23)
        
        # Create a log path for LOG type (mismatch with FBC token)
        log_path = os.path.join(self.temp_dir.name, "LOG", "NODE", "NODE_123_192-168-0-1_123.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        # Test that open_log raises ValueError for token type vs file type mismatch
        with self.assertRaises(ValueError) as ctx:
            self.writer.open_log("NODE", "192.168.0.1", fbc_token, log_path)
        
        # Verify error details
        self.assertIn("conflicts with file type", str(ctx.exception))

    def test_concurrent_file_handles(self):
        """Test multiple simultaneous log handles"""
        token2 = NodeToken(token_id="456", token_type="RPC")
        path1 = self.writer.get_log_path("NODE1", "192.168.1.1", self.token)
        path1 = self.writer.open_log("NODE1", "192.168.1.1", self.token, path1)
        path2 = self.writer.get_log_path("NODE2", "192.168.1.2", token2)
        path2 = self.writer.open_log("NODE2", "192.168.1.2", token2, path2)
        
        self.assertNotEqual(path1, path2)
        self.assertEqual(len(self.writer.loggers), 2)

    def test_invalid_token_append(self):
        """Test append to non-existent log handle"""
        with self.assertRaises(ValueError):
            self.writer.append_to_log("999", "test", "telnet")

    def test_empty_content_handling(self):
        """Test logging of empty content"""
        log_path = self.writer.get_log_path("TEST_NODE", "192.168.0.1", self.token)
        self.writer.open_log("TEST_NODE", "192.168.0.1", self.token, log_path)
        self.writer.append_to_log("123", "", "telnet")
        
        with open(log_path, 'r') as f:
            content = f.read()
            self.assertIn("[TELNET] <empty response>", content)

    def test_null_content_handling(self):
        """Test logging of None content"""
        log_path = self.writer.get_log_path("TEST_NODE", "192.168.0.1", self.token)
        self.writer.open_log("TEST_NODE", "192.168.0.1", self.token, log_path)
        self.writer.append_to_log("123", None, "vnc")
        
        with open(log_path, 'r') as f:
            content = f.read()
            self.assertIn("[VNC] <empty response>", content)

    def tearDown(self):
        self.writer.close_all_logs()
        self.temp_dir.cleanup()

if __name__ == '__main__':
    unittest.main()