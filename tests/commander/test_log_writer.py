import unittest
import os
import tempfile
from src.commander.log_writer import LogWriter
from src.commander.models import NodeToken

class TestLogWriter(unittest.TestCase):
    """Tests for LogWriter integration and null safety"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.writer = LogWriter()
        self.token = NodeToken(token_id="123", token_type="FBC")
        
    def test_log_creation_with_header(self):
        """Test new log file creation with LSR header"""
        log_path = self.writer.open_log("TEST_NODE", "192.168.0.1", self.token)
        
        with open(log_path, 'r') as f:
            content = f.read()
            self.assertIn("=== COMMANDER LOG ===", content)
            self.assertIn("Token: 123", content)

    def test_null_safe_token_handling(self):
        """Test logging with None values in token data"""
        null_token = NodeToken(token_id=None, token_type="FBC")
        log_path = self.writer.open_log(None, None, null_token)
        
        self.assertIn("unknown-node", log_path)
        self.assertIn("unknown-ip", log_path)
        self.assertIn("unknown-token", log_path)

    def test_log_appending(self):
        """Test multi-line append operations"""
        self.writer.open_log("TEST_NODE", "192.168.0.1", self.token)
        self.writer.append_to_log("123", "Line 1", "telnet")
        self.writer.append_to_log("123", "Line 2", "vnc")
        
        with open(self.writer.get_log_path("123"), 'r') as f:
            lines = f.readlines()
            self.assertIn("telnet", lines[-2])
            self.assertIn("vnc", lines[-1])

    def test_token_validation_and_error_handling(self):
        """Test token validation and error logging mechanisms"""
        invalid_token = NodeToken(token_id="invalid!", token_type="FBC")
        
        with patch('src.commander.log_writer.TelnetClient') as mock_client:
            mock_client.execute_command.side_effect = Exception("Connection timeout")
            
            with self.assertLogs(level='ERROR') as log_ctx:
                self.writer.open_log("NODE", "192.168.0.1", invalid_token)
                self.writer.append_to_log(invalid_token.token_id, "test", "telnet")
                
            self.assertIn("Invalid token format", log_ctx.output[0])
            self.assertIn("Connection timeout", log_ctx.output[1])

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

    def tearDown(self):
        self.temp_dir.cleanup()
        self.writer.close_all_logs()

if __name__ == '__main__':
    unittest.main()