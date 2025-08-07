import unittest
import tempfile
import os
import shutil
from unittest.mock import MagicMock, patch
from commander.services.logging_service import LoggingService
from commander.log_writer import LogWriter
from commander.models import NodeToken, CommandResult
from commander.node_manager import NodeManager
from commander.models import TokenProcessor

class TestLoggingIntegration(unittest.TestCase):
    """Integration tests for full logging workflow"""
    
    def setUp(self):
        # Create temporary log directory
        self.temp_dir = tempfile.mkdtemp()
        self.node_manager = NodeManager(log_root=self.temp_dir)
        self.log_writer = LogWriter(self.node_manager)
        self.logging_service = LoggingService(self.node_manager, self.log_writer)
        
        # Setup token processor
        self.token_processor = TokenProcessor(self.node_manager)
        self.logging_service.set_thread_pool(MagicMock())  # Mock thread pool
        
        # Create test node and token
        self.token = NodeToken(token_id="INTEG-123", token_type="FBC", ip_address="192.168.1.100")
        self.node = self.node_manager.create_node("IntegrationNode", "192.168.1.100")
        self.node_manager.assign_token(self.node, self.token)
        
        # Configure mock components
        self.log_writer.open_log = MagicMock()
        self.log_writer.append_to_log = MagicMock()
        self.log_writer.close_log = MagicMock()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_full_command_workflow(self):
        """Test complete command execution workflow"""
        # Process token
        self.token_processor.process_token(self.token)
        
        # Execute manual command
        cmd_result = CommandResult(
            command="show version",
            output="Version 2.0",
            is_manual=True,
            token=self.token
        )
        self.logging_service.log_command_result(cmd_result)
        
        # Execute automatic command
        auto_result = CommandResult(
            command="auto-backup",
            output="Backup complete",
            is_manual=False,
            token=self.token
        )
        self.logging_service.log_command_result(auto_result)
        
        # Verify log interactions
        self.log_writer.open_log.assert_called()
        self.assertEqual(self.log_writer.append_to_log.call_count, 3)
        calls = self.log_writer.append_to_log.call_args_list
        self.assertIn("Manual command: show version", calls[0][0][1])
        self.assertIn("Automatic command: auto-backup", calls[1][0][1])

    def test_telnet_session_workflow(self):
        """Test complete telnet session workflow"""
        # Start telnet session
        self.logging_service.start_telnet_log(self.token, "192.168.1.100")
        
        # Send telnet data
        self.logging_service.log_telnet_data(self.token.token_id, "Connected to device", "fbc")
        self.logging_service.log_telnet_data(self.token.token_id, "show running-config", "fbc")
        
        # End session
        self.logging_service.end_telnet_log(self.token.token_id, "fbc")
        
        # Verify log interactions
        self.log_writer.open_log.assert_called_once()
        self.assertEqual(self.log_writer.append_to_log.call_count, 3)
        calls = self.log_writer.append_to_log.call_args_list
        self.assertIn("TELNET SESSION STARTED", calls[0][0][1])
        self.assertIn("TELNET: show running-config", calls[1][0][1])
        self.assertIn("TELNET SESSION ENDED", calls[2][0][1])
        self.log_writer.close_log.assert_called_once()

    def test_error_reporting_workflow(self):
        """Test error reporting workflow"""
        # Report different error levels
        self.logging_service.error("Critical failure")
        self.logging_service.warn("Potential issue")
        self.logging_service.info("Informational message")
        
        # Verify log interactions
        self.assertEqual(self.log_writer.append_to_log.call_count, 3)
        calls = self.log_writer.append_to_log.call_args_list
        self.assertIn("[ERROR] Critical failure", calls[0][0][1])
        self.assertIn("[WARNING] Potential issue", calls[1][0][1])
        self.assertIn("[INFO] Informational message", calls[2][0][1])

    @patch('logging.handlers.RotatingFileHandler.doRollover')
    def test_log_rotation(self, mock_rollover):
        """Test log rotation mechanics"""
        # Force log rotation by exceeding max bytes
        large_content = "X" * 5000  # Exceeds default 1000 byte limit
        
        # Open log and write large content
        self.logging_service.start_telnet_log(self.token, "192.168.1.100")
        self.logging_service.log_telnet_data(self.token.token_id, large_content, "fbc")
        
        # Verify rollover was called
        mock_rollover.assert_called_once()

    def test_file_creation_and_content(self):
        """Verify actual file creation and content"""
        # Use real file operations (no mocks)
        self.log_writer = LogWriter(self.node_manager)
        self.logging_service = LoggingService(self.node_manager, self.log_writer)
        self.logging_service.set_thread_pool(MagicMock())
        
        # Execute command
        cmd_result = CommandResult(
            command="integration-test",
            output="success",
            is_manual=True,
            token=self.token
        )
        self.logging_service.log_command_result(cmd_result)
        
        # Close log to flush content
        self.log_writer.close_log(self.token.token_id, "fbc")
        
        # Verify file creation
        log_path = self.log_writer.log_paths.get((self.token.token_id, "fbc"))
        self.assertIsNotNone(log_path)
        self.assertTrue(os.path.exists(log_path))
        
        # Verify content
        with open(log_path, 'r') as f:
            content = f.read()
            self.assertIn("Manual command: integration-test", content)
            self.assertIn("Output: success", content)

if __name__ == '__main__':
    unittest.main()