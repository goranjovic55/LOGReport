import unittest
from unittest.mock import patch, MagicMock
from src.commander.telnet_client import TelnetClient
import socket

class TestTelnetClient(unittest.TestCase):
    """Tests for TelnetClient connection state handling"""
    
    def setUp(self):
        self.client = TelnetClient()
        self.client.timeout = 1  # Shorter timeout for tests
        
    @patch('telnetlib.Telnet')
    def test_successful_connection(self, mock_telnet):
        """Test successful telnet connection"""
        mock_instance = MagicMock()
        mock_telnet.return_value = mock_instance
        
        result = self.client.connect("192.168.0.1", 23)
        self.assertTrue(result)
        mock_instance.open.assert_called_with("192.168.0.1", 23, 1)

    @patch('telnetlib.Telnet')
    def test_connection_timeout(self, mock_telnet):
        """Test connection timeout handling"""
        mock_telnet.side_effect = socket.timeout
        result = self.client.connect("192.168.0.1", 23)
        self.assertFalse(result)

    @patch('telnetlib.Telnet')
    def test_command_execution_while_connected(self, mock_telnet):
        """Test command execution when connected"""
        mock_instance = MagicMock()
        mock_instance.read_very_eager.return_value = b"response"
        mock_telnet.return_value = mock_instance
        
        self.client.connect("192.168.0.1", 23)
        response = self.client.send_command("test")
        self.assertIn("response", response)

    @patch('telnetlib.Telnet')
    def test_command_timeout_handling(self, mock_telnet):
        """Test command timeout recovery"""
        mock_instance = MagicMock()
        mock_instance.read_very_eager.side_effect = socket.timeout
        mock_telnet.return_value = mock_instance
        
        self.client.connect("192.168.0.1", 23)
        response = self.client.send_command("test")
        self.assertIn("timed out", response)

    def test_response_filtering(self):
        """Test ANSI code and control character removal"""
        test_response = "\x1b[32mRESPONSE\x07\n~"
        filtered = self.client._filter_output(test_response)
        self.assertEqual(filtered, "RESPONSE")

    @patch('telnetlib.Telnet')
    def test_mode_detection(self, mock_telnet):
        """Test editor mode detection in responses"""
        mock_instance = MagicMock()
        mock_instance.read_very_eager.return_value = b"Editor changed to INSERT mode"
        mock_telnet.return_value = mock_instance
        
        self.client.connect("192.168.0.1", 23)
        response = self.client.send_command("test")
        self.assertEqual(self.client.mode, "INSERT")

if __name__ == '__main__':
    unittest.main()