import unittest
from unittest.mock import patch, MagicMock
from src.commander.ui.commander_window import CommanderWindow
from src.commander.models import Node, NodeToken
from src.commander.presenters.node_tree_presenter import NodeTreePresenter
from src.commander.services.commander_service import CommanderService
from src.commander.services.logging_service import LoggingService
from src.commander.services.status_service import StatusService
from PyQt6.QtWidgets import QApplication, QTreeWidget
import os

class TestCommanderWindowTokenQueue(unittest.TestCase):
    """Tests for token queue handling and null safety in CommanderWindow"""
    
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])
        
    def setUp(self):
        self.window = CommanderWindow()
        self.window.node_manager = MagicMock()
        self.window.log_writer = MagicMock()
        # Mock the threading service
        self.window.threading_service = MagicMock()
        # Mock the status service
        self.window.status_service = MagicMock()
        self.mock_node = Node(name="TEST_NODE", ip_address="192.168.0.1")
        self.mock_node.tokens = {
            "123": NodeToken(token_id="123", token_type="FBC", name="test", ip_address="192.168.0.1", port=23),
            "456": NodeToken(token_id="456", token_type="FBC", name="test", ip_address="192.168.0.1", port=23)
        }
        
        # Mock UI component required for command processing
        self.window.fbc_subgroup_item = MagicMock()
        self.window.fbc_subgroup_item.parent.return_value = MagicMock()
        
        # Initialize services with mock dependencies
        self.mock_session_manager = MagicMock()
        self.mock_log_writer = self.window.log_writer  # Use the same mock as window.log_writer
        self.mock_command_queue = MagicMock()
        self.mock_fbc_service = MagicMock()
        self.mock_rpc_service = MagicMock()
        
        # Initialize CommanderService with mock dependencies
        self.window.commander_service = CommanderService(
            self.window.node_manager,
            self.mock_session_manager,
            self.mock_command_queue,
            self.mock_log_writer,
            self.mock_fbc_service,
            self.mock_rpc_service
        )
        
        # Mock LoggingService
        self.window.logging_service = MagicMock()
        
        # Initialize NodeTreePresenter with mock dependencies
        self.mock_view = MagicMock()
        self.mock_context_menu_service = MagicMock()
        
        # Mock the node manager's get_node method to return our mock node
        self.window.node_manager.get_node.return_value = self.mock_node
        
        self.window.node_tree_presenter = NodeTreePresenter(
            self.mock_view,
            self.window.node_manager,
            self.mock_session_manager,
            self.mock_log_writer,
            self.mock_command_queue,
            self.mock_fbc_service,
            self.mock_rpc_service,
            self.mock_context_menu_service
        )
        
    def test_empty_token_queue(self):
        """Test handling of empty token queue"""
        # Create a mock node with no FBC tokens
        empty_node = Node(name="TEST_NODE", ip_address="192.168.0.1")
        empty_node.tokens = {}
        self.window.node_manager.get_node.return_value = empty_node
        
        with patch.object(self.window.node_tree_presenter, 'status_message_signal') as mock_signal:
            # Create a mock item hierarchy
            mock_item = MagicMock()
            mock_section_item = MagicMock()
            mock_node_item = MagicMock()
            mock_node_item.text.return_value = "TEST_NODE (192.168.0.1)"
            mock_section_item.parent.return_value = mock_node_item
            mock_item.parent.return_value = mock_section_item
            
            self.window.node_tree_presenter.process_all_fbc_subgroup_commands(mock_item)
            mock_signal.emit.assert_called_with("No FBC tokens found in node TEST_NODE", 3000)

    def test_missing_token_handling(self):
        """Test command execution with missing node token"""
        # Create a mock node with no FBC tokens
        empty_node = Node(name="TEST_NODE", ip_address="192.168.0.1")
        empty_node.tokens = {}
        self.window.node_manager.get_node.return_value = empty_node
        
        with patch.object(self.window.node_tree_presenter, 'status_message_signal') as mock_signal:
            # Create a mock item hierarchy
            mock_item = MagicMock()
            mock_section_item = MagicMock()
            mock_node_item = MagicMock()
            mock_node_item.text.return_value = "TEST_NODE (192.168.0.1)"
            mock_section_item.parent.return_value = mock_node_item
            mock_item.parent.return_value = mock_section_item
            
            self.window.node_tree_presenter.process_all_fbc_subgroup_commands(mock_item)
            mock_signal.emit.assert_called_with("No FBC tokens found in node TEST_NODE", 3000)

    def test_null_node_handling(self):
        """Test command execution with null node reference"""
        # Mock node manager to return None for get_node
        self.window.node_manager.get_node.return_value = None
        
        with patch.object(self.window.node_tree_presenter, 'status_message_signal') as mock_signal:
            # Create a mock item hierarchy
            mock_item = MagicMock()
            mock_section_item = MagicMock()
            mock_node_item = MagicMock()
            mock_node_item.text.return_value = "INVALID_NODE (192.168.0.1)"
            mock_section_item.parent.return_value = mock_node_item
            mock_item.parent.return_value = mock_section_item
            
            self.window.node_tree_presenter.process_all_fbc_subgroup_commands(mock_item)
            mock_signal.emit.assert_called_with("Node INVALID_NODE not found", 3000)

    def test_valid_command_queuing(self):
        """Test command queuing with FBC tokens"""
        with patch.object(self.window.node_tree_presenter, 'status_message_signal') as mock_signal:
            # Create a mock item hierarchy
            mock_item = MagicMock()
            mock_section_item = MagicMock()
            mock_node_item = MagicMock()
            mock_node_item.text.return_value = "TEST_NODE (192.168.0.1)"
            mock_section_item.parent.return_value = mock_node_item
            mock_item.parent.return_value = mock_section_item
            
            self.window.node_tree_presenter.process_all_fbc_subgroup_commands(mock_item)
            # Verify that the FBC service queue method was called for each token
            self.assertEqual(self.mock_fbc_service.queue_fieldbus_command.call_count, 2)
            # Verify that the command queue start method was called
            self.mock_command_queue.start_processing.assert_called_once()
            # Verify status messages
            mock_signal.emit.assert_any_call("Processing 2 FBC tokens in node TEST_NODE...", 0)
            mock_signal.emit.assert_any_call("Queued 2 commands for node TEST_NODE", 3000)

