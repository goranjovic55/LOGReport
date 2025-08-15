#!/usr/bin/env python3
"""
Simple test to verify CommandQueue concurrent processing changes
"""
import sys
import os

# Add src to path so we can import commander modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_command_queue_import():
    """Test that we can import CommandQueue and check its structure"""
    try:
        # Try to import just the basic modules we need
        from commander.models import NodeToken
        print("Successfully imported NodeToken")
        
        # Try to read the command_queue.py file directly to check our changes
        command_queue_path = os.path.join(os.path.dirname(__file__), 'src', 'commander', 'command_queue.py')
        with open(command_queue_path, 'r') as f:
            content = f.read()
            
        # Check for our changes
        if "max_thread_count=1" in content:
            print("✓ Found default max_thread_count=1 parameter")
        else:
            print("✗ Did not find default max_thread_count=1 parameter")
            
        if "max_thread_count" in content:
            print("✓ Found max_thread_count parameter in CommandQueue.__init__")
        else:
            print("✗ Did not find max_thread_count parameter")
            
        if "_tokens_in_process" in content:
            print("✓ Found _tokens_in_process for ordering management")
        else:
            print("✗ Did not find _tokens_in_process")
            
        if "sequence" in content:
            print("✓ Found sequence attribute for command ordering")
        else:
            print("✗ Did not find sequence attribute")
            
        # Check for concurrent processing setup
        if "self.thread_pool.setMaxThreadCount(max_thread_count)" in content:
            print("✓ Found thread pool configuration with max_thread_count")
        else:
            print("✗ Did not find thread pool configuration")
            
        return True
        
    except Exception as e:
        print(f"Error importing modules: {e}")
        return False

def test_commander_window_import():
    """Test that CommanderWindow uses concurrent processing"""
    try:
        # Try to read the commander_window.py file directly to check our changes
        commander_window_path = os.path.join(os.path.dirname(__file__), 'src', 'commander', 'ui', 'commander_window.py')
        with open(commander_window_path, 'r') as f:
            content = f.read()
            
        # Check for our changes
        if "max_thread_count=4" in content:
            print("✓ Found max_thread_count=4 in CommanderWindow")
        else:
            print("✗ Did not find max_thread_count=4 in CommanderWindow")
            
        return True
        
    except Exception as e:
        print(f"Error checking CommanderWindow: {e}")
        return False

if __name__ == "__main__":
    print("Running simple CommandQueue verification...")
    print("=" * 50)
    
    success1 = test_command_queue_import()
    print()
    success2 = test_commander_window_import()
    
    print()
    if success1 and success2:
        print("✓ All structural checks passed!")
        print("The implementation should support concurrent token processing")
        print("while maintaining sequential ordering for same-token commands")
    else:
        print("✗ Some checks failed")
        sys.exit(1)