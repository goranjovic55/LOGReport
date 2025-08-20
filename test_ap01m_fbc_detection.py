import os
import tempfile
import pytest
from src.commander.node_manager import NodeManager
from src.commander.models import Node, NodeToken

def test_ap01m_fbc_token_detection_from_log_files():
    """Test that FBC tokens are correctly detected from .log files with naming pattern XXX_FBC.log"""
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create node-specific directory structure
        ap01m_dir = os.path.join(tmpdir, "AP01m")
        os.makedirs(ap01m_dir)
        
        # Create .log files with FBC/RPC naming pattern
        fbc_file_162 = os.path.join(ap01m_dir, "162_FBC.log")
        fbc_file_163 = os.path.join(ap01m_dir, "163_FBC.log")
        fbc_file_164 = os.path.join(ap01m_dir, "164_FBC.log")
        
        # Write test content to files
        for file_path in [fbc_file_162, fbc_file_163, fbc_file_164]:
            with open(file_path, "w") as f:
                f.write("test log content")
        
        # Initialize NodeManager with test configuration
        manager = NodeManager()
        manager.log_root = tmpdir
        
        # Create node with expected tokens
        node = Node(name="AP01m", ip_address="192.168.1.101")
        
        # Add the three tokens that should be detected
        token_162 = NodeToken(
            name="AP01m 162",
            token_id="162",
            token_type="FBC",
            ip_address="192.168.1.101",
            port=2077
        )
        node.add_token(token_162)
        
        token_163 = NodeToken(
            name="AP01m 163",
            token_id="163",
            token_type="VNC",
            ip_address="192.168.1.101",
            port=5901
        )
        node.add_token(token_163)
        
        token_164 = NodeToken(
            name="AP01m 164",
            token_id="164",
            token_type="RPC",
            ip_address="192.168.1.101",
            port=2077
        )
        node.add_token(token_164)
        
        manager.nodes = {"AP01m": node}
        
        # Scan log files
        manager.scan_log_files()
        
        # Verify that all three tokens have their log paths updated
        # Token 162 (FBC) - should match existing token
        assert token_162.log_path == fbc_file_162, f"Expected {fbc_file_162}, got {token_162.log_path}"
        
        # Token 163 (VNC in config, but FBC file) - should match existing token since token ID matches
        assert token_163.log_path == fbc_file_163, f"Expected {fbc_file_163}, got {token_163.log_path}"
        
        # Token 164 (RPC in config, but FBC file) - should match existing token since token ID matches
        assert token_164.log_path == fbc_file_164, f"Expected {fbc_file_164}, got {token_164.log_path}"

def test_log_file_token_type_detection():
    """Test that .log files are correctly classified based on filename pattern"""
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create node-specific directory structure
        ap01m_dir = os.path.join(tmpdir, "AP01m")
        os.makedirs(ap01m_dir)
        
        # Create .log files with different naming patterns
        fbc_file = os.path.join(ap01m_dir, "162_FBC.log")
        rpc_file = os.path.join(ap01m_dir, "163_RPC.log")
        log_file = os.path.join(ap01m_dir, "164_LOG.log")  # This should be classified as LOG
        
        # Write test content to files
        for file_path in [fbc_file, rpc_file, log_file]:
            with open(file_path, "w") as f:
                f.write("test log content")
        
        # Initialize NodeManager with test configuration
        manager = NodeManager()
        manager.log_root = tmpdir
        
        # Create node with expected tokens
        node = Node(name="AP01m", ip_address="192.168.1.101")
        
        # Add tokens for FBC and RPC
        token_162 = NodeToken(
            name="AP01m 162",
            token_id="162",
            token_type="FBC",
            ip_address="192.168.1.101",
            port=2077
        )
        node.add_token(token_162)
        
        token_163 = NodeToken(
            name="AP01m 163",
            token_id="163",
            token_type="RPC",
            ip_address="192.168.1.101",
            port=2077
        )
        node.add_token(token_163)
        
        # Add token for LOG file
        token_164 = NodeToken(
            name="AP01m 164",
            token_id="164",
            token_type="LOG",
            ip_address="192.168.1.101",
            port=2077
        )
        node.add_token(token_164)
        
        manager.nodes = {"AP01m": node}
        
        # Scan log files
        manager.scan_log_files()
        
        # Verify that FBC file is correctly classified
        assert token_162.log_path == fbc_file, f"Expected {fbc_file}, got {token_162.log_path}"
        
        # Verify that RPC file is correctly classified
        assert token_163.log_path == rpc_file, f"Expected {rpc_file}, got {token_163.log_path}"
        
        # Verify that LOG file is correctly classified
        assert token_164.log_path == log_file, f"Expected {log_file}, got {token_164.log_path}"

