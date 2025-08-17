#!/usr/bin/env python3
"""
Test script for sequential token processing implementation.
"""
import sys
import os
import logging

# Add src to path so we can import commander modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from commander.models import NodeToken
from commander.services.sequential_command_processor import SequentialCommandProcessor

# Mock classes for testing
class MockCommandQueue:
    def __init__(self):
        self.commands = []
        # Add mock signals
        self.command_completed = MockSignal()
        self.progress_updated = MockSignal()
        self.processor = None  # Reference to the processor for callbacks
        
    def add_command(self, command, token, telnet_client=None):
        print(f"MockCommandQueue.add_command: {command} for token {token.token_id}")
        self.commands.append((command, token, telnet_client))
        # Simulate immediate completion
        if self.processor:
            self.processor._on_command_completed(command, "Success", True, token)
        
    def start_processing(self):
        print("MockCommandQueue.start_processing called")
        
    def clear_queue(self):
        self.commands = []

class MockSignal:
    def connect(self, handler):
        pass
        
    def emit(self, *args) -> None:
        pass

class MockFbcService:
    class MockNodeManager:
        def get_node(self, node_name) -> None:
            return None
            
    def __init__(self):
        self.node_manager = self.MockNodeManager()

class MockRpcService:
    class MockNodeManager:
        def get_node(self, node_name) -> None:
            return None
            
    def __init__(self):
        self.node_manager = self.MockNodeManager()

class MockSessionManager:
    pass

class MockLoggingService:
    def start_batch_logging(self, batch_id, node_name, token_count):
        print(f"MockLoggingService.start_batch_logging: batch_id={batch_id}, node_name={node_name}, token_count={token_count}")
        
    def end_batch_logging(self, batch_id, node_name, success_count, total_count):
        print(f"MockLoggingService.end_batch_logging: batch_id={batch_id}, node_name={node_name}, success_count={success_count}, total_count={total_count}")        
    
    def open_log_for_token(self, token_id, node_name, node_ip, protocol, batch_id):
        print(f"MockLoggingService.open_log_for_token: token_id={token_id}, node_name={node_name}, protocol={protocol}")
        return f"/mock/log/{node_name}_{token_id}_{protocol}.log"
        
    def close_log_for_token(self, token_id, protocol, batch_id):
        print(f"MockLoggingService.close_log_for_token: token_id={token_id}, protocol={protocol}")
        
    def log(self, message):
        print(f"MockLoggingService.log: {message}")


def test_sequential_processing(): 
    """Test sequential processing with mixed FBC and RPC tokens using simulated completion"""
    print("Testing sequential token processing...")
    
    # Create mock services
    command_queue = MockCommandQueue()
    fbc_service = MockFbcService()
    rpc_service = MockRpcService()
    session_manager = MockSessionManager()
    logging_service = MockLoggingService()
    
    # Create processor
    processor = SequentialCommandProcessor(
        command_queue=command_queue,
        fbc_service=fbc_service,
        rpc_service=rpc_service,
        session_manager=session_manager,
        logging_service=logging_service
    )
    
    # Set processor reference in command queue
    command_queue.processor = processor
    
    # Create test tokens
    tokens = [ 
        NodeToken(token_id="162", token_type="FBC", node_ip="192.168.0.11"),
        NodeToken(token_id="163", token_type="RPC", node_ip="192.168.0.11"),
        NodeToken(token_id="164", token_type="FBC", node_ip="192.168.0.11"),
        NodeToken(token_id="165", token_type="RPC", node_ip="192.168.0.11")
    ]
    
    # Process tokens sequentially
    print("\nProcessing tokens sequentially...")
    processor.process_tokens_sequentially("AP01m", tokens)
    
    # Check results
    print(f"\nCommands added to queue: {len(command_queue.commands)}")
    for i, (command, token, telnet_client) in enumerate(command_queue.commands):
        print(f"  {i+1}. Command: '{command}' for {token.token_type} token {token.token_id}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Run test
    test_sequential_processing()