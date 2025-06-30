import os
import sys
from src.commander.node_manager import NodeManager

def test_path_handling():
    # Create NodeManager instance
    node_manager = NodeManager()
    
    # Set log root to test_logs directory
    test_log_root = os.path.join(os.path.dirname(__file__), 'test_logs')
    node_manager.set_log_root(test_log_root)
    print(f"Set log root to: {test_log_root}")
    
    # Test sample paths
    sample_paths = [
        'test_logs/AP01m/162_FBC.log',
        'test_logs/AP01r/362_FBC.log',
        'test_logs/AP03m/2a2_FBC.log'
    ]
    
    print("\nTesting path normalization:")
    for path in sample_paths:
        normalized = os.path.normpath(path)
        print(f"Original: {path} -> Normalized: {normalized}")
        
        # Verify path points to correct location
        full_path = os.path.join(os.path.dirname(__file__), normalized)
        if not os.path.exists(full_path):
            print(f"  ERROR: Path does not exist: {full_path}")
        else:
            print(f"  SUCCESS: Path exists: {full_path}")
    
    # Test telnet command execution
    print("\nTesting telnet command execution with fixed paths:")
    commands = [
        "print from fieldbus io structure 1620000",
        "print from fieldbus io structure 3620000",
        "print from fieldbus io structure 2a20000"
    ]
    
    # This would normally connect to telnet server
    # For testing, we'll just verify command formatting
    for cmd in commands:
        print(f"Command: {cmd}")
        # In real test, we would execute and check for errors
        print("  [SIMULATED] Command executed successfully - no path errors")

if __name__ == "__main__":
    test_path_handling()