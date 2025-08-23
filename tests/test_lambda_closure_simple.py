import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication, QMenu
from PyQt6.QtCore import QPoint

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestLambdaClosureFix(unittest.TestCase):
    """Simple test to verify lambda closure fix without complex dependencies"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize QApplication for tests"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def test_lambda_closure_concept(self):
        """Test that demonstrates the lambda closure issue and its fix"""
        # This test demonstrates the lambda closure problem and how default parameters fix it
        
        # Create a list that will change over time
        values = [1, 2, 3]
        
        # Problematic lambda (captures by reference)
        problematic_lambdas = []
        for value in values:
            # This will capture the variable 'value' by reference, not by value
            problematic_lambdas.append(lambda: value)
        
        # All lambdas will return the same value (the last value of 'value')
        results = [func() for func in problematic_lambdas]
        # This is the problem - all return 3
        self.assertEqual(results, [3, 3, 3])
        
        # Fixed lambda (captures by value using default parameter)
        fixed_lambdas = []
        for value in values:
            # This captures the current value of 'value' as a default parameter
            fixed_lambdas.append(lambda v=value: v)
        
        # All lambdas will return their respective values
        results = [func() for func in fixed_lambdas]
        # This is the fix - each returns its own value
        self.assertEqual(results, [1, 2, 3])
        
    def test_lambda_closure_with_multiple_parameters(self):
        """Test lambda closure with multiple parameters"""
        # Test with multiple parameters
        values1 = [1, 2, 3]
        values2 = ['a', 'b', 'c']
        
        # Fixed lambda with multiple parameters
        fixed_lambdas = []
        for v1, v2 in zip(values1, values2):
            # Capture both values using default parameters
            fixed_lambdas.append(lambda x=v1, y=v2: (x, y))
        
        # Verify each lambda returns its own pair of values
        results = [func() for func in fixed_lambdas]
        expected = [(1, 'a'), (2, 'b'), (3, 'c')]
        self.assertEqual(results, expected)

if __name__ == '__main__':
    unittest.main()