def test_mixed_file_types_in_same_directory():
    """Test that different file types in the same directory are correctly classified"""
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create node-specific directory structure
        ap01m_dir = os.path.join(tmpdir, "AP01m")
        os.makedirs(ap01m_dir)
        
        # Create mixed .log files with different naming patterns
        fbc_file = os.path.join(ap01m_dir, "162_FBC.log")
        rpc_file = os.path.join(ap01m_dir, "163_RPC.log")
        vnc_file = os.path.join(ap01m_dir, "164_VNC.log")
        
        # Write test content to files
        for file_path in [fbc_file, rpc_file, vnc_file]:
            with open(file_path, "w") as f:
                f.write("test log content")
        
        # Initialize NodeManager with test configuration
        manager = NodeManager()
        manager.log_root = tmpdir
        
        # Create node with expected tokens
        node = Node(name="AP01m", ip_address="192.168.1.101")
        
        # Add tokens
        token_162 = NodeToken(
            name="AP01m 162",
            token_id="162",
            token_type="FBC",
            ip_address="192.168.1.101",
            port=2077
        )
        node.add_token(token_162)
        
        token_163 = NodeToken(
            name="AP01m 163",
            token_id="163",
            token_type="RPC",
            ip_address="192.168.1.101",
            port=2077
        )
        node.add_token(token_163)
        
        token_164 = NodeToken(
            name="AP01m 164",
            token_id="164",
            token_type="VNC",
            ip_address="192.168.1.101",
            port=5901
        )
        node.add_token(token_164)
        
        manager.nodes = {"AP01m": node}
        
        # Scan log files
        manager.scan_log_files()
        
        # Verify that each file is correctly classified by its filename pattern
        assert token_162.log_path == fbc_file, f"Expected {fbc_file}, got {token_162.log_path}"
        assert token_163.log_path == rpc_file, f"Expected {rpc_file}, got {token_163.log_path}"
        assert token_164.log_path == vnc_file, f"Expected {vnc_file}, got {token_164.log_path}"

def test_directory_based_node_name_extraction():
    """Test that node name is correctly extracted from directory name for node-specific files"""
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create node-specific directory structure
        ap01m_dir = os.path.join(tmpdir, "AP01m")
        os.makedirs(ap01m_dir)
        
        # Create .log files with naming that doesn't match directory
        fbc_file = os.path.join(ap01m_dir, "different_name_FBC.log")
        
        # Write test content to file
        with open(fbc_file, "w") as f:
            f.write("test log content")
        
        # Initialize NodeManager with test configuration
        manager = NodeManager()
        manager.log_root = tmpdir
        
        # Create node with expected tokens
        node = Node(name="AP01m", ip_address="192.168.1.101")
        
        # Add token
        token_162 = NodeToken(
            name="AP01m 162",
            token_id="162",
            token_type="FBC",
            ip_address="192.168.1.101",
            port=2077
        )
        node.add_token(token_162)
        
        manager.nodes = {"AP01m": node}
        
        # Scan log files
        manager.scan_log_files()
        
        # Verify that file is correctly mapped to node based on directory name
        assert token_162.log_path == fbc_file, f"Expected {fbc_file}, got {token_162.log_path}"

if __name__ == "__main__":
    test_ap01m_fbc_token_detection_from_log_files()
    test_log_file_token_type_detection()
    test_mixed_file_types_in_same_directory()
    test_directory_based_node_name_extraction()
    print("All tests passed!")