#!/usr/bin/env python3
"""
Comprehensive FBC Context Menu Validation Test
Validates the FBC token context menu fix with systematic testing approach
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from commander.services.context_menu_service import ContextMenuService
from commander.services.context_menu_filter import ContextMenuFilterService
from commander.node_manager import NodeManager
from commander.models import Node, NodeToken

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FBCContextMenuValidator:
    """Comprehensive validator for FBC context menu functionality"""
    
    def __init__(self):
        self.node_manager = NodeManager()
        self.context_menu_filter = ContextMenuFilterService()
        self.context_menu_service = ContextMenuService(self.node_manager, self.context_menu_filter)
        self.test_results = []
        
    def validate_ap01m_fbc_tokens(self) -> bool:
        """Validate AP01m node has all expected FBC tokens (162, 163, 164)"""
        logger.info("=== Validating AP01m FBC Token Detection ===")
        
        # Get AP01m node
        ap01m_node = self.node_manager.get_node("AP01m")
        if not ap01m_node:
            error_msg = "AP01m node not found in configuration"
            logger.error(error_msg)
            self.test_results.append(("AP01m Node Detection", False, error_msg))
            return False
            
        logger.info(f"AP01m node found with {len(ap01m_node.tokens)} total tokens")
        
        # Get FBC tokens using context menu service method
        fbc_tokens = self.context_menu_service.get_node_tokens("AP01m", "FBC")
        logger.info(f"Found {len(fbc_tokens)} FBC tokens for AP01m")
        
        # Log all FBC tokens found
        for token in fbc_tokens:
            logger.info(f"  - Token ID: {token.token_id}, Type: {token.token_type}, Path: {token.log_path}")
        
        # Check for required tokens
        required_tokens = {"162", "163", "164"}
        found_tokens = {str(t.token_id) for t in fbc_tokens}
        
        missing_tokens = required_tokens - found_tokens
        if missing_tokens:
            error_msg = f"Missing FBC tokens: {missing_tokens}"
            logger.error(error_msg)
            self.test_results.append(("AP01m FBC Token Detection", False, error_msg))
            return False
            
        success_msg = f"All required FBC tokens found: {sorted(found_tokens)}"
        logger.info(success_msg)
        self.test_results.append(("AP01m FBC Token Detection", True, success_msg))
        return True
    
    def validate_context_menu_actions(self) -> bool:
        """Validate context menu generates correct actions for FBC tokens"""
        logger.info("=== Validating Context Menu Actions ===")
        
        # Create mock menu and item data for FBC subgroup
        mock_menu = Mock()
        mock_menu.actions = []
        mock_menu.addAction = Mock(side_effect=lambda action: mock_menu.actions.append(action))
        
        # Test data for FBC subgroup
        item_data = {
            "section_type": "FBC",
            "node": "AP01m"
        }
        
        # Get FBC tokens
        fbc_tokens = self.context_menu_service.get_node_tokens("AP01m", "FBC")
        
        # Mock the presenter
        mock_presenter = Mock()
        self.context_menu_service.set_presenter(mock_presenter)
        
        # Simulate context menu invocation
        added_actions = self.context_menu_service.show_context_menu(mock_menu, item_data, (100, 100))
        
        logger.info(f"Context menu added {len(mock_menu.actions)} actions")
        
        # Check if actions were added
        if not added_actions:
            error_msg = "No actions were added to context menu"
            logger.error(error_msg)
            self.test_results.append(("Context Menu Actions", False, error_msg))
            return False
            
        # Analyze actions
        action_texts = [action.text() for action in mock_menu.actions]
        logger.info(f"Actions generated: {action_texts}")
        
        # Check for "Print All" action
        print_all_actions = [action for action in mock_menu.actions if "Print All" in action.text()]
        if not print_all_actions:
            error_msg = "Print All action not found"
            logger.error(error_msg)
            self.test_results.append(("Context Menu Print All Action", False, error_msg))
            return False
            
        # Check for individual token actions
        individual_actions = [action for action in mock_menu.actions if "Token" in action.text()]
        expected_individual_count = len(fbc_tokens)
        
        if len(individual_actions) != expected_individual_count:
            error_msg = f"Expected {expected_individual_count} individual token actions, got {len(individual_actions)}"
            logger.error(error_msg)
            self.test_results.append(("Context Menu Individual Actions", False, error_msg))
            return False
            
        # Verify individual token actions contain correct token IDs
        token_ids_found = set()
        for action in individual_actions:
            action_text = action.text()
            # Extract token ID from action text (e.g., "Print FieldBus Structure (Token 162)")
            if "Token" in action_text:
                # Extract number from action text
                import re
                token_match = re.search(r'Token (\d+)', action_text)
                if token_match:
                    token_ids_found.add(token_match.group(1))
        
        expected_token_ids = {str(t.token_id) for t in fbc_tokens}
        if token_ids_found != expected_token_ids:
            error_msg = f"Token IDs mismatch. Expected: {expected_token_ids}, Found: {token_ids_found}"
            logger.error(error_msg)
            self.test_results.append(("Context Menu Token ID Accuracy", False, error_msg))
            return False
            
        success_msg = f"Context menu correctly generated {len(print_all_actions)} Print All action and {len(individual_actions)} individual token actions"
        logger.info(success_msg)
        self.test_results.append(("Context Menu Actions", True, success_msg))
        return True
    
    def validate_rpc_token_handling(self) -> bool:
        """Validate RPC token handling remains unchanged"""
        logger.info("=== Validating RPC Token Handling ===")
        
        # Get RPC tokens for AP01m
        rpc_tokens = self.context_menu_service.get_node_tokens("AP01m", "RPC")
        logger.info(f"Found {len(rpc_tokens)} RPC tokens for AP01m")
        
        # Create mock menu and item data for RPC subgroup
        mock_menu = Mock()
        mock_menu.actions = []
        mock_menu.addAction = Mock(side_effect=lambda action: mock_menu.actions.append(action))
        
        # Test data for RPC subgroup
        item_data = {
            "section_type": "RPC",
            "node": "AP01m"
        }
        
        # Mock the presenter
        mock_presenter = Mock()
        self.context_menu_service.set_presenter(mock_presenter)
        
        # Simulate context menu invocation for RPC
        added_actions = self.context_menu_service.show_context_menu(mock_menu, item_data, (100, 100))
        
        logger.info(f"RPC context menu added {len(mock_menu.actions)} actions")
        
        # Check if actions were added
        if not added_actions:
            error_msg = "No actions were added to RPC context menu"
            logger.error(error_msg)
            self.test_results.append(("RPC Context Menu Actions", False, error_msg))
            return False
            
        # Analyze actions
        action_texts = [action.text() for action in mock_menu.actions]
        logger.info(f"RPC Actions generated: {action_texts}")
        
        # For RPC, we should only have "Print All" action, no individual actions
        print_all_actions = [action for action in mock_menu.actions if "Print All" in action.text()]
        individual_actions = [action for action in mock_menu.actions if "Token" in action.text()]
        
        if len(individual_actions) > 0:
            error_msg = f"Individual token actions found for RPC (should not have any): {[a.text() for a in individual_actions]}"
            logger.error(error_msg)
            self.test_results.append(("RPC Individual Actions", False, error_msg))
            return False
            
        if len(print_all_actions) != 1:
            error_msg = f"Expected exactly 1 Print All action for RPC, got {len(print_all_actions)}"
            logger.error(error_msg)
            self.test_results.append(("RPC Print All Action", False, error_msg))
            return False
            
        success_msg = f"RPC token handling correctly maintained - only Print All action generated"
        logger.info(success_msg)
        self.test_results.append(("RPC Token Handling", True, success_msg))
        return True
    
    def validate_edge_cases(self) -> bool:
        """Validate edge cases and error handling"""
        logger.info("=== Validating Edge Cases ===")
        
        # Test 1: Non-existent node
        logger.info("Testing non-existent node...")
        fbc_tokens = self.context_menu_service.get_node_tokens("NONEXISTENT", "FBC")
        if len(fbc_tokens) != 0:
            error_msg = f"Expected 0 tokens for non-existent node, got {len(fbc_tokens)}"
            logger.error(error_msg)
            self.test_results.append(("Non-existent Node Handling", False, error_msg))
            return False
        logger.info("✓ Non-existent node handled correctly")
        
        # Test 2: Invalid token type
        logger.info("Testing invalid token type...")
        invalid_tokens = self.context_menu_service.get_node_tokens("AP01m", "INVALID")
        if len(invalid_tokens) != 0:
            error_msg = f"Expected 0 tokens for invalid type, got {len(invalid_tokens)}"
            logger.error(error_msg)
            self.test_results.append(("Invalid Token Type Handling", False, error_msg))
            return False
        logger.info("✓ Invalid token type handled correctly")
        
        # Test 3: Empty context menu data
        logger.info("Testing empty context menu data...")
        mock_menu = Mock()
        mock_menu.actions = []
        mock_menu.addAction = Mock(side_effect=lambda action: mock_menu.actions.append(action))
        
        added_actions = self.context_menu_service.show_context_menu(mock_menu, None, (100, 100))
        if added_actions:
            error_msg = "Expected no actions for empty data, but actions were added"
            logger.error(error_msg)
            self.test_results.append(("Empty Data Handling", False, error_msg))
            return False
        logger.info("✓ Empty context menu data handled correctly")
        
        success_msg = "All edge cases handled correctly"
        logger.info(success_msg)
        self.test_results.append(("Edge Cases", True, success_msg))
        return True
    
    def validate_configuration_compliance(self) -> bool:
        """Validate compliance with nodes_test.json configuration"""
        logger.info("=== Validating Configuration Compliance ===")
        
        # Load and validate nodes_test.json
        config_path = os.path.join(os.path.dirname(__file__), "nodes_test.json")
        if not os.path.exists(config_path):
            error_msg = f"Configuration file not found: {config_path}"
            logger.error(error_msg)
            self.test_results.append(("Configuration File Existence", False, error_msg))
            return False
            
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        except Exception as e:
            error_msg = f"Failed to load configuration: {e}"
            logger.error(error_msg)
            self.test_results.append(("Configuration File Loading", False, error_msg))
            return False
            
        # Find AP01m in configuration
        ap01m_config = None
        for node in config_data:
            if node.get("name") == "AP01m":
                ap01m_config = node
                break
                
        if not ap01m_config:
            error_msg = "AP01m not found in configuration"
            logger.error(error_msg)
            self.test_results.append(("AP01m Configuration", False, error_msg))
            return False
            
        # Validate tokens in configuration
        config_tokens = ap01m_config.get("tokens", [])
        config_types = ap01m_config.get("types", [])
        
        logger.info(f"Configuration shows {len(config_tokens)} tokens: {config_tokens}")
        logger.info(f"Configuration shows types: {config_types}")
        
        # Get actual tokens from node manager
        ap01m_node = self.node_manager.get_node("AP01m")
        if not ap01m_node:
            error_msg = "AP01m node not found in node manager"
            logger.error(error_msg)
            self.test_results.append(("AP01m Node Manager", False, error_msg))
            return False
            
        # Check if all configured tokens are present
        configured_fbc_tokens = []
        for i, token_id in enumerate(config_tokens):
            if i < len(config_types) and config_types[i].upper() == "FBC":
                configured_fbc_tokens.append(str(token_id))
                
        logger.info(f"Configured FBC tokens: {configured_fbc_tokens}")
        
        # Get actual FBC tokens
        actual_fbc_tokens = [str(t.token_id) for t in ap01m_node.tokens.values() if t.token_type == "FBC"]
        logger.info(f"Actual FBC tokens: {actual_fbc_tokens}")
        
        if set(configured_fbc_tokens) != set(actual_fbc_tokens):
            error_msg = f"Configuration mismatch. Configured: {configured_fbc_tokens}, Actual: {actual_fbc_tokens}"
            logger.error(error_msg)
            self.test_results.append(("Configuration Compliance", False, error_msg))
            return False
            
        success_msg = f"Configuration compliance verified - {len(configured_fbc_tokens)} FBC tokens match"
        logger.info(success_msg)
        self.test_results.append(("Configuration Compliance", True, success_msg))
        return True
    
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report"""
        logger.info("=== Generating Validation Report ===")
        
        report_lines = [
            "# FBC Token Context Menu Fix Validation Report",
            "",
            "## Executive Summary",
            f"Validation completed on {Path(__file__).name}",
            f"Total tests executed: {len(self.test_results)}",
            f"Tests passed: {sum(1 for result in self.test_results if result[1])}",
            f"Tests failed: {sum(1 for result in self.test_results if not result[1])}",
            "",
            "## Test Results Summary",
            ""
        ]
        
        # Add test results
        for test_name, passed, details in self.test_results:
            status = "✅ PASS" if passed else "❌ FAIL"
            report_lines.append(f"### {test_name}")
            report_lines.append(f"**Status**: {status}")
            report_lines.append(f"**Details**: {details}")
            report_lines.append("")
        
        # Add overall assessment
        passed_tests = sum(1 for result in self.test_results if result[1])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        report_lines.extend([
            "## Overall Assessment",
            f"**Success Rate**: {success_rate:.1f}% ({passed_tests}/{total_tests} tests passed)",
            "",
            "## Validation Criteria",
            ""
        ])
        
        # Check specific validation criteria
        criteria_met = []
        
        # Check if AP01m FBC tokens are detected
        ap01m_fbc_passed = any(result[0] == "AP01m FBC Token Detection" and result[1] for result in self.test_results)
        criteria_met.append(("Individual FBC token actions appear", ap01m_fbc_passed))
        
        # Check if context menu works correctly
        context_menu_passed = any(result[0] == "Context Menu Actions" and result[1] for result in self.test_results)
        criteria_met.append(("Context menu functionality", context_menu_passed))
        
        # Check if "Print All" is preserved
        print_all_passed = any(result[0] == "Context Menu Print All Action" and result[1] for result in self.test_results)
        criteria_met.append(("'Print All' functionality preserved", print_all_passed))
        
        # Check RPC handling
        rpc_passed = any(result[0] == "RPC Token Handling" and result[1] for result in self.test_results)
        criteria_met.append(("RPC token handling unchanged", rpc_passed))
        
        # Check edge cases
        edge_cases_passed = any(result[0] == "Edge Cases" and result[1] for result in self.test_results)
        criteria_met.append(("Edge case handling", edge_cases_passed))
        
        # Check configuration compliance
        config_passed = any(result[0] == "Configuration Compliance" and result[1] for result in self.test_results)
        criteria_met.append(("Configuration compliance", config_passed))
        
        # Add criteria to report
        for criterion, met in criteria_met:
            status = "✅ MET" if met else "❌ NOT MET"
            report_lines.append(f"- {criterion}: {status}")
        
        report_lines.append("")
        
        # Add final conclusion
        if success_rate >= 90:
            conclusion = "🎉 **VALIDATION SUCCESSFUL** - All critical criteria met"
        elif success_rate >= 70:
            conclusion = "⚠️ **VALIDATION PARTIAL** - Some criteria met, review failed tests"
        else:
            conclusion = "❌ **VALIDATION FAILED** - Multiple criteria not met"
            
        report_lines.extend([
            "## Conclusion",
            conclusion,
            "",
            "## Recommendations",
            ""
        ])
        
        if success_rate < 100:
            failed_tests = [result[0] for result in self.test_results if not result[1]]
            report_lines.append(f"Review and fix the following failed tests:")
            for test in failed_tests:
                report_lines.append(f"- {test}")
        else:
            report_lines.append("No recommendations - all tests passed successfully")
        
        return "\n".join(report_lines)
    
    def run_validation(self) -> bool:
        """Run complete validation workflow"""
        logger.info("Starting FBC Context Menu Validation...")
        
        # Execute all validation tests
        tests = [
            self.validate_ap01m_fbc_tokens,
            self.validate_context_menu_actions,
            self.validate_rpc_token_handling,
            self.validate_edge_cases,
            self.validate_configuration_compliance
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                logger.error(f"Test {test.__name__} failed with exception: {e}")
                import traceback
                traceback.print_exc()
                self.test_results.append((test.__name__, False, f"Exception: {e}"))
        
        # Generate and save report
        report = self.generate_validation_report()
        report_path = os.path.join(os.path.dirname(__file__), "fbc_context_menu_validation_report.md")
        
        try:
            with open(report_path, 'w') as f:
                f.write(report)
            logger.info(f"Validation report saved to: {report_path}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
        
        # Return overall success
        passed_tests = sum(1 for result in self.test_results if result[1])
        total_tests = len(self.test_results)
        
        logger.info(f"Validation completed: {passed_tests}/{total_tests} tests passed")
        return passed_tests == total_tests

def main():
    """Main function to run the validation"""
    print("FBC Token Context Menu Fix Validation")
    print("=" * 50)
    
    validator = FBCContextMenuValidator()
    success = validator.run_validation()
    
    if success:
        print("\n🎉 All validation tests passed!")
        return 0
    else:
        print(f"\n⚠️ {sum(1 for result in validator.test_results if not result[1])} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())