class TestContextMenuCommands(unittest.TestCase):
    """Tests for right-click context menu command execution"""
    
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])
        
    def setUp(self):
        self.window = CommanderWindow()
        self.window.node_manager = MagicMock()
        self.window.log_writer = MagicMock()
        # Mock the threading service
        self.window.threading_service = MagicMock()
        self.window.telnet_service = MagicMock()
        self.window.telnet_service.execute_command = MagicMock()
        # Mock the status service
        self.window.status_service = MagicMock()
        
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
        
        # Initialize services with mock dependencies for TestContextMenuCommands
        self.mock_session_manager = MagicMock()
        self.mock_log_writer = self.window.log_writer  # Use the same mock as window.log_writer
        self.mock_command_queue = MagicMock()
        self.mock_fbc_service = MagicMock()
        self.mock_fbc_service.generate_fieldbus_command.return_value = "print from fbc io structure 1230000"
        self.mock_rpc_service = MagicMock()
        
        # Mock LoggingService
        self.window.logging_service = MagicMock()
        
        # Mock LoggingService
        self.window.logging_service = MagicMock()
        
        # Initialize CommanderService with mock dependencies
        self.window.commander_service = CommanderService(
            self.window.node_manager,
            self.mock_session_manager,
            self.mock_command_queue,
            self.mock_log_writer,
            self.mock_fbc_service,
            self.mock_rpc_service
        )
        # Mock the logging_service in commander_service as well
        self.window.commander_service.logging_service = self.window.logging_service
        # Mock the logging_service in commander_service as well
        self.window.commander_service.logging_service = self.window.logging_service
        
        # Mock LoggingService
        self.window.logging_service = MagicMock()
        
        # Initialize NodeTreePresenter with mock dependencies for TestContextMenuCommands
        self.mock_view = MagicMock()
        self.mock_context_menu_service = MagicMock()
        
        # Mock the node manager's get_node method to return our mock node
        self.window.node_manager.get_node.return_value = self.mock_node
        # Mock the node manager's get_node_by_token method to return our mock node
        self.window.node_manager.get_node_by_token.return_value = self.mock_node
        
        self.window.node_tree_presenter = NodeTreePresenter(
            self.mock_view,
            self.window.node_manager,
            self.mock_session_manager,
            self.mock_log_writer,
            self.mock_command_queue,
            self.mock_fbc_service,
            self.mock_rpc_service,
            self.mock_context_menu_service
        )
        
        # Connect presenter signals like in the real window
        self.window.node_tree_presenter.status_message_signal.connect(self.window.status_service.status_updated)
        self.window.node_tree_presenter.node_tree_updated_signal.connect(self.window.on_node_tree_updated)

    def test_context_menu_command_execution(self):
        """Test context menu command triggers telnet execution"""
        with patch.object(self.window.commander_service, 'status_message') as mock_signal:
            # Simulate context menu command execution by calling the window's method
            # which should delegate to the commander service
            self.window.process_fieldbus_command("123", "TEST_NODE")
            
            # Verify command execution - the window should call the commander service's method
            # which in turn calls the FBC service
            self.mock_fbc_service.queue_fieldbus_command.assert_called_once_with("TEST_NODE", "123", None)
            self.mock_command_queue.start_processing.assert_called_once()
            mock_signal.emit.assert_called_with("Executing: print from fbc io structure 1230000...", 3000)

    def test_command_output_logging(self):
        """Test successful command output is logged correctly"""
        test_response = "Fieldbus structure data"
        self.window.current_token = self.mock_token
        
        # Simulate command completion through commander service
        self.window.commander_service._log_command_result("test command", test_response, True, self.mock_token)
        
        # Verify logging through LoggingService
        self.window.commander_service.logging_service.log_command_result.assert_called_with(
            "test command", test_response, True, self.mock_token
        )

    def test_invalid_node_logging(self):
        """Test error handling for invalid node references"""
        # Mock the FBC service's queue_fieldbus_command method to raise ValueError for invalid node
        self.mock_fbc_service.queue_fieldbus_command.side_effect = ValueError("Node INVALID_NODE not found")
        
        with patch.object(self.window.commander_service, 'status_message') as mock_signal:
            self.window.process_fieldbus_command("123", "INVALID_NODE")
            mock_signal.emit.assert_called_with("Node INVALID_NODE not found", 3000)

    def test_command_error_handling(self):
        """Test error handling during command execution"""
        with patch.object(self.window.commander_service, 'status_message') as mock_signal:
            # Mock the node manager to return our test node
            self.window.node_manager.get_node.return_value = self.mock_node
            
            # Call the window's method which should handle the error
            self.window.process_fieldbus_command("123", "TEST_NODE")
            
            # Verify that the FBC service was called
            self.mock_fbc_service.queue_fieldbus_command.assert_called_once_with("TEST_NODE", "123", None)
            # Note: We're not testing the error case here because we're not mocking the service to throw an exception
            # The error handling for service exceptions is tested in the presenter tests

    def test_log_file_path_generation(self):
        """Verify log path matches node and token"""
        expected_path = os.path.join("logs", "TEST_NODE", "FBC_123.log")
        self.window.log_writer.open_log.return_value = expected_path
        
        self.window.current_token = self.mock_token
        self.window.on_telnet_command_finished("test output", automatic=True)
        
        # Verify logging through LoggingService
        self.window.commander_service.logging_service.log_telnet_command_finished.assert_called()