import pytest
from unittest.mock import patch
from PyQt6.QtCore import QObject, pyqtSignal
from src.commander.node_manager import NodeManager
from src.commander.models import Node, NodeToken

class TestNodeManagerSignal:
    """Test cases for NodeManager signal emissions"""
    
    @pytest.fixture
    def node_manager(self):
        nm = NodeManager()
        return nm
    
    def test_load_configuration_emits_signal(self, node_manager, qtbot):
        """Test that load_configuration emits nodes_updated signal"""
        with qtbot.waitSignal(node_manager.nodes_updated, timeout=1000):
            with patch("builtins.open"), \
                 patch("json.load") as mock_load, \
                 patch("os.path.exists", return_value=True):
                mock_load.return_value = [{
                    "name": "TestNode",
                    "ip_address": "192.168.1.1",
                    "tokens": [{"token_id": "123", "token_type": "FBC", "port": 23}]
                }]
                assert node_manager.load_configuration() is True
    
    def test_add_node_emits_signal(self, node_manager, qtbot):
        """Test that add_node emits nodes_updated signal"""
        node_data = {
            "name": "NewNode",
            "ip_address": "192.168.1.100",
            "tokens": [{"token_id": "456", "token_type": "RPC", "port": 23}]
        }
        with qtbot.waitSignal(node_manager.nodes_updated, timeout=1000):
            node_manager.add_node(node_data)
    
    def test_remove_node_emits_signal(self, node_manager, qtbot):
        """Test that removing a node emits nodes_updated signal"""
        # First add a node to remove
        node_data = {
            "name": "TempNode",
            "ip_address": "192.168.1.50",
            "tokens": [{"token_id": "789", "token_type": "LOG", "port": 23}]
        }
        node_manager.add_node(node_data)
        
        with qtbot.waitSignal(node_manager.nodes_updated, timeout=1000):
            # Implement node removal in NodeManager
            node_manager.nodes.pop("TempNode")
    
    def test_scan_log_files_emits_signal(self, node_manager, qtbot):
        """Test that scan_log_files emits nodes_updated signal"""
        # Setup test node
        node = Node(name="ScanNode", ip_address="192.168.1.200")
        token = NodeToken(token_id="999", token_type="FBC", ip_address="192.168.1.200", port=23)
        node.add_token(token)
        node_manager.nodes["ScanNode"] = node
        
        with qtbot.waitSignal(node_manager.nodes_updated, timeout=1000):
            with patch("os.path.exists", return_value=True), \
                 patch("os.listdir", return_value=["ScanNode_192-168-1-200_999.fbc"]), \
                 patch("os.path.isdir", return_value=True):
                node_manager.scan_log_files()
class TestNodeManagerScanLogFiles:
    """Test cases for NodeManager's scan_log_files method"""

    def test_scan_log_files_for_log_tokens(self, tmp_path):
        # Create a temporary directory structure for LOG tokens
        log_root = tmp_path / "logs"
        log_dir = log_root / "LOG"
        ap01m_dir = log_dir / "AP01m"
        ap01m_dir.mkdir(parents=True)
        
        # Create a sample LOG token file
        log_file = ap01m_dir / "162_LOG.log"
        log_file.write_text("test log content")
        
        # Create node manager and nodes
        manager = NodeManager()
        manager.log_root = str(log_root)
        
        node = Node(name="AP01m", ip_address="192.168.0.11")
        token = NodeToken(
            name="AP01m 162",
            token_id="162",
            token_type="LOG",
            ip_address="192.168.0.11",
            port=23
        )
        node.add_token(token)
        manager.nodes = {"AP01m": node}
        
        # Scan log files
        manager.scan_log_files()
        
        # Verify token log path was updated
        assert token.log_path == str(log_file)

    def test_scan_log_files_for_log_tokens_invalid_format(self, tmp_path, capsys):
        # Create a temporary directory structure for LOG tokens
        log_root = tmp_path / "logs"
        log_dir = log_root / "LOG"
        ap01m_dir = log_dir / "AP01m"
        ap01m_dir.mkdir(parents=True)
        
        # Create an invalid LOG token file
        invalid_file = ap01m_dir / "invalid.log"
        invalid_file.write_text("invalid format")
        
        # Create node manager and nodes
        manager = NodeManager()
        manager.log_root = str(log_root)
        
        node = Node(name="AP01m", ip_address="192.168.0.11")
        token = NodeToken(
            name="AP01m 162",
            token_id="162",
            token_type="LOG",
            ip_address="192.168.0.11",
            port=23
        )
        node.add_token(token)
        manager.nodes = {"AP01m": node}
        
        # Scan log files
        manager.scan_log_files()
        
        # Verify token log path not updated
        assert token.log_path is None
        captured = capsys.readouterr()
        assert "Skipping non-LOG file" in captured.out
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from src.commander.node_manager import NodeManager
from src.commander.models import Node, NodeToken

