import unittest
from unittest.mock import patch, MagicMock, call
from src.commander.telnet_client import TelnetClient
import src.commander.telnet_client  # Force coverage import
import socket

class TestTelnetClient(unittest.TestCase):
    """Tests for TelnetClient connection state handling"""
    
    def setUp(self):
        self.client = TelnetClient()
        self.client.timeout = 1  # Shorter timeout for tests
        
    @patch('telnetlib.Telnet')
    @patch('time.sleep')
    def test_successful_connection(self, mock_sleep, mock_telnet):
        """Test successful telnet connection"""
        mock_instance = MagicMock()
        mock_telnet.return_value = mock_instance
        
        success, message = self.client.connect("192.168.0.1", 23)
        self.assertTrue(success)
        self.assertEqual(message, "Connected successfully")
        mock_instance.open.assert_called_with("192.168.0.1", 23, 1)

    @patch('telnetlib.Telnet')
    @patch('time.sleep')
    def test_connection_timeout(self, mock_sleep, mock_telnet):
        """Test connection timeout handling"""
        mock_instance = MagicMock()
        mock_telnet.return_value = mock_instance
        mock_instance.open.side_effect = socket.timeout
        
        success, message = self.client.connect("192.168.0.1", 23)
        self.assertFalse(success)
        self.assertIn("Connection timed out", message)
        # Verify cleanup attempt
        mock_instance.close.assert_called_once()

    @patch('telnetlib.Telnet')
    @patch('time.sleep')
    def test_command_execution_while_connected(self, mock_sleep, mock_telnet):
        """Test command execution when connected"""
        mock_instance = MagicMock()
        mock_instance.read_very_eager.return_value = b"response"
        mock_telnet.return_value = mock_instance
        
        success, _ = self.client.connect("192.168.0.1", 23)
        self.assertTrue(success)
        response = self.client.send_command("test")
        self.assertIn("response", response)

    @patch('telnetlib.Telnet')
    @patch('time.sleep')
    def test_command_timeout_handling(self, mock_sleep, mock_telnet):
        """Test command timeout recovery"""
        """Test command timeout recovery"""
        mock_instance = MagicMock()
        mock_telnet.return_value = mock_instance
        
        # Successful connection
        success, message = self.client.connect("192.168.0.1", 23)
        self.assertTrue(success)
        
        # Reset write mock to ignore connection setup writes
        mock_instance.write.reset_mock()

        # Set up mock responses to allow control character writes first
        mock_instance.read_very_eager.side_effect = [
            b'',  # Initial buffer clear
            b'',  # After Ctrl+X
            b'',  # After Ctrl+Z
            socket.timeout  # Actual command response timeout
        ]
        response = self.client.send_command("test")
        self.assertIn("timed out", response)

        # Verify control sequence and command writes
        self.assertEqual(mock_instance.write.call_count, 3)
        mock_instance.write.assert_has_calls([
            call(b'\x18'),  # Ctrl+X
            call(b'\x1A'),  # Ctrl+Z
            call(b'test\r\n')
        ])
        mock_instance.write.assert_has_calls([
            call(b'\x18'),  # Ctrl+X
            call(b'\x1A'),  # Ctrl+Z
            call(b'test\r\n')
        ])
        # Verify control characters and command formatting
        self.assertEqual(mock_instance.write.call_args_list[0][0], (b'\x18',))  # Ctrl+X
        self.assertEqual(mock_instance.write.call_args_list[1][0], (b'\x1A',))  # Ctrl+Z
        self.assertEqual(mock_instance.write.call_args_list[2][0], (b'test\r\n',))
        mock_instance.write.assert_has_calls([
            call(b'\x18'),
            call(b'\x1a'),
            call(b'test\r\n')
        ])

    def test_response_filtering(self):
        """Test ANSI code and control character removal"""
        test_response = "\x1b[32mRESPONSE\x07\n~"
        filtered = self.client._filter_output(test_response)
        self.assertEqual(filtered, "RESPONSE")

    @patch('time.sleep')
    def test_none_response_handling(self, mock_sleep):
        """Test handling of None response from telnet"""
        with patch('telnetlib.Telnet') as mock_telnet:
            mock_instance = MagicMock()
            mock_instance.read_very_eager.return_value = None
            mock_telnet.return_value = mock_instance
            
            success, _ = self.client.connect("192.168.0.1", 23)
            self.assertTrue(success)
            response = self.client.send_command("test")
            self.assertEqual(response, "")

    def test_empty_response_filtering(self):
        """Test filtering of empty response with control characters"""
        test_response = "\x1b[32m\x07\n~"
        filtered = self.client._filter_output(test_response)
        self.assertEqual(filtered, "")

    @patch('telnetlib.Telnet')
    @patch('time.sleep')
    def test_mode_detection(self, mock_sleep, mock_telnet):
        """Test editor mode detection in responses"""
        mock_instance = MagicMock()
        mock_instance.read_very_eager.return_value = b"Editor changed to INSERT mode"
        mock_telnet.return_value = mock_instance
        
        success, _ = self.client.connect("192.168.0.1", 23)
        self.assertTrue(success)
        response = self.client.send_command("test")
        self.assertEqual(self.client.mode, "INSERT")

    @patch('telnetlib.Telnet')
    def test_connection_refused_error(self, mock_telnet):
        """Test connection refused error handling"""
        mock_telnet.side_effect = ConnectionRefusedError("Connection refused")
        success, message = self.client.connect("192.168.0.1", 23)
        self.assertFalse(success)
        self.assertEqual(message, "Connection refused")

    @patch('telnetlib.Telnet')
    def test_generic_exception_handling(self, mock_telnet):
        """Test generic exception handling during connection"""
        mock_telnet.side_effect = Exception("Generic error")
        success, message = self.client.connect("192.168.0.1", 23)
        self.assertFalse(success)
        self.assertEqual(message, "Connection failed: Generic error")

    @patch('telnetlib.Telnet')
    @patch('time.sleep')
    def test_read_response_timeout(self, mock_sleep, mock_telnet):
        """Test full response timeout handling"""
        mock_instance = MagicMock()
        mock_telnet.return_value = mock_instance
        self.client.timeout = 0.1
        
        # Simulate no response until timeout
        # Establish connection first
        self.client.connect("192.168.0.1", 23)
        # Reset mock to clear connection setup writes
        mock_instance.write.reset_mock()
        # Set up proper timeout simulation
        mock_instance.read_very_eager.side_effect = socket.timeout
        mock_instance.write.reset_mock()
        
        response = self.client.send_command("test")
        self.assertIn("timed out", response)

    def test_filter_output_with_null_bytes(self):
        """Test filtering of null bytes and special characters"""
        test_response = "Hello\x00World\x07\n"
        filtered = self.client._filter_output(test_response)
        self.assertEqual(filtered, "HelloWorld")

if __name__ == '__main__':
    unittest.main()