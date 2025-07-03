import unittest
from unittest.mock import patch, MagicMock
from src.commander.commander_window import CommanderWindow
from src.commander.models import Node, NodeToken
from PyQt6.QtWidgets import QApplication
import threading

class TestCommanderWindowTokenQueue(unittest.TestCase):
    """Tests for token queue handling and null safety in CommanderWindow"""
    
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])
        
    def setUp(self):
        self.window = CommanderWindow()
        self.window.node_manager = MagicMock()
        self.mock_node = Node(name="TEST_NODE", ip_address="192.168.0.1")
        self.mock_node.tokens = {
            "123": NodeToken(token_id="123", token_type="FBC"),
            "456": NodeToken(token_id="456", token_type="FBC")
        }
        
    def test_empty_token_queue(self):
        """Test handling of empty token queue"""
        with patch.object(self.window, 'status_message_signal') as mock_signal:
            self.window.process_all_fbc_subgroup_commands(MagicMock())
            mock_signal.assert_called_with("No FBC tokens found in node TEST_NODE", 3000)

    def test_invalid_token_format(self):
        """Test token ID validation"""
        invalid_token = NodeToken(token_id="12A", token_type="FBC")
        self.mock_node.tokens = {"12A": invalid_token}
        
        with patch.object(self.window, 'status_message_signal') as mock_signal:
            self.window.process_all_fbc_subgroup_commands(MagicMock())
            mock_signal.assert_called_with("Invalid token ID format: 12A. Must be 3 digits. Skipping.", 3000)

    def test_concurrent_queue_access(self):
        """Test thread-safe queue operations"""
        test_tokens = [NodeToken(token_id=str(i), token_type="FBC") for i in range(100)]
        self.mock_node.tokens = {t.token_id: t for t in test_tokens}
        
        def mock_process_command(token_id):
            with self.window.telnet_lock:
                return f"Processed {token_id}"

        with patch('threading.Timer') as mock_timer:
            self.window.process_all_fbc_subgroup_commands(MagicMock())
            self.assertEqual(mock_timer.call_count, len(test_tokens))

    def test_token_processing_order(self):
        """Verify FIFO processing order"""
        tokens = [NodeToken(token_id=str(i), token_type="FBC") for i in range(3)]
        self.mock_node.tokens = {t.token_id: t for t in tokens}
        
        processing_order = []
        original_method = self.window.process_fieldbus_command
        
        def tracked_method(token_id):
            processing_order.append(token_id)
            original_method(token_id)
            
        with patch.object(self.window, 'process_fieldbus_command', new=tracked_method):
            self.window.process_all_fbc_subgroup_commands(MagicMock())
            self.assertEqual(processing_order, ["0", "1", "2"])

    @patch('src.commander.commander_window.threading.Thread')
    def test_error_handling_in_queue(self, mock_thread):
        """Test error recovery in token processing"""
        error_token = NodeToken(token_id="999", token_type="FBC")
        self.mock_node.tokens = {"999": error_token}
        
        with patch.object(self.window, 'process_fieldbus_command', side_effect=Exception("Test error")):
            with patch.object(self.window, 'status_message_signal') as mock_signal:
                self.window.process_all_fbc_subgroup_commands(MagicMock())
                mock_signal.assert_called_with("Error processing token 999: Test error", 3000)

    def test_missing_token_handling(self):
        """Test command execution with missing node token"""
        self.mock_node.tokens = {}
        
        with patch.object(self.window, 'status_message_signal') as mock_signal:
            self.window.process_all_fbc_subgroup_commands(MagicMock())
            mock_signal.assert_called_with(
                "No FBC tokens found in node TEST_NODE",
                3000
            )

    def test_valid_token_processing(self):
        """Test successful command execution with valid token"""
        valid_token = NodeToken(token_id="123", token_type="FBC")
        self.mock_node.tokens = {"123": valid_token}
        
        with patch('src.commander.telnet_client.TelnetClient.execute_command') as mock_exec:
            self.window.process_all_fbc_subgroup_commands(MagicMock())
            mock_exec.assert_called_once_with(
                "print all fieldbuses",
                ip="192.168.0.1",
                token="123"
            )

if __name__ == '__main__':
    unittest.main()