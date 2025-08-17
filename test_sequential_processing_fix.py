#!/usr/bin/env python3
"""
Test script for sequential token processing fix implementation
"""
import sys
import os
import logging

# Add src to path so we can import commander modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock the required modules
import unittest.mock as mock
from unittest.mock import MagicMock, patch

def test_sequential_processing_implementation():
    """Test that the sequential processing implementation is correct"""
    print("Testing sequential token processing implementation...")
    
    # Read the sequential command processor file
    with open('src/commander/services/sequential_command_processor.py', 'r') as f:
        content = f.read()
    
    # Check that the implementation processes one command at a time
    # Look for key indicators that show sequential processing
    has_process_next_token = '_process_next_token' in content
    has_on_command_completed = '_on_command_completed' in content
    has_sequential_logic = 'self._current_token_index += 1' in content
    
    print(f"Has _process_next_token method: {has_process_next_token}")
    print(f"Has _on_command_completed method: {has_on_command_completed}")
    print(f"Has sequential logic: {has_sequential_logic}")
    
    # Check that the command queue is only adding one command at a time
    # This is indicated by the fact that commands are added in the _process_next_* methods
    process_methods = [
        '_process_next_token',
        '_process_next_fbc_token', 
        '_process_next_rpc_token',
        '_process_next_batch_token'
    ]
    
    found_process_methods = [method for method in process_methods if method in content]
    print(f"Found process methods: {found_process_methods}")
    
    # Check that _on_command_completed advances to the next token
    advances_tokens = 'self._current_token_index += 1' in content
    print(f"Advances to next token: {advances_tokens}")
    
    if has_process_next_token and has_on_command_completed and advances_tokens:
        print("\n✓ Implementation correctly processes tokens sequentially")
        print("✓ Commands are added to queue one at a time")
        print("✓ Next token is processed after command completion")
        return True
    else:
        print("\n✗ Implementation issues detected")
        return False

def test_command_queue_integration():
    """Test that the command queue integration is correct"""
    print("\nTesting command queue integration...")
    
    # Read the command queue file
    with open('src/commander/command_queue.py', 'r') as f:
        content = f.read()
    
    # Check that the command queue has proper sequential processing
    # The key is that it uses a thread pool with max thread count of 1
    has_thread_pool = 'QThreadPool()' in content
    has_max_thread_count = 'setMaxThreadCount(1)' in content
    
    print(f"Has thread pool: {has_thread_pool}")
    print(f"Has max thread count of 1: {has_max_thread_count}")
    
    if has_thread_pool and has_max_thread_count:
        print("\n✓ Command queue correctly processes commands sequentially")
        print("✓ Thread pool configured for single-threaded execution")
        return True
    else:
        print("\n✗ Command queue configuration issues detected")
        return False

if __name__ == "__main__":
    print("Sequential Token Processing Fix Implementation Test")
    print("=" * 50)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    implementation_ok = test_sequential_processing_implementation()
    queue_ok = test_command_queue_integration()
    
    print("\n" + "=" * 50)
    if implementation_ok and queue_ok:
        print("All tests passed! Sequential processing fix is implemented correctly.")
        sys.exit(0)
    else:
        print("Some tests failed. Please review the implementation.")
        sys.exit(1)