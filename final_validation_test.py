#!/usr/bin/env python3
"""
Final validation test for FBC token menu improvements.
This test validates:
1. Right-click context menu shows all FBC tokens individually (162, 163, 164 for AP01m)
2. "Print All" option remains available with correct token count
3. RPC token handling remains unchanged
4. Subgroup labels display correct token counts
5. No regressions in other menu functionality
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class TestFBCMenuValidation(unittest.TestCase):
    """Test FBC token menu improvements validation"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock PyQt6 imports to avoid dependency issues
        sys.modules['PyQt6'] = Mock()
        sys.modules['PyQt6.QtGui'] = Mock()
        sys.modules['PyQt6.QtWidgets'] = Mock()
        sys.modules['PyQt6.QtCore'] = Mock()
        
        # Now we can import the actual modules
        from commander.services.context_menu_service import ContextMenuService
        from commander.services.context_menu_filter import ContextMenuFilterService
        from commander.models import NodeToken
        from commander.node_manager import NodeManager
        
        # Create mocks
        self.mock_node_manager = Mock(spec=NodeManager)
        self.mock_context_menu_filter = Mock(spec=ContextMenuFilterService)
        
        # Create service instance
        self.context_menu_service = ContextMenuService(
            node_manager=self.mock_node_manager,
            context_menu_filter=self.mock_context_menu_filter
        )
        
        # Mock presenter
        self.mock_presenter = Mock()
        self.context_menu_service.set_presenter(self.mock_presenter)
        
        # Create test tokens for AP01m
        self.ap01m_tokens = [
            NodeToken(token_id="162", token_type="FBC", name="AP01m", ip_address="192.168.0.11"),
            NodeToken(token_id="163", token_type="FBC", name="AP01m", ip_address="192.168.0.11"),
            NodeToken(token_id="164", token_type="FBC", name="AP01m", ip_address="192.168.0.11")
        ]
        
        # Create RPC tokens for comparison
        self.rpc_tokens = [
            NodeToken(token_id="163", token_type="RPC", name="AP01m", ip_address="192.168.0.11"),
            NodeToken(token_id="164", token_type="RPC", name="AP01m", ip_address="192.168.0.11")
        ]
    
    def test_ap01m_fbc_tokens_individual_display(self):
        """Test that AP01m FBC tokens are displayed individually in context menu"""
        # Mock node manager to return our test tokens
        mock_node = Mock()
        mock_node.tokens = {str(i): token for i, token in enumerate(self.ap01m_tokens)}
        self.mock_node_manager.get_node.return_value = mock_node
        
        # Mock context menu filter to allow all commands
        self.mock_context_menu_filter.should_show_command.return_value = True
        
        # Create mock menu
        mock_menu = Mock()
        
        # Test FBC subgroup context menu
        item_data = {
            "section_type": "FBC",
            "node": "AP01m"
        }
        
        # Mock get_node_tokens to return our test tokens
        self.context_menu_service.get_node_tokens = Mock(return_value=self.ap01m_tokens)
        
        # Call show_context_menu
        result = self.context_menu_service.show_context_menu(mock_menu, item_data, None)
        
        # Verify that individual actions were created for each token
        expected_calls = [
            unittest.mock.call(f"FBC: {token.token_id}"),
            unittest.mock.call().triggered.connect(unittest.mock.ANY)
        ] * len(self.ap01m_tokens)
        
        # Check that actions were added to menu
        self.assertTrue(mock_menu.addAction.called)
        
        # Verify the correct number of individual token actions
        # We expect 3 individual actions (one for each token) + 1 "Print All" action
        # Plus separators
        print(f"Menu addAction called {mock_menu.addAction.call_count} times")
        
        # Check that we have individual actions for each token
        action_texts = []
        for call in mock_menu.addAction.call_args_list:
            if call and call[0]:
                action_texts.append(str(call[0][0]))
        
        print(f"Action texts: {action_texts}")
        
        # Verify individual token actions exist
        for token in self.ap01m_tokens:
            self.assertTrue(any(f"FBC: {token.token_id}" in text for text in action_texts),
                          f"Individual action for token {token.token_id} not found")
        
        print("✓ Individual FBC token actions are displayed correctly")
    
    def test_print_all_option_with_correct_count(self):
        """Test that 'Print All' option remains available with correct token count"""
        # Mock node manager to return our test tokens
        mock_node = Mock()
        mock_node.tokens = {str(i): token for i, token in enumerate(self.ap01m_tokens)}
        self.mock_node_manager.get_node.return_value = mock_node
        
        # Mock context menu filter to allow all commands
        self.mock_context_menu_filter.should_show_command.return_value = True
        
        # Create mock menu
        mock_menu = Mock()
        
        # Test FBC subgroup context menu
        item_data = {
            "section_type": "FBC",
            "node": "AP01m"
        }
        
        # Mock get_node_tokens to return our test tokens
        self.context_menu_service.get_node_tokens = Mock(return_value=self.ap01m_tokens)
        
        # Call show_context_menu
        result = self.context_menu_service.show_context_menu(mock_menu, item_data, None)
        
        # Check action texts
        action_texts = []
        for call in mock_menu.addAction.call_args_list:
            if call and call[0]:
                action_texts.append(str(call[0][0]))
        
        # Verify "Print All" action exists with correct count
        print_all_action_found = False
        for text in action_texts:
            if "Print All FBC Tokens" in text and "(3)" in text:
                print_all_action_found = True
                break
        
        self.assertTrue(print_all_action_found,
                       f"'Print All' action with correct count not found. Actions: {action_texts}")
        print("✓ 'Print All' option available with correct token count")
    
    def test_rpc_token_handling_unchanged(self):
        """Test that RPC token handling remains unchanged"""
        # Mock node manager to return our test tokens
        mock_node = Mock()
        mock_node.tokens = {str(i): token for i, token in enumerate(self.rpc_tokens)}
        self.mock_node_manager.get_node.return_value = mock_node
        
        # Mock context menu filter to allow all commands
        self.mock_context_menu_filter.should_show_command.return_value = True
        
        # Create mock menu
        mock_menu = Mock()
        
        # Test RPC subgroup context menu
        item_data = {
            "section_type": "RPC",
            "node": "AP01m"
        }
        
        # Mock get_node_tokens to return our test tokens
        self.context_menu_service.get_node_tokens = Mock(return_value=self.rpc_tokens)
        
        # Call show_context_menu
        result = self.context_menu_service.show_context_menu(mock_menu, item_data, None)
        
        # Check action texts
        action_texts = []
        for call in mock_menu.addAction.call_args_list:
            if call and call[0]:
                action_texts.append(str(call[0][0]))
        
        print(f"RPC action texts: {action_texts}")
        
        # For RPC, we expect a single "Print All" action, not individual actions
        individual_actions = [text for text in action_texts if "RPC:" in text]
        print_all_actions = [text for text in action_texts if "Print All RPC Tokens" in text]
        
        # Should have no individual actions for RPC
        self.assertEqual(len(individual_actions), 0,
                        f"RPC should not have individual actions, but found: {individual_actions}")
        
        # Should have one "Print All" action
        self.assertEqual(len(print_all_actions), 1,
                        f"RPC should have one 'Print All' action, but found: {print_all_actions}")
        
        print("✓ RPC token handling remains unchanged")
    
    def test_subgroup_labels_display_correct_counts(self):
        """Test that subgroup labels display correct token counts"""
        # Test FBC subgroup
        mock_node = Mock()
        mock_node.tokens = {str(i): token for i, token in enumerate(self.ap01m_tokens)}
        self.mock_node_manager.get_node.return_value = mock_node
        
        # Mock context menu filter to allow all commands
        self.mock_context_menu_filter.should_show_command.return_value = True
        
        # Create mock menu
        mock_menu = Mock()
        
        # Test FBC subgroup context menu
        item_data = {
            "section_type": "FBC",
            "node": "AP01m"
        }
        
        # Mock get_node_tokens to return our test tokens
        self.context_menu_service.get_node_tokens = Mock(return_value=self.ap01m_tokens)
        
        # Call show_context_menu
        result = self.context_menu_service.show_context_menu(mock_menu, item_data, None)
        
        # Check action texts
        action_texts = []
        for call in mock_menu.addAction.call_args_list:
            if call and call[0]:
                action_texts.append(str(call[0][0]))
        
        # Verify "Print All" action has correct count
        print_all_action_found = False
        for text in action_texts:
            if "Print All FBC Tokens" in text and "(3)" in text:
                print_all_action_found = True
                break
        
        self.assertTrue(print_all_action_found,
                       f"FBC subgroup label doesn't show correct count. Actions: {action_texts}")
        
        # Test RPC subgroup
        mock_node.tokens = {str(i): token for i, token in enumerate(self.rpc_tokens)}
        self.mock_node_manager.get_node.return_value = mock_node
        self.context_menu_service.get_node_tokens = Mock(return_value=self.rpc_tokens)
        
        # Clear previous calls
        mock_menu.addAction.reset_mock()
        
        # Test RPC subgroup context menu
        item_data = {
            "section_type": "RPC",
            "node": "AP01m"
        }
        
        # Call show_context_menu
        result = self.context_menu_service.show_context_menu(mock_menu, item_data, None)
        
        # Check action texts
        action_texts = []
        for call in mock_menu.addAction.call_args_list:
            if call and call[0]:
                action_texts.append(str(call[0][0]))
        
        # Verify "Print All" action has correct count
        print_all_action_found = False
        for text in action_texts:
            if "Print All RPC Tokens" in text and "AP01m" in text:
                print_all_action_found = True
                break
        
        self.assertTrue(print_all_action_found,
                       f"RPC subgroup label doesn't show correct information. Actions: {action_texts}")
        
        print("✓ Subgroup labels display correct token counts")
    
    def test_no_regressions_in_other_menu_functionality(self):
        """Test that there are no regressions in other menu functionality"""
        # Test individual token context menu (not subgroup)
        mock_menu = Mock()
        
        # Mock context menu filter to allow all commands
        self.mock_context_menu_filter.should_show_command.return_value = True
        
        # Test individual FBC token context menu
        item_data = {
            "token_type": "FBC",
            "token": "162",
            "node": "AP01m"
        }
        
        # Call show_context_menu
        result = self.context_menu_service.show_context_menu(mock_menu, item_data, None)
        
        # Check that actions were added
        self.assertTrue(mock_menu.addAction.called,
                       "Individual FBC token context menu not working")
        
        # Test individual RPC token context menu
        mock_menu.addAction.reset_mock()
        item_data = {
            "token_type": "RPC",
            "token": "163",
            "node": "AP01m"
        }
        
        # Call show_context_menu
        result = self.context_menu_service.show_context_menu(mock_menu, item_data, None)
        
        # Check that actions were added
        self.assertTrue(mock_menu.addAction.called,
                       "Individual RPC token context menu not working")
        
        print("✓ No regressions in other menu functionality")

def main():
    """Run the validation tests"""
    print("Running FBC Token Menu Improvements Validation Tests")
    print("=" * 55)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFBCMenuValidation)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 55)
    print("VALIDATION SUMMARY")
    print("=" * 55)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✓ ALL VALIDATION TESTS PASSED")
        print("FBC token menu improvements are working correctly:")
        print("  1. ✓ Right-click context menu shows all FBC tokens individually")
        print("  2. ✓ 'Print All' option remains available with correct token count")
        print("  3. ✓ RPC token handling remains unchanged")
        print("  4. ✓ Subgroup labels display correct token counts")
        print("  5. ✓ No regressions in other menu functionality")
        return 0
    else:
        print("\n✗ SOME VALIDATION TESTS FAILED")
        if result.failures:
            print("Failures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        if result.errors:
            print("Errors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
        return 1

if __name__ == "__main__":
    sys.exit(main())