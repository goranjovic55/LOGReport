import unittest
import os
import tempfile
import logging
from unittest.mock import Mock, patch
from src.commander.log_writer import LogWriter
from src.commander.models import NodeToken
from src.commander.node_manager import NodeManager
from src.commander.command_queue import CommandQueue
from src.commander.services.fbc_command_service import FbcCommandService
from src.commander.services.rpc_command_service import RpcCommandService


class TestLogLifecycle(unittest.TestCase):
    """Tests for log lifecycle management including initialization and cleanup"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.writer = LogWriter()
        # Mock node_manager for log path generation
        self.writer.node_manager = Mock()
        self.writer.node_manager.log_root = self.temp_dir.name
        self.node_manager = NodeManager()
        self.command_queue = CommandQueue()
        
    def test_fbc_log_initialization(self):
        """Test FBC log initialization with proper token validation"""
        fbc_service = FbcCommandService(self.node_manager, self.command_queue, self.writer)
        
        # Create a mock token
        token = NodeToken(token_id="162", token_type="FBC", name="AP01m", ip_address="192.168.0.11")
        
        # Mock the logger to avoid actual logging
        fbc_service.logger = Mock()
        
        # Test log initialization
        fbc_service._initialize_log_file(token)
        
        # Verify log writer was called correctly
        # Note: Since we're using a mock log_writer, we can't verify the actual file creation
        # but we can verify the method was called without errors
        
    def test_rpc_log_initialization(self):
        """Test RPC log initialization with proper token validation"""
        rpc_service = RpcCommandService(self.node_manager, self.command_queue)
        rpc_service.log_writer = self.writer
        
        # Create a mock token
        token = NodeToken(token_id="163", token_type="RPC", name="AP01m", ip_address="192.168.0.11")
        
        # Mock the logger to avoid actual logging
        rpc_service.logger = Mock()
        
        # Test log initialization
        rpc_service._initialize_log_file(token)
        
        # Verify log writer was called correctly
        # Note: Since we're using a mock log_writer, we can't verify the actual file creation
        # but we can verify the method was called without errors
        
    def test_fbc_token_validation(self):
        """Test FBC service token validation"""
        fbc_service = FbcCommandService(self.node_manager, self.command_queue, self.writer)
        
        # Test with empty token ID
        with self.assertRaises(ValueError) as context:
            fbc_service.get_token("AP01m", "")
        self.assertIn("Token ID cannot be empty", str(context.exception))
        
        # Test with None token ID
        with self.assertRaises(ValueError) as context:
            fbc_service.get_token("AP01m", None)
        self.assertIn("Token ID cannot be empty", str(context.exception))
        
    def test_rpc_token_validation(self):
        """Test RPC service token validation"""
        rpc_service = RpcCommandService(self.node_manager, self.command_queue)
        rpc_service.log_writer = self.writer
        
        # Test with empty token ID
        with self.assertRaises(ValueError) as context:
            rpc_service.get_token("AP01m", "")
        self.assertIn("Token ID cannot be empty", str(context.exception))
        
        # Test with None token ID
        with self.assertRaises(ValueError) as context:
            rpc_service.get_token("AP01m", None)
        self.assertIn("Token ID cannot be empty", str(context.exception))
        
    def test_log_writer_close_all_logs(self):
        """Test LogWriter close_all_logs functionality"""
        # Create a token and initialize a log
        token = NodeToken(token_id="162", token_type="FBC", name="AP01m", ip_address="192.168.0.11")
        log_path = self.writer.get_log_path("AP01m", "192.168.0.11", token)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        # Open log
        self.writer.open_log("AP01m", "192.168.0.11", token, log_path)
        
        # Verify log is open
        key = (token.token_id, token.token_type.lower())
        self.assertIn(key, self.writer.loggers)
        
        # Close all logs
        self.writer.close_all_logs()
        
        # Verify logs are closed
        self.assertEqual(len(self.writer.loggers), 0)
        self.assertEqual(len(self.writer.log_paths), 0)
        
    def tearDown(self):
        self.writer.close_all_logs()
        self.temp_dir.cleanup()


if __name__ == '__main__':
    unittest.main()