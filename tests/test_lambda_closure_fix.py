import sys
import os
import logging
import unittest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication, QMenu

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.commander.services.context_menu_service import ContextMenuService
from src.commander.models import Node, NodeToken
from src.commander.services.context_menu_filter import ContextMenuFilterService

class TestLambdaClosureFix(unittest.TestCase):
    """Test that the lambda closure fix works correctly with multiple tokens"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize QApplication for tests"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock node manager
        self.mock_node_manager = Mock()
        
        # Create mock context menu filter service
        self.mock_context_menu_filter = Mock()
        self.mock_context_menu_filter.should_show_command.return_value = True
        
        # Create the service
        self.context_menu_service = ContextMenuService(
            node_manager=self.mock_node_manager,
            context_menu_filter=self.mock_context_menu_filter
        )
        
        # Create mock presenter
        self.mock_presenter = Mock()
        self.context_menu_service.set_presenter(self.mock_presenter)
        
        # Create test node with multiple FBC tokens
        self.test_node = Node(name="AP01m", ip_address="192.168.0.11")
        
        # Add multiple FBC tokens to the node
        token162 = NodeToken(
            token_id="162",
            token_type="FBC",
            name="AP01m",
            ip_address="192.168.0.11",
            log_path="test_logs/AP01m/162_FBC.log"
        )
        token163 = NodeToken(
            token_id="163",
            token_type="FBC",
            name="AP01m",
            ip_address="192.168.0.11",
            log_path="test_logs/AP01m/163_FBC.log"
        )
        token164 = NodeToken(
            token_id="164",
            token_type="FBC",
            name="AP01m",
            ip_address="192.168.0.11",
            log_path="test_logs/AP01m/164_FBC.log"
        )
        
        self.test_node.add_token(token162)
        self.test_node.add_token(token163)
        self.test_node.add_token(token164)
        
        # Configure mock node manager to return our test node
        self.mock_node_manager.get_node.return_value = self.test_node

    def test_fbc_subgroup_lambda_closure_fix(self):
        """Test that FBC subgroup context menu properly handles multiple tokens"""
        # Create menu and item data for FBC subgroup
        menu = QMenu()
        item_data = {
            "section_type": "FBC",
            "node": "AP01m"
        }
        
        # Show context menu
        from PyQt6.QtCore import QPoint
        result = self.context_menu_service.show_context_menu(menu, item_data, QPoint(100, 100))
        
        # Verify menu was shown
        self.assertTrue(result)
        self.assertEqual(len(menu.actions()), 1)  # Should have one action
        
        # Get the action
        action = menu.actions()[0]
        self.assertIn("Print All FBC Tokens for AP01m", action.text())
        
        # Trigger the action
        action.trigger()
        
        # Verify the presenter method was called with the correct tokens
        # The fix ensures that the lambda captures the correct tokens at creation time
        self.mock_presenter.process_all_fbc_subgroup_commands.assert_called_once()
        
        # Get the argument passed to the presenter method
        call_args = self.mock_presenter.process_all_fbc_subgroup_commands.call_args
        mock_item = call_args[0][0]  # First positional argument
        
        # Verify the mock item has the correct tokens
        self.assertTrue(hasattr(mock_item, 'tokens'))
        self.assertEqual(len(mock_item.tokens), 3)
        
        # Verify token IDs
        token_ids = [token.token_id for token in mock_item.tokens]
        self.assertIn("162", token_ids)
        self.assertIn("163", token_ids)
        self.assertIn("164", token_ids)

    def test_fbc_individual_token_lambda_closure_fix(self):
        """Test that individual FBC token context menu properly handles lambda closure"""
        # Create menu and item data for individual FBC token
        menu = QMenu()
        item_data = {
            "token_type": "FBC",
            "token": "162",
            "node": "AP01m"
        }
        
        # Show context menu
        from PyQt6.QtCore import QPoint
        result = self.context_menu_service.show_context_menu(menu, item_data, QPoint(100, 100))
        
        # Verify menu was shown
        self.assertTrue(result)
        self.assertEqual(len(menu.actions()), 1)  # Should have one action
        
        # Get the action
        action = menu.actions()[0]
        self.assertIn("Print FieldBus Structure (Token 162)", action.text())
        
        # Trigger the action
        action.trigger()
        
        # Verify the presenter method was called with the correct parameters
        self.mock_presenter.process_fieldbus_command.assert_called_once_with("162", "AP01m")

    def test_rpc_subgroup_lambda_closure_fix(self):
        """Test that RPC subgroup context menu properly handles lambda closure"""
        # Add RPC tokens to the node
        rpc_token163 = NodeToken(
            token_id="163",
            token_type="RPC",
            name="AP01m",
            ip_address="192.168.0.11",
            log_path="test_logs/AP01m/163_RPC.log"
        )
        rpc_token164 = NodeToken(
            token_id="164",
            token_type="RPC",
            name="AP01m",
            ip_address="192.168.0.11",
            log_path="test_logs/AP01m/164_RPC.log"
        )
        
        self.test_node.add_token(rpc_token163)
        self.test_node.add_token(rpc_token164)
        
        # Create menu and item data for RPC subgroup
        menu = QMenu()
        item_data = {
            "section_type": "RPC",
            "node": "AP01m"
        }
        
        # Show context menu
        from PyQt6.QtCore import QPoint
        result = self.context_menu_service.show_context_menu(menu, item_data, QPoint(100, 100))
        
        # Verify menu was shown
        self.assertTrue(result)
        self.assertEqual(len(menu.actions()), 1)  # Should have one action
        
        # Get the action
        action = menu.actions()[0]
        self.assertIn("Print All RPC Tokens for AP01m", action.text())
        
        # Trigger the action
        action.trigger()
        
        # Verify the presenter method was called with the correct tokens
        self.mock_presenter.process_all_rpc_subgroup_commands.assert_called_once()
        
        # Get the argument passed to the presenter method
        call_args = self.mock_presenter.process_all_rpc_subgroup_commands.call_args
        mock_item = call_args[0][0]  # First positional argument
        
        # Verify the mock item has the correct tokens
        self.assertTrue(hasattr(mock_item, 'tokens'))
        self.assertEqual(len(mock_item.tokens), 2)
        
        # Verify token IDs
        token_ids = [token.token_id for token in mock_item.tokens]
        self.assertIn("163", token_ids)
        self.assertIn("164", token_ids)

    def test_rpc_individual_token_lambda_closure_fix(self):
        """Test that individual RPC token context menu properly handles lambda closure"""
        # Create menu and item data for individual RPC token
        menu = QMenu()
        item_data = {
            "token_type": "RPC",
            "token": "163",
            "node": "AP01m"
        }
        
        # Show context menu
        from PyQt6.QtCore import QPoint
        result = self.context_menu_service.show_context_menu(menu, item_data, QPoint(100, 100))
        
        # Verify menu was shown
        self.assertTrue(result)
        self.assertEqual(len(menu.actions()), 2)  # Should have two actions (print and clear)
        
        # Get the actions
        print_action = menu.actions()[0]
        clear_action = menu.actions()[1]
        
        self.assertIn("Print Rupi counters Token '163'", print_action.text())
        self.assertIn("Clear Rupi counters '163'", clear_action.text())
        
        # Trigger the print action
        print_action.trigger()
        
        # Verify the presenter method was called with the correct parameters
        self.mock_presenter.process_rpc_command.assert_called_with("AP01m", "163", "print")
        
        # Reset mock and trigger the clear action
        self.mock_presenter.process_rpc_command.reset_mock()
        clear_action.trigger()
        
        # Verify the presenter method was called with the correct parameters
        self.mock_presenter.process_rpc_command.assert_called_with("AP01m", "163", "clear")

if __name__ == '__main__':
    unittest.main()