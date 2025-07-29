import sys
import os
import unittest

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.commander.utils.error_detection import is_error_response

class TestErrorDetection(unittest.TestCase):
    
    def test_valid_response_not_error(self):
        """Test that valid responses are not identified as errors"""
        # The specific case mentioned in the issue
        response = "int from fbc rupi counters 1620000"
        self.assertFalse(is_error_response(response), 
                        f"Valid response '{response}' should not be identified as error")
        
        # Other valid responses
        valid_responses = [
            "OK",
            "Success",
            "Completed",
            "Done",
            "Finished",
            "int from fbc rupi counters 1234567",
            "Command executed successfully"
        ]
        
        for response in valid_responses:
            with self.subTest(response=response):
                self.assertFalse(is_error_response(response), 
                               f"Valid response '{response}' should not be identified as error")
    
    def test_error_responses_identified_correctly(self):
        """Test that actual error responses are identified as errors"""
        error_responses = [
            "Error: Connection failed",
            "Command not found",
            "Syntax error",
            "Permission denied",
            "Access denied",
            "Connection refused",
            "Connection failed",
            "Connection timeout",
            "Network error",
            "Authentication failed",
            "Login failed",
            "Error 404",
            "Err 500",
            "Failure occurred",
            "Exception raised",
            "Timeout occurred",
            "Not found",
            "Not supported",
            "Invalid command",
            "Unknown command"
        ]
        
        for response in error_responses:
            with self.subTest(response=response):
                self.assertTrue(is_error_response(response), 
                              f"Error response '{response}' should be identified as error")
    
    def test_empty_response(self):
        """Test that empty responses are not identified as errors"""
        self.assertFalse(is_error_response(""), "Empty response should not be identified as error")
        self.assertFalse(is_error_response(None), "None response should not be identified as error")
    
    def test_case_insensitive_matching(self):
        """Test that error detection is case insensitive"""
        error_responses = [
            "ERROR: Connection failed",
            "error: Connection failed",
            "Error: Connection failed",
            "FAILURE occurred",
            "failure occurred",
            "Failure occurred"
        ]
        
        for response in error_responses:
            with self.subTest(response=response):
                self.assertTrue(is_error_response(response), 
                              f"Error response '{response}' should be identified as error (case insensitive)")

if __name__ == '__main__':
    unittest.main()