def test_scan_log_files_includes_root_logs():
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create root log files
        root_log1 = os.path.join(tmpdir, "app.log")
        root_log2 = os.path.join(tmpdir, "system.log")
        with open(root_log1, "w") as f:
            f.write("test log")
        with open(root_log2, "w") as f:
            f.write("test log")
        
        # Create token directories and files
        os.mkdir(os.path.join(tmpdir, "FBC"))
        os.mkdir(os.path.join(tmpdir, "FBC", "AP01m"))
        token_log = os.path.join(tmpdir, "FBC", "AP01m", "AP01m_192-168-0-11_162_fbc.log")
        with open(token_log, "w") as f:
            f.write("test log")
        
        # Initialize NodeManager and scan
        manager = NodeManager()
        manager.log_root = tmpdir
        manager.scan_log_files()
        
        # Verify root logs were found
        assert len(manager.root_logs) == 2
        assert root_log1 in manager.root_logs
        assert root_log2 in manager.root_logs
        
        # Verify token logs were still processed
        node = manager.get_node("AP01m")
        assert node is not None
        token = node.get_token("162")
        assert token is not None
        assert token.log_path == token_log

def test_scan_log_files_handles_root_errors(caplog):
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Make the directory unreadable
        os.chmod(tmpdir, 0o000)
        
        # Initialize NodeManager and scan
        manager = NodeManager()
        manager.log_root = tmpdir
        manager.scan_log_files()
        
        # Verify error was logged
        assert "Error scanning root directory" in caplog.text

class TestNodeManagerHybridTokenResolution:
    """Test cases for NodeManager's hybrid token resolution"""
    
    def test_get_token_with_fallback_to_fbc(self, tmp_path):
        """Test that RPC commands can use FBC tokens as fallback"""
        # Create node manager with test configuration
        manager = NodeManager()
        manager.log_root = str(tmp_path)
        
        # Create node with FBC token only
        node = Node(name="AP01m", ip_address="192.168.0.11")
        fbc_token = NodeToken(
            name="AP01m 162",
            token_id="162",
            token_type="FBC",
            ip_address="192.168.0.11",
            port=2077
        )
        node.add_token(fbc_token)
        manager.nodes = {"AP01m": node}
        
        # Test that we can get an RPC token based on FBC token
        token = manager.get_token("AP01m", "162")
        assert token is not None
        assert token.token_id == "162"
        assert token.token_type == "FBC"  # Original token is still FBC
        
    def test_scan_log_files_dynamic_ip_resolution(self, tmp_path):
        """Test dynamic IP resolution from directory names"""
        # Create directory structure with IP in directory name
        log_root = tmp_path / "logs"
        rpc_dir = log_root / "RPC" / "AP01m_192-168-0-11"
        rpc_dir.mkdir(parents=True)
        
        # Create node manager with test node that has no IP
        manager = NodeManager()
        manager.log_root = str(log_root)
        
        node = Node(name="AP01m", ip_address="0.0.0.0")
        token = NodeToken(
            name="AP01m 162",
            token_id="162",
            token_type="RPC",
            ip_address="0.0.0.0",  # No IP initially
            port=2077
        )
        node.add_token(token)
        manager.nodes = {"AP01m": node}
        
        # Scan for IPs
        manager.scan_log_files()
        
        # Verify token IP was updated
        assert token.ip_address == "192.168.0.11"
        
    def test_scan_log_files_dynamic_ip_resolution_from_filename(self, tmp_path):
        """Test dynamic IP resolution from filenames"""
        # Create directory structure with IP in filename
        log_root = tmp_path / "logs"
        rpc_dir = log_root / "RPC" / "AP01m"
        rpc_dir.mkdir(parents=True)
        
        # Create file with IP in name
        log_file = rpc_dir / "AP01m_192-168-0-11_162.rpc"
        log_file.write_text("test content")
        
        # Create node manager with test node that has no IP
        manager = NodeManager()
        manager.log_root = str(log_root)
        
        node = Node(name="AP01m", ip_address="0.0.0.0")
        token = NodeToken(
            name="AP01m 162",
            token_id="162",
            token_type="RPC",
            ip_address="0.0.0.0",  # No IP initially
            port=2077
        )
        node.add_token(token)
        manager.nodes = {"AP01m": node}
        
        # Scan for IPs
        manager.scan_log_files()
        
        # Verify token IP was updated
        assert token.ip_address == "192.168.0.11"
        
    def test_configuration_fallback_behavior(self):
        """Test configuration fallback behavior when tokens are not found"""
        # Create node manager with empty configuration
        manager = NodeManager()
        manager.nodes = {}
        
        # Test that get_token returns None for non-existent node
        token = manager.get_token("NonExistentNode", "123")
        assert token is None