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
            "123": NodeToken(token_id="123", token_type="FBC", name="test", ip_address="192.168.0.1", port=23),
            "456": NodeToken(token_id="456", token_type="FBC", name="test", ip_address="192.168.0.1", port=23)
        }
        # Mock UI component required for command processing
        self.window.fbc_subgroup_item = MagicMock()
        self.window.fbc_subgroup_item.parent.return_value = MagicMock()
        
    def test_empty_token_queue(self):
        """Test handling of empty token queue"""
        with patch.object(self.window, 'status_message_signal') as mock_signal:
            self.window.process_all_fbc_subgroup_commands(MagicMock())
            mock_signal.assert_called_with("No FBC tokens found in node TEST_NODE", 3000)

    def test_invalid_token_format(self):
        """Test token ID validation"""
        invalid_token = NodeToken(token_id="12A", token_type="FBC", name="test", ip_address="192.168.0.1", port=23)
        self.mock_node.tokens = {"12A": invalid_token}
        
        with patch.object(self.window, 'status_message_signal') as mock_signal:
            self.window.process_all_fbc_subgroup_commands(MagicMock())
            mock_signal.assert_called_with("Invalid token ID format: 12A. Must be 3 digits. Skipping.", 3000)

    def test_concurrent_queue_access(self):
        """Test thread-safe queue operations"""
        test_tokens = [NodeToken(token_id=str(i), token_type="FBC", name="test", ip_address="192.168.0.1", port=23) for i in range(100)]
        self.mock_node.tokens = {t.token_id: t for t in test_tokens}
        
        def mock_process_command(token_id):
            with self.window.telnet_lock:
                return f"Processed {token_id}"

        with patch('threading.Timer') as mock_timer:
            self.window.process_all_fbc_subgroup_commands(MagicMock())
            self.assertEqual(mock_timer.call_count, len(test_tokens))

    def test_token_processing_order(self):
        """Verify FIFO processing order"""
        tokens = [NodeToken(token_id=str(i), token_type="FBC", name="test", ip_address="192.168.0.1", port=23) for i in range(3)]
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

    def test_null_node_handling(self):
        """Test command execution with null node reference"""
        with patch.object(self.window, 'status_message_signal') as mock_signal:
            self.window.process_all_fbc_subgroup_commands(None)
            mock_signal.assert_called_with(
                "Invalid node reference provided",
                3000
            )

    def test_null_token_handling(self):
        """Test command execution with null token in node"""
        self.mock_node.tokens = {"123": None}
        
        with patch.object(self.window, 'status_message_signal') as mock_signal:
            self.window.process_all_fbc_subgroup_commands(MagicMock())
            mock_signal.assert_called_with(
                "Invalid FBC token 123 in node TEST_NODE",
                3000
            )

    def test_valid_command_queuing(self):
        """Test command queuing with QSignalSpy validation"""
        from PyQt6.QtTest import QSignalSpy
        from PyQt6.QtCore import QTimer
        
        valid_token = NodeToken(token_id="123", token_type="FBC")
        self.mock_node.tokens = {"123": valid_token}
        
        # Setup signal spy
        spy = QSignalSpy(self.window.command_finished)
        
        # Execute processing
        self.window.process_all_fbc_subgroup_commands(MagicMock())
        
        # Process events and wait for signals
        QTimer.singleShot(100, self.app.quit)
        self.app.exec()
        
        self.assertEqual(len(spy), 1)
        response, automatic = spy[0]
        self.assertIn("fieldbus structure", response)

if __name__ == '__main__':
    unittest.main()

class TestContextMenuCommands(unittest.TestCase):
    """Tests for right-click context menu command execution"""
    
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])
        
    def setUp(self):
        self.window = CommanderWindow()
        self.window.node_manager = MagicMock()
        self.window.log_writer = MagicMock()
        self.window.execute_telnet_command = MagicMock()
        
        # Setup test node with FBC token
        self.mock_node = Node(name="TEST_NODE", ip_address="192.168.0.1")
        self.mock_token = NodeToken(token_id="123", token_type="FBC",
                                  name="test", ip_address="192.168.0.1", port=23)
        self.mock_node.tokens = {"123": self.mock_token}
        
        # Mock UI components
        self.mock_item = MagicMock()
        self.mock_item.data.return_value = {
            "token": "123",
            "node": "TEST_NODE",
            "token_type": "FBC"
        }

    def test_context_menu_command_execution(self):
        """Test context menu command triggers telnet execution"""
        with patch.object(self.window, 'status_message_signal') as mock_signal:
            # Simulate context menu command execution
            self.window.process_fieldbus_command("123", "TEST_NODE")
            
            # Verify command execution
            self.window.execute_telnet_command.assert_called_once()
            mock_signal.assert_called_with("Executing: print from fieldbus io structure 1230000...", 3000)

    def test_command_output_logging(self):
        """Test successful command output is logged correctly"""
        test_response = "Fieldbus structure data"
        self.window.current_token = self.mock_token
        
        # Simulate command completion
        self.window.on_telnet_command_finished(test_response, automatic=True)
        
        # Verify logging
        self.window.log_writer.append_to_log.assert_called_with(
            "123", test_response, source="telnet"
        )

    def test_invalid_node_logging(self):
        """Test error handling for invalid node references"""
        with patch.object(self.window.node_manager, 'get_node', return_value=None):
            with patch.object(self.window, 'status_message_signal') as mock_signal:
                self.window.process_fieldbus_command("123", "INVALID_NODE")
                mock_signal.assert_called_with("Node INVALID_NODE not found", 3000)

    def test_command_error_handling(self):
        """Test error handling during command execution"""
        with patch.object(self.window, 'execute_telnet_command',
                        side_effect=Exception("Connection failed")):
            with patch.object(self.window, 'status_message_signal') as mock_signal:
                self.window.process_fieldbus_command("123", "TEST_NODE")
                mock_signal.assert_called_with("Error: Connection failed", 3000)

    def test_log_file_path_generation(self):
        """Verify log path matches node and token"""
        expected_path = os.path.join("logs", "TEST_NODE", "FBC_123.log")
        self.window.log_writer.open_log.return_value = expected_path
        
        self.window.current_token = self.mock_token
        self.window.on_telnet_command_finished("test output", automatic=True)
        
        self.window.log_writer.open_log.assert_called_with(
            "TEST_NODE", "192-168-0-1", self.mock_token
        )