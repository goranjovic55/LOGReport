from ..models import NodeToken
from ..services.fbc_command_service import FbcCommandService
from ..services.rpc_command_service import RpcCommandService
from ..command_queue import CommandQueue
from ..log_writer import LogWriter
from ..node_manager import NodeManager
from ..session_manager import SessionManager
from ..services.logging_service import LoggingService
import logging
import os
from PyQt6.QtCore import pyqtSignal, QObject


class CommanderService(QObject):
    """Service for handling command execution logic"""
    
    # Signals for UI updates
    status_message = pyqtSignal(str, int)
    set_cmd_input_text = pyqtSignal(str)
    switch_to_telnet_tab = pyqtSignal()
    focus_command_input = pyqtSignal()
    report_error = pyqtSignal(str)
    command_finished = pyqtSignal(str, bool)  # response, automatic
    queue_processed = pyqtSignal(int, int)  # Success count, total
    
    def __init__(self, node_manager: NodeManager, session_manager: SessionManager,
                 command_queue: CommandQueue, log_writer: LogWriter,
                 fbc_service: FbcCommandService, rpc_service: RpcCommandService):
        super().__init__()
        self.node_manager = node_manager
        self.session_manager = session_manager
        self.command_queue = command_queue
        self.log_writer = log_writer
        self.fbc_service = fbc_service
        self.rpc_service = rpc_service
        
        # Initialize Logging Service
        self.logging_service = LoggingService(node_manager, log_writer)
        
        # Connect service signals
        self.fbc_service.set_command_text.connect(self.set_cmd_input_text)
        self.fbc_service.switch_to_telnet_tab.connect(self.switch_to_telnet_tab)
        self.fbc_service.focus_command_input.connect(self.focus_command_input)
        self.fbc_service.status_message.connect(self.status_message)
        self.fbc_service.report_error.connect(self.report_error)
        
        self.rpc_service.set_command_text.connect(self.set_cmd_input_text)
        self.rpc_service.switch_to_telnet_tab.connect(self.switch_to_telnet_tab)
        self.rpc_service.focus_command_input.connect(self.focus_command_input)
        self.rpc_service.status_message.connect(self.status_message)
        self.rpc_service.report_error.connect(self.report_error)
        
        self.command_queue.command_completed.connect(self._handle_queued_command_result)
        self.command_queue.command_completed.connect(self._log_command_result)
        self.command_queue.progress_updated.connect(self.queue_processed)
        
    def process_fieldbus_command(self, token_id, node_name):
        """Process fieldbus command with optimized error handling"""
        try:
            # First, try to queue the command
            # This will validate the node and token
            self.fbc_service.queue_fieldbus_command(node_name, token_id, None)
            self.command_queue.start_processing()
            
            # Only emit the "Executing" message after successful queuing
            command_text = self.fbc_service.generate_fieldbus_command(token_id)
            self.status_message.emit(f"Executing: {command_text}...", 3000)
        except ValueError as e:
            # If we get a ValueError, don't emit the "Executing" message
            # Just emit the error message
            self.status_message.emit(str(e), 3000)
        except Exception as e:
            logging.error(f"Error processing fieldbus command: {e}")
            self.status_message.emit(f"Error: {str(e)}", 5000)
            
    def process_rpc_command(self, node_name, token_id, action_type):
        """Process RPC commands with token validation and auto-execute"""
        try:
            self.rpc_service.queue_rpc_command(node_name, token_id, action_type)
            self.command_queue.start_processing()
        except ValueError as e:
            self.status_message.emit(str(e), 3000)
        except Exception as e:
            logging.error(f"Error processing RPC command: {e}")
            self.status_message.emit(f"Error: {str(e)}", 5000)
            
    def _handle_queued_command_result(self, command: str, result: str, success: bool, token=None):
        """Handle completed commands from the queue and log results"""
        logging.debug(f"_handle_queued_command_result: command={command}, success={success}, result_length={len(result)}")
        if success:
            self.status_message.emit(f"Command succeeded: {command}", 3000)
            logging.info(f"Command completed successfully: {command}\nResult: {result}")
        else:
            self.status_message.emit(f"Command failed: {command} - {result}", 5000)
            logging.error(f"Command failed: {command}\nError: {result}")
            
    def _log_command_result(self, command: str, result: str, success: bool, token=None):
        """Log command results to the appropriate log file"""
        self.logging_service.log_command_result(command, result, success, token)
    
    def log_telnet_command_finished(self, response: str, automatic: bool, current_token,
                                   node_manager, status_message_signal, log_writer,
                                   cmd_input=None, execute_btn=None):
        """
        Handle logging when a telnet command finishes execution.
        
        Args:
            response: Command response text
            automatic: True if command was triggered automatically
            current_token: Current token being processed
            node_manager: Node manager instance
            status_message_signal: Signal for status messages
            log_writer: Log writer instance
            cmd_input: Command input widget (for manual commands)
            execute_btn: Execute button widget (for manual commands)
        """
        self.logging_service.log_telnet_command_finished(
            response, automatic, current_token, node_manager,
            status_message_signal, log_writer, cmd_input, execute_btn
        )