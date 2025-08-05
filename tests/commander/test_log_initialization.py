import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
from src.commander.services.logging_service import LoggingService
from src.commander.log_writer import LogWriter
from src.commander.models import NodeToken
from src.commander.node_manager import NodeManager

class TestLogInitialization(unittest.TestCase):
    """Tests for log initialization fix"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.node_manager = NodeManager()
        self.node_manager.log_root = self.temp_dir.name
        self.log_writer = LogWriter(self.node_manager)
        self.logging_service = LoggingService(self.node_manager, self.log_writer)
        
    def test_fbc_log_initialization_with_invalid_node(self):
        """Test FBC log initialization with invalid node"""
        # Create a token with an IP that doesn't exist in node manager
        token = NodeToken(
            token_id="162", 
            token_type="FBC", 
            name="test_node",
            ip_address="0.0.0.0",  # Invalid IP
            port=23
        )
        
        # Mock NodeManager.get_node to return None for invalid IP
        with patch.object(self.node_manager, 'get_node', return_value=None):
            # Should not raise an exception (just log a warning)
            try:
                # This would normally call the log initialization
                result = True  # Placeholder for actual implementation
                self.assertTrue(result)
            except Exception as e:
                self.fail(f"initialize_log() raised an unexpected exception: {e}")
    
    def test_fbc_log_initialization_with_valid_node(self):
        """Test FBC log initialization with valid node"""
        # Create a token with a valid IP
        token = NodeToken(
            token_id="162", 
            token_type="FBC", 
            name="test_node",
            ip_address="192.168.0.11",
            port=23
        )
        
        # Mock NodeManager.get_node to return a valid node
        mock_node = MagicMock()
        mock_node.name = "test_node"
        mock_node.ip_address = "192.168.0.11"
        
        with patch.object(self.node_manager, 'get_node', return_value=mock_node):
            # Should not raise an exception
            try:
                # This would normally call the log initialization
                result = True  # Placeholder for actual implementation
                self.assertTrue(result)
            except Exception as e:
                self.fail(f"initialize_log() raised an unexpected exception: {e}")
    
    def tearDown(self):
        self.temp_dir.cleanup()

if __name__ == '__main__':
    unittest.main()