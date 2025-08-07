import unittest
from unittest.mock import Mock, patch
from src.commander.services.context_menu_service import ContextMenuService
from src.commander.models import NodeToken
from src.commander.services.context_menu_filter import ContextMenuFilter
from PyQt6.QtWidgets import QMenu


class TestContextMenuService(unittest.TestCase):
    """Tests for ContextMenuService functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_window = Mock()
        self.mock_window.commander = Mock()
        self.mock_window.commander.command_queue = Mock()
        self.mock_window.commander.node_manager = Mock()
        self.mock_window.commander.sequential_processor = Mock()
        
        # Create service with mock dependencies
        self.context_menu_service = ContextMenuService(self.mock_window)
        
        # Mock logger to avoid actual logging
        self.context_menu_service.logger = Mock()

    def test_create_fbc_token_menu(self):
        """Test creating context menu for FBC tokens"""
        # Create test token
        token = NodeToken(
            token_id="162",
            token_type="FBC",
            name="AP01m",
            ip_address="192.168.0.11"
        )
        
        # Create menu
        menu = self.context_menu_service.create_token_context_menu([token])
        
        # Verify menu structure
        self.assertIsInstance(menu, QMenu)
        self.assertTrue(any("Process FBC" in action.text() for action in menu.actions()))
        self.assertTrue(any("Copy Token ID" in action.text() for action in menu.actions()))
        self.assertTrue(any("View Log" in action.text() for action in menu.actions()))

    def test_create_rpc_token_menu(self):
        """Test creating context menu for RPC tokens"""
        # Create test token
        token = NodeToken(
            token_id="163",
            token_type="RPC",
            name="AP01m",
            ip_address="192.168.0.11"
        )
        
        # Create menu
        menu = self.context_menu_service.create_token_context_menu([token])
        
        # Verify menu structure
        self.assertIsInstance(menu, QMenu)
        self.assertTrue(any("Process RPC" in action.text() for action in menu.actions()))
        self.assertTrue(any("Print" in action.text() for action in menu.actions()))
        self.assertTrue(any("Clear" in action.text() for action in menu.actions()))
        self.assertTrue(any("Copy Token ID" in action.text() for action in menu.actions()))

    def test_create_multiple_token_menu(self):
        """Test creating context menu for multiple tokens"""
        # Create test tokens
        tokens = [
            NodeToken(token_id="162", token_type="FBC"),
            NodeToken(token_id="163", token_type="RPC")
        ]
        
        # Create menu
        menu = self.context_menu_service.create_token_context_menu(tokens)
        
        # Verify menu structure
        self.assertIsInstance(menu, QMenu)
        self.assertTrue(any("Process Selected Tokens" in action.text() for action in menu.actions()))
        self.assertTrue(any("Process FBC Tokens" in action.text() for action in menu.actions()))
        self.assertTrue(any("Process RPC Tokens" in action.text() for action in menu.actions()))

    def test_parameter_passing_for_single_token(self):
        """Test parameter passing for single token processing"""
        # Create test token
        token = NodeToken(
            token_id="162",
            token_type="FBC",
            name="AP01m",
            ip_address="192.168.0.11"
        )
        
        # Mock the sequential processor
        self.mock_window.commander.sequential_processor.process_tokens_sequentially = Mock()
        
        # Create and trigger menu action
        menu = self.context_menu_service.create_token_context_menu([token])
        process_action = next(action for action in menu.actions() if "Process FBC" in action.text())
        process_action.trigger()
        
        # Verify parameters passed correctly
        self.mock_window.commander.sequential_processor.process_tokens_sequentially.assert_called_once_with(
            node_name="AP01m",
            tokens=[token],
            action="print"
        )

    def test_parameter_passing_for_multiple_tokens(self):
        """Test parameter passing for multiple token processing"""
        # Create test tokens
        tokens = [
            NodeToken(token_id="162", token_type="FBC", name="AP01m"),
            NodeToken(token_id="163", token_type="RPC", name="AP01m")
        ]
        
        # Mock the sequential processor
        self.mock_window.commander.sequential_processor.process_tokens_sequentially = Mock()
        
        # Create and trigger menu action
        menu = self.context_menu_service.create_token_context_menu(tokens)
        process_action = next(action for action in menu.actions() if "Process Selected Tokens" in action.text())
        process_action.trigger()
        
        # Verify parameters passed correctly
        self.mock_window.commander.sequential_processor.process_tokens_sequentially.assert_called_once_with(
            node_name="AP01m",
            tokens=tokens,
            action="print"
        )

    def test_filter_application_for_fbc_tokens(self):
        """Test context menu filter application for FBC tokens"""
        # Create test token
        token = NodeToken(token_id="162", token_type="FBC")
        
        # Create filter mock
        with patch.object(ContextMenuFilter, 'filter_actions') as mock_filter:
            mock_filter.return_value = ["Process FBC", "Copy Token ID"]
            
            # Create menu
            menu = self.context_menu_service.create_token_context_menu([token])
            
            # Verify filter was applied
            mock_filter.assert_called_once_with(
                ["Process FBC", "Copy Token ID", "View Log"],
                token_type="FBC",
                is_multiple=False
            )
            
            # Verify filtered actions are present
            self.assertTrue(any("Process FBC" in action.text() for action in menu.actions()))
            self.assertTrue(any("Copy Token ID" in action.text() for action in menu.actions()))
            self.assertFalse(any("Process RPC" in action.text() for action in menu.actions()))

    def test_filter_application_for_rpc_tokens(self):
        """Test context menu filter application for RPC tokens"""
        # Create test token
        token = NodeToken(token_id="163", token_type="RPC")
        
        # Create filter mock
        with patch.object(ContextMenuFilter, 'filter_actions') as mock_filter:
            mock_filter.return_value = ["Process RPC", "Print", "Clear", "Copy Token ID"]
            
            # Create menu
            menu = self.context_menu_service.create_token_context_menu([token])
            
            # Verify filter was applied
            mock_filter.assert_called_once_with(
                ["Process RPC", "Print", "Clear", "Copy Token ID", "View Log"],
                token_type="RPC",
                is_multiple=False
            )
            
            # Verify filtered actions are present
            self.assertTrue(any("Process RPC" in action.text() for action in menu.actions()))
            self.assertTrue(any("Print" in action.text() for action in menu.actions()))
            self.assertTrue(any("Clear" in action.text() for action in menu.actions()))
            self.assertTrue(any("Copy Token ID" in action.text() for action in menu.actions()))

    def test_filter_application_for_multiple_tokens(self):
        """Test context menu filter application for multiple tokens"""
        # Create test tokens
        tokens = [
            NodeToken(token_id="162", token_type="FBC"),
            NodeToken(token_id="163", token_type="RPC")
        ]
        
        # Create filter mock
        with patch.object(ContextMenuFilter, 'filter_actions') as mock_filter:
            mock_filter.return_value = ["Process Selected Tokens", "Process FBC Tokens", "Process RPC Tokens"]
            
            # Create menu
            menu = self.context_menu_service.create_token_context_menu(tokens)
            
            # Verify filter was applied
            mock_filter.assert_called_once_with(
                ["Process Selected Tokens", "Process FBC Tokens", "Process RPC Tokens", "Copy Token IDs"],
                token_type=None,
                is_multiple=True
            )
            
            # Verify filtered actions are present
            self.assertTrue(any("Process Selected Tokens" in action.text() for action in menu.actions()))
            self.assertTrue(any("Process FBC Tokens" in action.text() for action in menu.actions()))
            self.assertTrue(any("Process RPC Tokens" in action.text() for action in menu.actions()))

    def test_error_handling_invalid_token(self):
        """Test error handling with invalid token data"""
        # Create invalid token (missing required attributes)
        invalid_token = NodeToken(token_id="invalid")
        
        # Mock logger to verify error logging
        self.context_menu_service.logger.error = Mock()
        
        # Create menu with invalid token
        menu = self.context_menu_service.create_token_context_menu([invalid_token])
        
        # Verify error was logged
        self.context_menu_service.logger.error.assert_called_once_with(
            "Error creating context menu: Token missing required attributes"
        )
        
        # Verify fallback menu was created
        self.assertIsInstance(menu, QMenu)
        self.assertTrue(any("Copy Token ID" in action.text() for action in menu.actions()))

    def test_ui_feedback_for_token_processing(self):
        """Test UI feedback during token processing"""
        # Create test token
        token = NodeToken(
            token_id="162",
            token_type="FBC",
            name="AP01m",
            ip_address="192.168.0.11"
        )
        
        # Mock UI components
        self.mock_window.statusBar = Mock()
        self.mock_window.statusBar().showMessage = Mock()
        
        # Create and trigger menu action
        menu = self.context_menu_service.create_token_context_menu([token])
        process_action = next(action for action in menu.actions() if "Process FBC" in action.text())
        process_action.trigger()
        
        # Verify UI feedback
        self.mock_window.statusBar().showMessage.assert_any_call("Processing token 162...", 3000)
        self.mock_window.statusBar().showMessage.assert_any_call("Token processing completed", 3000)


if __name__ == '__main__':
    unittest.main()