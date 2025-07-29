import unittest
from unittest.mock import Mock, patch
from src.commander.services.rpc_command_service import RpcCommandService
from src.commander.models import NodeToken
from src.commander.node_manager import NodeManager
from src.commander.command_queue import CommandQueue


class TestRpcCommandService(unittest.TestCase):
    """Tests for RpcCommandService functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.node_manager = NodeManager()
        self.command_queue = CommandQueue()
        self.rpc_service = RpcCommandService(self.node_manager, self.command_queue)

    def test_generate_rpc_command_print(self):
        """Test generating print RPC command with correct 7-digit format"""
        # Test with numeric token
        command = self.rpc_service.generate_rpc_command("162", "print")
        self.assertEqual(command, "print from fbc rupi counters 1620000")
        
        # Test with alphanumeric token
        command = self.rpc_service.generate_rpc_command("2a2", "print")
        self.assertEqual(command, "print from fbc rupi counters 2a20000")

    def test_generate_rpc_command_clear(self):
        """Test generating clear RPC command with correct 7-digit format"""
        # Test with numeric token
        command = self.rpc_service.generate_rpc_command("163", "clear")
        self.assertEqual(command, "clear fbc rupi counters 1630000")
        
        # Test with alphanumeric token
        command = self.rpc_service.generate_rpc_command("3a3", "clear")
        self.assertEqual(command, "clear fbc rupi counters 3a30000")

    def test_normalize_token(self):
        """Test token normalization to 3-digit format"""
        # Test single digit token
        normalized = self.rpc_service.normalize_token("1")
        self.assertEqual(normalized, "001")
        
        # Test two digit token
        normalized = self.rpc_service.normalize_token("12")
        self.assertEqual(normalized, "012")
        
        # Test three digit token
        normalized = self.rpc_service.normalize_token("123")
        self.assertEqual(normalized, "123")
        
        # Test alphanumeric token (should not be zero-padded)
        normalized = self.rpc_service.normalize_token("2a2")
        self.assertEqual(normalized, "2a2")

    @patch('src.commander.services.rpc_command_service.NodeManager')
    def test_queue_rpc_command_integration(self, mock_node_manager):
        """Test queuing RPC command integration with proper formatting"""
        # Set up mock node manager
        mock_node = Mock()
        mock_node.tokens = {
            "162": NodeToken(
                token_id="162",
                token_type="RPC",
                name="AP01m",
                ip_address="192.168.0.11",
                port=2077
            )
        }
        mock_node_manager.get_node.return_value = mock_node
        
        # Create service with mock
        rpc_service = RpcCommandService(mock_node_manager, self.command_queue)
        
        # Mock the logger to avoid actual logging
        rpc_service.logger = Mock()
        
        # Mock UI signals
        rpc_service.set_command_text = Mock()
        rpc_service.switch_to_telnet_tab = Mock()
        rpc_service.focus_command_input = Mock()
        rpc_service.status_message = Mock()
        rpc_service.report_error = Mock()
        
        # Mock parent for log writer access
        from PyQt6.QtCore import QObject
        mock_parent = Mock(spec=QObject)
        mock_parent.log_writer = Mock()
        rpc_service.setParent(mock_parent)
        
        # Test queuing a command
        rpc_service.queue_rpc_command("AP01m", "162", "print")
        
        # Verify the command text was set with correct format
        expected_command = "print from fbc rupi counters 1620000"
        rpc_service.set_command_text.emit.assert_called_with(expected_command)


if __name__ == '__main__':
    unittest.main()