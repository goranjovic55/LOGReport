import unittest
import os
from unittest.mock import MagicMock, patch, call
from src.commander.services.logging_service import LoggingService
from src.commander.models import CommandResult, NodeToken

class TestLoggingService(unittest.TestCase):
    """Tests for LoggingService class"""
    
    def setUp(self):
        self.node_manager = MagicMock()
        self.log_writer = MagicMock()
        self.thread_pool = MagicMock()
        self.logging_service = LoggingService(self.node_manager, self.log_writer)
        self.logging_service.set_thread_pool(self.thread_pool)
        
        # Sample token
        self.token = NodeToken(token_id="123", token_type="FBC", ip_address="192.168.0.1")
        self.node_manager.get_node_by_token.return_value = MagicMock(name="TestNode")
        self.log_writer.open_log.return_value = "/test/path.log"

    def test_report_error(self):
        self.logging_service.error("Test error")
        self.log_writer.append_to_log.assert_called_with(
            LoggingService.SYSTEM_TOKEN, "[ERROR] Test error", "system"
        )
        
    def test_report_warning(self):
        self.logging_service.warn("Test warning")
        self.log_writer.append_to_log.assert_called_with(
            LoggingService.SYSTEM_TOKEN, "[WARNING] Test warning", "system"
        )
        
    def test_report_info(self):
        self.logging_service.info("Test info")
        self.log_writer.append_to_log.assert_called_with(
            LoggingService.SYSTEM_TOKEN, "[INFO] Test info", "system"
        )

    def test_log_command_result_manual(self):
        result = CommandResult(
            command="test command", 
            output="success", 
            is_manual=True,
            token=self.token
        )
        self.logging_service.log_command_result(result)
        
        self.log_writer.open_log.assert_called()
        self.log_writer.append_to_log.assert_called_with(
            "123", "Manual command: test command\nOutput: success", "fbc"
        )

    def test_log_command_result_automatic(self):
        result = CommandResult(
            command="auto command", 
            output="completed", 
            is_manual=False,
            token=self.token
        )
        self.logging_service.log_command_result(result)
        
        self.log_writer.append_to_log.assert_called_with(
            "123", "Automatic command: auto command\nOutput: completed", "fbc"
        )

    def test_start_telnet_log(self):
        self.logging_service.start_telnet_log(self.token, "192.168.0.1")
        self.log_writer.open_log.assert_called_with(
            "TestNode", "192.168.0.1", self.token, "fbc"
        )
        self.log_writer.append_to_log.assert_called_with(
            "123", "TELNET SESSION STARTED", "fbc"
        )

    def test_log_telnet_data(self):
        self.logging_service.log_telnet_data("123", "data output", "fbc")
        self.log_writer.append_to_log.assert_called_with(
            "123", "TELNET: data output", "fbc"
        )

    def test_end_telnet_log(self):
        self.logging_service.end_telnet_log("123", "fbc")
        self.log_writer.append_to_log.assert_called_with(
            "123", "TELNET SESSION ENDED", "fbc"
        )
        self.log_writer.close_log.assert_called_with("123", "fbc")

    @patch('src.commander.services.logging_service.is_token_processing_allowed')
    @patch('src.commander.services.logging_service.get_token_processing_wait_time')
    def test_rate_limiting(self, mock_wait_time, mock_allowed):
        mock_allowed.return_value = False
        mock_wait_time.return_value = 0.5
        
        self.logging_service.info("Should be throttled")
        self.log_writer.append_to_log.assert_not_called()
        
        mock_allowed.return_value = True
        self.logging_service.info("Should be logged")
        self.log_writer.append_to_log.assert_called()

    def test_async_logging(self):
        self.logging_service.log_async("123", "Async content", "fbc")
        self.thread_pool.submit.assert_called_once()
        
        # Extract and call the submitted function
        log_func = self.thread_pool.submit.call_args[0][0]
        log_func()
        self.log_writer.append_to_log.assert_called_with("123", "Async content", "fbc")

    def test_automatic_token_preloading(self):
        """Test that logs are pre-opened for tokens when OTP handling starts"""
        token = NodeToken("preloading_test", "FBC", "Preloading Node", "192.168.0.50")
        
        # Simulate token being added for OTP
        self.node_manager.active_otp_tokens = {"valid_otp": token}
        
        # Trigger OTP handling or similar call that triggers preloading
        self.logging_service.log_async("not_a_token", "Some unrelated content", "fbc")
        
        # Verify log was pre-opened
        self.assertTrue(token.token_id in self.logging_service.log_cache)
        self.assertIsNone(self.logging_service.log_cache[token.token_id].write_error)
    
    def test_rotation_and_cleaning(self):
        """Test that old token logs are cleaned up at max capacity"""
        # Fill the cache to trigger rotation
        self.logging_service.log_cache = {str(i): MagicMock() for i in range(12)}
        self.logging_service.log_writer.written_tokens = list(map(str, range(10, 12)))
        
        token = NodeToken("ejected", "FBC", "Ejected Node", "192.168.0.51")
        # The addition should trigger rotation which ejects 4 files
        self.logging_service.log_cache[token.token_id] = MagicMock()
        
        self.assertEqual(len(self.logging_service.log_cache), 10)
        self.assertIn("10", self.logging_service.log_writer.written_tokens)
    
    def test_comprehensive_log_cycle(self):
        """End-to-end test of log lifecycle:
        - Preloading
        - Writing
        - Rotation
        """
        # Set smaller rotation capacity for faster testing
        self.logging_service.LOG_ROTATION_CAPACITY = 3
        
        # 1. Preloading stage
        preload_token = NodeToken("preload", "FBC", "Preload Node", "192.168.0.52")
        self.node_manager.active_otp_tokens = {"valid_otp": preload_token}
        self.logging_service.log_async("not_a_token", "Some unrelated content", "fbc")
        self.assertTrue(preload_token.token_id in self.logging_service.log_cache)
        
        # 2. Regular writing stage
        write_token_1 = NodeToken("write_1", "FBC", "Write Node 1", "192.168.0.53")
        write_token_2 = NodeToken("write_2", "FBC", "Write Node 2", "192.168.0.54")
        
        self.logging_service.log_async(write_token_1.token_id, "Write 1 content", "fbc")
        self.logging_service.log_async(write_token_2.token_id, "Write 2 content", "fbc")
        
        # 3. Rotation stage
        rotation_token = NodeToken("rotate", "FBC", "Rotate Node", "192.168.0.55")
        self.logging_service.log_async(rotation_token.token_id, "Rotating log content", "fbc")
        
        # Verify rotation occurred
        self.assertEqual(len(self.logging_service.log_cache), 3)  # Only 3 should be cached
        # The first two tokens should be ejected
        self.assertNotIn(write_token_1.token_id, self.logging_service.log_cache)
        self.assertNotIn(write_token_2.token_id, self.logging_service.log_cache)
    
    def test_file_size_control(self):
        """Test that files are cleaned up when reaching size limit"""
        self.logging_service.LOG_SIZE_LIMIT_BYTES = 100
        
        # Create small content that will fill the limit
        long_content = 'x' * 101
        fill_token = NodeToken("size_check", "FBC", "Size Check", "192.168.0.56")
        
        # Write first time, should be primed
        self.logging_service.log_async(fill_token.token_id, "Initial content", "fbc")
        self.assertTrue(fill_token.token_id in self.logging_service.log_cache)
        
        # Fill size limit
        self.logging_service.log_async(fill_token.token_id, long_content, "fbc")
        
        # Last part should trigger rotation
        self.assertEqual(len(self.logging_service.log_cache), 1)
        self.assertIn(fill_token.token_id, self.logging_service.log_writer.written_tokens)
    
    def test_backup_creation(self):
        """Test that backups are correctly created at rotation"""
        # Set rotation to 1 file for testing
        self.logging_service.LOG_ROTATION_FILES = 1
        
        backup_token = NodeToken("backup", "FBC", "Backup Node", "192.168.0.57")
        
        # Fill cache and trigger rotation
        self.logging_service.log_cache = {str(i): MagicMock() for i in range(3)}
        
        # Open log for rotation
        log_path = self.logging_service.log_writer.open_log(
            "Backup Node",
            "192.168.0.57", 
            backup_token, 
            "fbc"
        )
        
        # Cache the log to trigger rotation
        self.logging_service.log_cache[str(0)] = MagicMock()
        
        # Verify backup files exist
        base_name = os.path.basename(log_path).split('.')[0]
        log_dir = os.path.dirname(log_path)
        backups = [f for f in os.listdir(log_dir) if f.startswith(base_name)]
        self.assertGreaterEqual(len(backups), 5)  # Original + 5 backups
    
    def test_header_writing(self):
        """Test that headers are written to log files"""
        token = NodeToken("header_test", "FBC", "Header Node", "192.168.0.55")
        log_path = self.logging_service.ensure_per_token_log(token)
        
        # Write header
        self.logging_service.write_header(token, "FBC", "192.168.0.55")
        
        # Verify header content
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("Token: header_test", content)
            self.assertIn("Protocol: FBC", content)
            self.assertIn("Node IP: 192.168.0.55", content)

if __name__ == '__main__':
    unittest.main()