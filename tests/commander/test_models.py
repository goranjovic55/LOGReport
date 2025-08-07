import unittest
from unittest.mock import patch, MagicMock
from src.commander.models import NodeToken, Node


class TestNodeToken(unittest.TestCase):
    """Test cases for NodeToken class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_token_data = {
            'token_id': 'test_token_001',
            'token_type': 'FBC',
            'name': 'test_node',
            'ip_address': '192.168.1.100',
            'port': 23,
            'log_path': '/var/log/test.log',
            'protocol': 'telnet'
        }
    
    def test_node_token_creation_with_defaults(self):
        """Test NodeToken creation with default values."""
        token = NodeToken(token_id='test_001', token_type='FBC')
        
        self.assertEqual(token.token_id, 'test_001')
        self.assertEqual(token.token_type, 'FBC')
        self.assertEqual(token.name, 'default')
        self.assertEqual(token.ip_address, '0.0.0.0')
        self.assertEqual(token.port, 23)
        self.assertEqual(token.log_path, '')
        self.assertEqual(token.protocol, 'telnet')
    
    def test_node_token_creation_with_full_data(self):
        """Test NodeToken creation with full data."""
        token = NodeToken(**self.valid_token_data)
        
        for key, expected_value in self.valid_token_data.items():
            self.assertEqual(getattr(token, key), expected_value)
    
    def test_node_token_from_dict(self):
        """Test NodeToken creation from dictionary."""
        token = NodeToken.from_dict(self.valid_token_data)
        
        for key, expected_value in self.valid_token_data.items():
            self.assertEqual(getattr(token, key), expected_value)
    
    def test_node_token_to_dict(self):
        """Test NodeToken conversion to dictionary."""
        token = NodeToken(**self.valid_token_data)
        token_dict = token.to_dict()
        
        self.assertEqual(token_dict, self.valid_token_data)
    
    def test_node_token_from_dict_missing_required_fields(self):
        """Test NodeToken creation from dictionary with missing required fields."""
        incomplete_data = self.valid_token_data.copy()
        del incomplete_data['token_id']
        
        with self.assertRaises(ValueError) as context:
            NodeToken.from_dict(incomplete_data)
        
        self.assertIn("Missing required field: token_id", str(context.exception))
    
    def test_node_token_equality(self):
        """Test NodeToken equality comparison."""
        token1 = NodeToken(token_id='test_001', token_type='FBC', name='node1')
        token2 = NodeToken(token_id='test_001', token_type='FBC', name='node1')
        token3 = NodeToken(token_id='test_002', token_type='FBC', name='node1')
        
        self.assertEqual(token1, token2)
        self.assertNotEqual(token1, token3)
    
    def test_node_token_hash(self):
        """Test NodeToken hashing for use in sets/dicts."""
        token1 = NodeToken(token_id='test_001', token_type='FBC', name='node1')
        token2 = NodeToken(token_id='test_001', token_type='FBC', name='node1')
        token3 = NodeToken(token_id='test_002', token_type='FBC', name='node1')
        
        token_set = {token1, token2, token3}
        self.assertEqual(len(token_set), 2)
        
        token_dict = {token1: 'value1', token2: 'value2', token3: 'value3'}
        self.assertEqual(len(token_dict), 2)
    
    def test_node_token_string_representation(self):
        """Test NodeToken string representations."""
        token = NodeToken(token_id='test_001', token_type='FBC', name='test_node')
        
        str_repr = str(token)
        self.assertIn('test_001', str_repr)
        self.assertIn('FBC', str_repr)
        self.assertIn('test_node', str_repr)
        self.assertIn('0.0.0.0', str_repr)  # Default IP
        
        repr_str = repr(token)
        self.assertIn('test_001', repr_str)
        self.assertIn('FBC', repr_str)
        self.assertIn('test_node', repr_str)
    
    def test_node_token_validation_valid(self):
        """Test NodeToken validation with valid data."""
        token = NodeToken(**self.valid_token_data)
        self.assertTrue(token.validate())
    
    def test_node_token_validation_invalid_token_id(self):
        """Test NodeToken validation with invalid token_id."""
        invalid_data = self.valid_token_data.copy()
        invalid_data['token_id'] = ''
        token = NodeToken(**invalid_data)
        self.assertFalse(token.validate())
    
    def test_node_token_validation_invalid_token_type(self):
        """Test NodeToken validation with invalid token_type."""
        invalid_data = self.valid_token_data.copy()
        invalid_data['token_type'] = ''
        token = NodeToken(**invalid_data)
        self.assertFalse(token.validate())
    
    def test_node_token_validation_invalid_name(self):
        """Test NodeToken validation with invalid name."""
        invalid_data = self.valid_token_data.copy()
        invalid_data['name'] = ''
        token = NodeToken(**invalid_data)
        self.assertFalse(token.validate())
    
    def test_node_token_validation_invalid_ip(self):
        """Test NodeToken validation with invalid IP."""
        invalid_data = self.valid_token_data.copy()
        invalid_data['ip_address'] = 'invalid_ip'
        token = NodeToken(**invalid_data)
        self.assertFalse(token.validate())
    
    def test_node_token_validation_invalid_port(self):
        """Test NodeToken validation with invalid port."""
        invalid_data = self.valid_token_data.copy()
        invalid_data['port'] = 99999
        token = NodeToken(**invalid_data)
        self.assertFalse(token.validate())
    
    def test_node_token_kwargs_extension(self):
        """Test NodeToken creation with additional kwargs for future extensibility."""
        token = NodeToken(
            token_id='test_001',
            token_type='FBC',
            custom_field='custom_value'
        )
        
        # Should not raise an error and should ignore custom_field
        self.assertEqual(token.token_id, 'test_001')
        self.assertEqual(token.token_type, 'FBC')


class TestNode(unittest.TestCase):
    """Test cases for Node class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.node_data = {
            'name': 'test_node',
            'ip_address': '192.168.1.100',
            'status': 'online',
            'tokens': {
                'token_001': {
                    'token_id': 'token_001',
                    'token_type': 'FBC',
                    'name': 'test_node',
                    'ip_address': '192.168.1.100'
                },
                'token_002': {
                    'token_id': 'token_002',
                    'token_type': 'RPC',
                    'name': 'test_node',
                    'ip_address': '192.168.1.100'
                }
            }
        }
    
    def test_node_creation_with_defaults(self):
        """Test Node creation with default values."""
        node = Node(name='test_node', ip_address='192.168.1.100')
        
        self.assertEqual(node.name, 'test_node')
        self.assertEqual(node.ip_address, '192.168.1.100')
        self.assertEqual(node.status, 'offline')
        self.assertEqual(len(node.tokens), 0)
    
    def test_node_creation_with_full_data(self):
        """Test Node creation with full data."""
        node = Node(
            name=self.node_data['name'],
            ip_address=self.node_data['ip_address'],
            status=self.node_data['status']
        )
        
        self.assertEqual(node.name, self.node_data['name'])
        self.assertEqual(node.ip_address, self.node_data['ip_address'])
        self.assertEqual(node.status, self.node_data['status'])
        self.assertEqual(len(node.tokens), 0)
    
    def test_node_add_token(self):
        """Test adding tokens to a node."""
        node = Node(name='test_node', ip_address='192.168.1.100')
        token = NodeToken(token_id='test_token', token_type='FBC')
        
        node.add_token(token)
        self.assertEqual(len(node.tokens), 1)
        self.assertIn('test_token', node.tokens)
        self.assertEqual(node.tokens['test_token'], token)
    
    def test_node_remove_token(self):
        """Test removing tokens from a node."""
        node = Node(name='test_node', ip_address='192.168.1.100')
        token = NodeToken(token_id='test_token', token_type='FBC')
        
        node.add_token(token)
        self.assertTrue(node.remove_token('test_token'))
        self.assertEqual(len(node.tokens), 0)
        self.assertFalse(node.remove_token('nonexistent_token'))
    
    def test_node_get_token(self):
        """Test getting tokens from a node."""
        node = Node(name='test_node', ip_address='192.168.1.100')
        token = NodeToken(token_id='test_token', token_type='FBC')
        
        node.add_token(token)
        
        retrieved_token = node.get_token('test_token')
        self.assertEqual(retrieved_token, token)
        
        nonexistent_token = node.get_token('nonexistent_token')
        self.assertIsNone(nonexistent_token)
    
    def test_node_get_tokens_by_type(self):
        """Test getting tokens by type."""
        node = Node(name='test_node', ip_address='192.168.1.100')
        fbc_token = NodeToken(token_id='fbc_token', token_type='FBC')
        rpc_token = NodeToken(token_id='rpc_token', token_type='RPC')
        
        node.add_token(fbc_token)
        node.add_token(rpc_token)
        
        fbc_tokens = node.get_tokens_by_type('FBC')
        rpc_tokens = node.get_tokens_by_type('RPC')
        
        self.assertEqual(len(fbc_tokens), 1)
        self.assertEqual(len(rpc_tokens), 1)
        self.assertEqual(fbc_tokens[0], fbc_token)
        self.assertEqual(rpc_tokens[0], rpc_token)
    
    def test_node_from_dict(self):
        """Test Node creation from dictionary."""
        node = Node.from_dict(self.node_data)
        
        self.assertEqual(node.name, self.node_data['name'])
        self.assertEqual(node.ip_address, self.node_data['ip_address'])
        self.assertEqual(node.status, self.node_data['status'])
        self.assertEqual(len(node.tokens), 2)
        
        # Check tokens
        for token_id, expected_token_data in self.node_data['tokens'].items():
            self.assertIn(token_id, node.tokens)
            token = node.tokens[token_id]
            self.assertEqual(token.token_id, expected_token_data['token_id'])
            self.assertEqual(token.token_type, expected_token_data['token_type'])
    
    def test_node_to_dict(self):
        """Test Node conversion to dictionary."""
        node = Node.from_dict(self.node_data)
        node_dict = node.to_dict()
        
        self.assertEqual(node_dict['name'], self.node_data['name'])
        self.assertEqual(node_dict['ip_address'], self.node_data['ip_address'])
        self.assertEqual(node_dict['status'], self.node_data['status'])
        self.assertEqual(len(node_dict['tokens']), 2)
    
    def test_node_validation_valid(self):
        """Test Node validation with valid data."""
        node = Node.from_dict(self.node_data)
        self.assertTrue(node.validate())
    
    def test_node_validation_invalid_name(self):
        """Test Node validation with invalid name."""
        invalid_data = self.node_data.copy()
        invalid_data['name'] = ''
        node = Node.from_dict(invalid_data)
        self.assertFalse(node.validate())
    
    def test_node_validation_invalid_ip(self):
        """Test Node validation with invalid IP."""
        invalid_data = self.node_data.copy()
        invalid_data['ip_address'] = '999.999.999.999'  # Invalid IP format
        node = Node.from_dict(invalid_data)
        self.assertFalse(node.validate())
    
    def test_node_validation_invalid_status(self):
        """Test Node validation with invalid status."""
        invalid_data = self.node_data.copy()
        invalid_data['status'] = ''
        node = Node.from_dict(invalid_data)
        self.assertFalse(node.validate())
    
    def test_node_validation_invalid_tokens(self):
        """Test Node validation with invalid tokens."""
        invalid_data = self.node_data.copy()
        invalid_data['tokens']['invalid_token'] = {
            'token_id': '',
            'token_type': 'FBC',
            'name': 'test_node',
            'ip_address': '192.168.1.100'
        }
        node = Node.from_dict(invalid_data)
        self.assertFalse(node.validate())


if __name__ == '__main__':
    unittest.main()