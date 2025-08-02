"""
Logging Service - Handles all logging operations for the Commander application
"""
import logging
import os
from typing import Optional
from ..models import NodeToken
from ..log_writer import LogWriter
from ..node_manager import NodeManager


class LoggingService:
    """Service for handling logging operations"""
    
    # Status message durations in milliseconds
    STATUS_MSG_SHORT = 3000    # 3 seconds
    STATUS_MSG_MEDIUM = 5000   # 5 seconds
    STATUS_MSG_LONG = 10000    # 10 seconds
    
    def __init__(self, node_manager: NodeManager, log_writer: LogWriter):
        """
        Initialize the Logging service.
        
        Args:
            node_manager: Manager for node operations
            log_writer: Writer for log file operations
        """
        self.node_manager = node_manager
        self.log_writer = log_writer
        logging.debug("LoggingService initialized")
    
    def report_error(self, message: str, exception: Exception | None = None, duration: int | None = None):
        """
        Centralized error reporting with logging and status bar updates.
        
        Args:
            message: Error message to display
            exception: Optional exception that occurred
            duration: Duration to display message (milliseconds)
        """
        duration = duration or self.STATUS_MSG_MEDIUM
        error_msg = f"{message}: {str(exception)}" if exception else message
        logging.error(error_msg)
        logging.error(error_msg)  # Duplicate logging as in original
        
    def handle_fbc_error(self, error_msg: str):
        """
        Handle FBC service errors by reporting them.
        
        Args:
            error_msg: Error message from FBC service
        """
        self.report_error("FBC Service Error", Exception(error_msg))
        
    def handle_queued_command_result(self, command: str, result: str, success: bool, token=None):
        """
        Handle completed commands from the queue and log results.
        
        Args:
            command: Command that was executed
            result: Result of the command
            success: Whether the command succeeded
            token: Token associated with the command
        """
        logging.debug(f"_handle_queued_command_result: command={command}, success={success}, result_length={len(result)}")
        if success:
            logging.info(f"Command completed successfully: {command}\nResult: {result}")
        else:
            logging.error(f"Command failed: {command}\nError: {result}")
            
    def log_command_result(self, command: str, result: str, success: bool, token=None):
        """
        Log command results to the appropriate log file.
        
        Args:
            command: Command that was executed
            result: Result of the command
            success: Whether the command succeeded
            token: Token associated with the command
        """
        try:
            if token and hasattr(token, 'token_id') and hasattr(token, 'token_type'):
                self.log_writer.append_to_log(
                    token.token_id,
                    f"{command}\n{result}",
                    protocol=token.token_type
                )
            else:
                logging.warning(f"Unable to log command result: missing token information")
        except Exception as e:
            logging.error(f"Failed to log command result: {str(e)}")
    
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
        if not automatic:
            # For manual commands: re-enable button and clear input
            if execute_btn:
                execute_btn.setEnabled(True)
            if cmd_input:
                cmd_input.clear()
                
            # Only write to log for manual commands when explicitly requested
            if current_token and response.strip():
                try:
                    logging.debug(f"Processing manual command for token {current_token.token_id}")
                    node = node_manager.get_node_by_token(current_token)
                    if node:
                        node_ip = node.ip_address.replace('.', '-') if node.ip_address else "unknown-ip"
                        log_path = log_writer.log_paths.get(current_token.token_id)
                        if not log_path:
                            logging.debug(f"Opening new log for token {current_token.token_id}")
                            log_path = log_writer.open_log(node.name, node_ip, current_token, log_writer.get_log_path(node.name, node_ip, current_token))
                            
                        log_writer.append_to_log(current_token.token_id, response, protocol=current_token.token_type)
                        logging.info(f"Successfully appended to log: {os.path.basename(log_path)}")
                        if status_message_signal:
                            status_message_signal.emit(f"Command output appended to {os.path.basename(log_path)}", 3000)
                    else:
                        logging.warning(f"Node not found for token {current_token.token_id}")
                        if status_message_signal:
                            status_message_signal.emit(f"Node not found for token {current_token.token_id}", 3000)
                except Exception as e:
                    logging.error(f"Failed to write to log: {str(e)}", exc_info=True)
                    if status_message_signal:
                        status_message_signal.emit(f"Log write failed: {str(e)}", 5000)
        else:   # automatic commands
            if response.strip() and current_token:
                try:
                    # Check if token has a direct log path (from context menu)
                    log_path = getattr(current_token, 'log_path', None)
                    if log_path:
                        # Write directly to the specified log file
                        with open(log_path, 'a') as f:
                            f.write(response + "\n")
                        if status_message_signal:
                            status_message_signal.emit(
                                f"Command output appended to {os.path.basename(log_path)}",
                                3000
                            )
                    else:
                        # For automatic commands, always ensure we have a log file open
                        node = node_manager.get_node_by_token(current_token)
                        if node:
                            node_ip = node.ip_address.replace('.', '-') if node.ip_address else "unknown-ip"
                            # Always call open_log for automatic commands to ensure proper log path generation
                            log_writer.open_log(node.name, node_ip, current_token, log_writer.get_log_path(node.name, node_ip, current_token))
                        
                        # Fall back to standard log writer
                        log_writer.append_to_log(
                            current_token.token_id,
                            response,
                            protocol=current_token.token_type
                        )
                        if status_message_signal:
                            status_message_signal.emit(
                                "Command output logged",
                                3000
                            )
                except Exception as e:
                    logging.error(f"Log write error: {str(e)}")
                    if status_message_signal:
                        status_message_signal.emit(f"Log write failed: {str(e)}", 5000)
            elif response.strip() and status_message_signal:
                status_message_signal.emit("Command executed successfully", 3000)
            elif status_message_signal:
                status_message_signal.emit("Empty response received", 3000)