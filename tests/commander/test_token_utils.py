import unittest
from unittest.mock import MagicMock, patch
from src.commander.utils.token_utils import (
    TokenValidator,
    TokenRateLimiter,
    token_validator,
    token_rate_limiter,
    normalize_token,
    validate_token,
    is_fbc_token,
    is_rpc_token,
    validate_token_node,
    is_token_processing_allowed,
    get_token_processing_wait_time
)

class TestTokenValidator(unittest.TestCase):
    """Tests for TokenValidator class"""
    
    def setUp(self):
        self.validator = TokenValidator()
    
    def test_normalize_token_fbc_numeric(self):
        self.assertEqual(self.validator.normalize_token("1"), "001")
        self.assertEqual(self.validator.normalize_token("23"), "023")
        self.assertEqual(self.validator.normalize_token("456"), "456")
        
    def test_normalize_token_fbc_alphanumeric(self):
        self.assertEqual(self.validator.normalize_token("a1b2"), "a1b2")
        self.assertEqual(self.validator.normalize_token(" ABC "), "abc")
        
    def test_normalize_token_rpc(self):
        self.assertEqual(self.validator.normalize_token(" rpc123 "), "rpc123")
        
    def test_normalize_token_invalid(self):
        with self.assertRaises(TypeError):
            self.validator.normalize_token(None)
        with self.assertRaises(TypeError):
            self.validator.normalize_token(123)
            
    def test_validate_token_valid(self):
        self.assertTrue(self.validator.validate_token("123"))
        self.assertTrue(self.validator.validate_token("abc"))
        self.assertTrue(self.validator.validate_token("a1b2c3"))
        
    def test_validate_token_invalid(self):
        self.assertFalse(self.validator.validate_token(""))
        self.assertFalse(self.validator.validate_token("!@#$"))
        self.assertFalse(self.validator.validate_token("abc def"))
        
    def test_is_fbc_token_valid(self):
        self.assertTrue(self.validator.is_fbc_token("123"))
        self.assertTrue(self.validator.is_fbc_token("123a"))
        
    def test_is_fbc_token_invalid(self):
        self.assertFalse(self.validator.is_fbc_token("1234"))  # Too long
        self.assertFalse(self.validator.is_fbc_token("12"))    # Too short
        self.assertFalse(self.validator.is_fbc_token("abc"))   # Non-numeric
        
    def test_is_rpc_token_valid(self):
        self.assertTrue(self.validator.is_rpc_token("rpc123"))
        self.assertTrue(self.validator.is_rpc_token("token456"))
        
    def test_is_rpc_token_invalid(self):
        self.assertFalse(self.validator.is_rpc_token("123"))  # FBC token
        self.assertFalse(self.validator.is_rpc_token("!@#$")) # Invalid chars
        
    def test_validate_token_node_valid(self):
        node_manager = MagicMock()
        node_manager.get_node.return_value = True
        token = MagicMock()
        token.ip_address = "192.168.0.1"
        self.assertTrue(validate_token_node(token, node_manager))
        
    def test_validate_token_node_invalid(self):
        node_manager = MagicMock()
        node_manager.get_node.return_value = False
        token = MagicMock()
        token.ip_address = "192.168.0.1"
        self.assertFalse(validate_token_node(token, node_manager))

class TestTokenRateLimiter(unittest.TestCase):
    """Tests for TokenRateLimiter class"""
    
    def setUp(self):
        self.limiter = TokenRateLimiter(max_tokens_per_second=2)
    
    @patch('time.time')
    def test_rate_limiting(self, mock_time):
        mock_time.return_value = 0.0
        self.assertTrue(self.limiter.is_allowed())  # First token
        self.assertTrue(self.limiter.is_allowed())  # Second token
        self.assertFalse(self.limiter.is_allowed()) # Rate limited
        
        # Advance time to reset
        mock_time.return_value = 1.1
        self.assertTrue(self.limiter.is_allowed())  # Should reset
        
    @patch('time.time')
    def test_wait_time(self, mock_time):
        mock_time.return_value = 0.0
        self.limiter.is_allowed()
        self.limiter.is_allowed()  # Hit limit
        
        # Should have wait time remaining
        self.assertAlmostEqual(self.limiter.get_wait_time(), 1.0)
        
        # After time passes
        mock_time.return_value = 0.5
        self.assertAlmostEqual(self.limiter.get_wait_time(), 0.5)

class TestSingletonFunctions(unittest.TestCase):
    """Tests for singleton functions"""
    
    def test_normalize_token_singleton(self):
        self.assertEqual(normalize_token("1"), "001")
        self.assertEqual(token_validator.normalize_token("1"), "001")
        
    def test_validate_token_singleton(self):
        self.assertTrue(validate_token("valid_token"))
        self.assertTrue(token_validator.validate_token("valid_token"))
        
    def test_is_token_processing_allowed(self):
        # First call should be allowed
        self.assertTrue(is_token_processing_allowed())
        
        # Subsequent calls depend on rate limiter state
        # (Actual behavior tested in rate limiter tests)
        
    def test_get_token_processing_wait_time(self):
        # Depends on current rate limiter state
        # (Actual behavior tested in rate limiter tests)
        self.assertIsInstance(get_token_processing_wait_time(), float)

if __name__ == '__main__':
    unittest.main()