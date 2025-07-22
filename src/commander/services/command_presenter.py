"""
Command Presenter - Handles business logic and coordinates between view and model
"""
import logging
import re
import socket
import threading
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QIcon
from ..models import NodeToken
from ..node_manager import NodeManager
from ..session_manager import SessionManager, SessionType, SessionConfig
from ..log_writer import LogWriter
from ..commands.telnet_commands import CommandResolver
from ..command_queue import CommandQueue
from .fbc_command_service import FbcCommandService
from .rpc_command_service import RpcCommandService

class CommandPresenter(QObject):
    """Handles business logic and coordinates between view and model"""
    
    # Status message durations in milliseconds
    STATUS_MSG_SHORT = 3000
    STATUS_MSG_MEDIUM = 5000
    STATUS_MSG_LONG = 10000
    
    # Compiled regex patterns for token extraction
    FBC_TOKEN_PATTERN = re.compile(r"^([\w-]+)_[\d\.-]+_([\w-]+)\.")
    RPC_TOKEN_PATTERN = re.compile(r"_([\d\w-]+)\.[^.]*$")
    LIS_TOKEN_PATTERN = re.compile(r"^([\w-]+)_[\d-]+_([\d\w-]+)\.lis$")
    
    # Signals
    command_finished = pyqtSignal(str, bool)
    queue_processed = pyqtSignal(int, int)
    status_message_signal = pyqtSignal(str, int)
    
    def __init__(self, view, node_manager: NodeManager, session_manager: SessionManager, 
                 log_writer: LogWriter, command_queue: CommandQueue,
                 fbc_service: FbcCommandService, rpc_service: RpcCommandService):
        super().__init__()
        self.view = view
        self.node_manager = node_manager
        self.session_manager = session_manager
        self.log_writer = log_writer
        self.command_queue = command_queue
        self.fbc_service = fbc_service
        self.rpc_service = rpc_service
        self.command_resolver = CommandResolver()
        self.telnet_lock = threading.Lock()
        self.current_token = None
        self.active_telnet_client = None
        
        # Connect signals
        self.command_finished.connect(self.on_telnet_command_finished)
        self.command_queue.command_completed.connect(self._handle_queued_command_result)
        
    def _report_error(self, message: str, exception: Exception = None, duration: int = None):
        """Centralized error reporting"""
        duration = duration or self.STATUS_MSG_MEDIUM
        error_msg = f"{message}: {str(exception)}" if exception else message
        logging.error(error_msg)
        self.status_message_signal.emit(error_msg, duration)
        
    def process_fieldbus_command(self, token_id, node_name):
        """Process fieldbus command with optimized error handling"""
        logging.debug(f"Processing Fieldbus command: token_id={token_id}, node_name={node_name}")
        try:
            token = self.fbc_service.get_token(node_name, token_id)
            telnet_client = self.active_telnet_client if hasattr(self, 'active_telnet_client') else None
            self.fbc_service.queue_fieldbus_command(node_name, token_id, telnet_client)
            self.command_queue.start_processing()
            
            command = self.fbc_service.generate_fieldbus_command(token_id)
            self.view.telnet_output.append(f"> {command}")
            self.view.telnet_output.moveCursor(QTextCursor.MoveOperation.End)
        except (ConnectionRefusedError, TimeoutError) as e:
            self._report_error(f"{type(e).__name__} processing command", e)
        except Exception as e:
            self._report_error("Unexpected error processing command", e)
            
    def process_rpc_command(self, token_id, action_type):
        """Process RPC commands with token validation and auto-execute"""
        if action_type not in ["print", "clear"]:
            return
            
        try:
            if not token_id or not isinstance(token_id, str):
                raise ValueError("Invalid token ID")
                
            token_num = token_id.split('_')[-1]
            command_text = (
                f"print from fbc rupi counters {token_num}0000"
                if action_type == "print"
                else f"clear fbc rupi counters {token_num}0000"
            )
            
            logging.debug(f"Context menu command: {action_type} for token {token_id}")
            
            self.view.cmd_input.setPlainText(command_text)
            self.view.session_tabs.setCurrentWidget(self.view.telnet_tab)
            self.view.cmd_input.setFocus()
            
            self.view.telnet_output.append(f"> {command_text}")
            self.view.telnet_output.moveCursor(QTextCursor.MoveOperation.End)
            
            if hasattr(self, 'active_telnet_client') and self.active_telnet_client and self.active_telnet_client.is_connected:
                logging.debug("Reusing active telnet connection for context command")
                self.view.telnet_session = self.active_telnet_client
            elif not self.view.telnet_session or not self.view.telnet_session.is_connected:
                try:
                    ip, port_text = self.view.telnet_connection_bar.get_address()
                    port = int(port_text) if port_text else 23
                    if not self.connect_telnet(ip, port):
                        raise ConnectionError(f"Failed to connect to manual telnet at {ip}:{port}")
                    self.active_telnet_client = self.view.telnet_session
                except Exception as e:
                    self._report_error("Connection error", e)
                    return
            
            self.execute_telnet_command(automatic=True)
            
            action_name = "Print" if action_type == "print" else "Clear"
            self.status_message_signal.emit(
                f"{action_name} Rupi counters for token {token_num}", 
                self.STATUS_MSG_SHORT
            )
        except ValueError as e:
            self._report_error("Invalid RPC command parameters", e)
        except AttributeError as e:
            self._report_error("UI component access error", e)
        except Exception as e:
            logging.error(f"Unexpected error in RPC command setup: {str(e)}")
            self._report_error("RPC command setup failed", e)
            
    def toggle_telnet_connection(self, connect: bool):
        """Toggles connection/disconnection for Telnet tab"""
        ip_address, port_text = self.view.telnet_connection_bar.get_address()
        if not ip_address or not port_text:
            self.status_message_signal.emit("IP and port are required.", self.STATUS_MSG_SHORT)
            self.view.telnet_connection_bar.update_status(ConnectionState.ERROR)
            return
        
        try:
            port = int(port_text)
        except ValueError:
            self.status_message_signal.emit(f"Invalid port number: {port_text}", self.STATUS_MSG_SHORT)
            self.view.telnet_connection_bar.update_status(ConnectionState.ERROR)
            return
            
        if connect:
            self.view.settings.setValue("telnet_ip", ip_address)
            self.view.settings.setValue("telnet_port", port_text)
            self.connect_telnet(ip_address, port)
            self.active_telnet_client = self.view.telnet_session
        else:
            self.disconnect_telnet()
            self.active_telnet_client = None

    def connect_telnet(self, ip_address: str, port: int):
        """Connects to specified telnet server using provided IP and port"""
        config = SessionConfig(
            host=ip_address,
            port=port,
            session_type=SessionType.TELNET,
            username="",
            password=""
        )
        
        try:
            self.view.telnet_connection_bar.update_status(ConnectionState.CONNECTING)
            self.view.telnet_session = self.session_manager.create_session(config)
            
            if self.view.telnet_session and self.view.telnet_session.is_connected:
                self.view.telnet_output.clear()
                self.view.telnet_output.append(f"Connected to {ip_address}:{port}")
                self.view.telnet_connection_bar.update_status(ConnectionState.CONNECTED)
                self.view.cmd_input.setFocus()
                return True
                
            self.status_message_signal.emit("Connection failed", self.STATUS_MSG_SHORT)
            self.view.telnet_connection_bar.update_status(ConnectionState.ERROR)
            return False
            
        except socket.timeout as e:
            self.status_message_signal.emit(f"Connection timed out: {str(e)}", self.STATUS_MSG_MEDIUM)
            self.view.telnet_connection_bar.update_status(ConnectionState.ERROR)
        except ConnectionRefusedError as e:
            self.status_message_signal.emit(f"Connection refused: {str(e)}", self.STATUS_MSG_MEDIUM)
            self.view.telnet_connection_bar.update_status(ConnectionState.ERROR)
        except Exception as e:
            self.status_message_signal.emit(f"Connection error: {str(e)}", self.STATUS_MSG_MEDIUM)
            self.view.telnet_connection_bar.update_status(ConnectionState.ERROR)
            return False
    
    def disconnect_telnet(self):
        """Disconnects from current telnet session"""
        try:
            self.session_manager.close_all_sessions()
            self.view.telnet_session = None
            self.view.telnet_connection_bar.update_status(ConnectionState.DISCONNECTED)
            self.view.telnet_output.append("\n>>> DISCONNECTED")
        except Exception as e:
            self.view.telnet_output.append(f"Error disconnecting: {str(e)}")
            self.view.telnet_connection_bar.update_status(ConnectionState.DISCONNECTED)
            
    def execute_telnet_command(self, automatic=False):
        """Executes command in Telnet session using background thread"""
        if hasattr(self, 'active_telnet_client') and self.active_telnet_client and self.active_telnet_client.is_connected:
            self.view.telnet_session = self.active_telnet_client
            
        if not self.view.telnet_session:
            if not automatic:
                self.status_message_signal.emit("Create a Telnet session first!", self.STATUS_MSG_SHORT)
            logging.debug("Telnet session not available for command execution")
            return ""
        
        command = self.view.cmd_input.toPlainText().strip()
        if not command:
            logging.debug("Empty command received in execute_telnet_command")
            return ""
        logging.debug(f"Executing telnet command: {command} (automatic={automatic})")
            
        if not automatic:
            self.view.command_history.add(command)
            self.view.telnet_output.append(f"> {command}")
            self.view.telnet_output.moveCursor(QTextCursor.MoveOperation.End)
            self.view.execute_btn.setEnabled(False)
        
        threading.Thread(
            target=self._run_telnet_command,
            args=(command, automatic),
            daemon=True
        ).start()
        
        return ""

    def _run_telnet_command(self, command, automatic):
        """Runs telnet command in background thread with improved error handling"""
        with self.telnet_lock:
            try:
                token_id = self.current_token.token_id if self.current_token else ""
                resolved_cmd = self.command_resolver.resolve(command, token_id)
                response = self.view.telnet_session.send_command(resolved_cmd, timeout=5)
                self.view.telnet_connection_bar.update_status(ConnectionState.CONNECTED)
            except (ConnectionRefusedError, TimeoutError, socket.timeout) as e:
                response = f"ERROR: {type(e).__name__} - {str(e)}"
                self._handle_connection_error(e)
            except Exception as e:
                response = f"ERROR: {type(e).__name__} - {str(e)}"
                logging.error(f"Telnet command failed: {command}", exc_info=True)
            
            logging.debug(f"Emitting command_finished signal for command: {command}")
            self.command_finished.emit(response, automatic)
            
    def _handle_connection_error(self, error):
        """Centralized connection error handling"""
        error_type = type(error).__name__
        if error_type in ["ConnectionRefusedError", "TimeoutError", "socket.timeout"]:
            self.view.telnet_connection_bar.update_status(ConnectionState.ERROR)
            self.status_message_signal.emit(f"Connection error: {str(error)}", self.STATUS_MSG_MEDIUM)

    def process_all_fbc_subgroup_commands(self, item):
        """Process all FBC commands using command queue"""
        try:
            section_item = item.parent()
            if not section_item:
                raise ValueError("FBC subgroup has no parent section")
            node_item = section_item.parent()
            if not node_item:
                raise ValueError(f"Section {section_item.text(0)} has no parent node")
            node_name = node_item.text(0).split(' ', 1)[0].strip()
            
            node = self.node_manager.get_node(node_name)
            if not node:
                self.status_message_signal.emit(f"Node {node_name} not found", self.STATUS_MSG_SHORT)
                return
                
            fbc_tokens = [t for t in node.tokens.values() if t.token_type == "FBC"]
            if not fbc_tokens:
                self.status_message_signal.emit(f"No FBC tokens found in node {node_name}", self.STATUS_MSG_SHORT)
                return
                
            self.status_message_signal.emit(f"Processing {len(fbc_tokens)} FBC tokens in node {node_name}...", 0)
            
            for token in fbc_tokens:
                command_text = f"print from fbc io structure {token.token_id}0000"
                self.command_queue.add_command(command_text, token)
                
            self.status_message_signal.emit(f"Queued {len(fbc_tokens)} commands for node {node_name}", self.STATUS_MSG_SHORT)
            self.command_queue.start_processing()
            
        except Exception as e:
            self.status_message_signal.emit(f"Error processing FBC commands: {str(e)}", self.STATUS_MSG_MEDIUM)

    def process_all_rpc_subgroup_commands(self, item):
        """Process all RPC commands using command queue"""
        try:
            section_item = item.parent()
            if not section_item:
                raise ValueError("RPC subgroup has no parent section")
            node_item = section_item.parent()
            if not node_item:
                raise ValueError(f"Section {section_item.text(0)} has no parent node")
            node_name = node_item.text(0).split(' ', 1)[0].strip()
            
            node = self.node_manager.get_node(node_name)
            if not node:
                self.status_message_signal.emit(f"Node {node_name} not found", self.STATUS_MSG_SHORT)
                return
                
            rpc_tokens = [t for t in node.tokens.values() if t.token_type == "RPC"]
            if not rpc_tokens:
                self.status_message_signal.emit(f"No RPC tokens found in node {node_name}", self.STATUS_MSG_SHORT)
                return
                
            self.status_message_signal.emit(f"Processing {len(rpc_tokens)} RPC tokens in node {node_name}...", 0)
            
            for token in rpc_tokens:
                command_text = f"print from fbc rupi counters {token.token_id}0000"
                self.command_queue.add_command(command_text, token)
                
            self.status_message_signal.emit(f"Queued {len(rpc_tokens)} commands for node {node_name}", self.STATUS_MSG_SHORT)
            self.command_queue.start_processing()
            
        except Exception as e:
            self.status_message_signal.emit(f"Error processing RPC commands: {str(e)}", self.STATUS_MSG_MEDIUM)
            
    def _handle_queued_command_result(self, command: str, result: str, success: bool):
        """Handle completed commands from the queue and log results"""
        logging.debug(f"_handle_queued_command_result: command={command}, success={success}, result_length={len(result)}")
        if success:
            self.status_message_signal.emit(f"Command succeeded: {command}", self.STATUS_MSG_SHORT)
            logging.info(f"Command completed successfully: {command}\nResult: {result}")
            
            token = None
            for queued_command in self.command_queue.queue:
                if queued_command.command == command:
                    token = queued_command.token
                    break
            
            if token and hasattr(token, 'token_id'):
                try:
                    self.log_writer.append_to_log(
                        token.token_id,
                        f"{command}\n{result}",
                        protocol=token.token_type
                    )
                except Exception as e:
                    logging.error(f"Failed to log command result: {str(e)}")
        else:
            self.status_message_signal.emit(f"Command failed: {command} - {result}", self.STATUS_MSG_MEDIUM)
            logging.error(f"Command failed: {command}\nError: {result}")
    
    def on_telnet_command_finished(self, response, automatic):
        """
        Handles the completion of a telnet command
        :param response: The command response text
        :param automatic: True if automatically triggered
        """
        logging.info(f"Telnet command finished (automatic={automatic}), response length: {len(response)}")
        
        if automatic:
            self.view.telnet_output.append(f"{response}\n")
        else:
            self.view.telnet_output.append(response)
        self.view.telnet_output.moveCursor(QTextCursor.MoveOperation.End)
        
        if not automatic:
            self.view.execute_btn.setEnabled(True)
            self.view.cmd_input.clear()
            
            if self.current_token and response.strip():
                try:
                    logging.debug(f"Processing manual command for token {self.current_token.token_id}")
                    node = self.node_manager.get_node_by_token(self.current_token)
                    if node:
                        node_ip = node.ip_address.replace('.', '-') if node.ip_address else "unknown-ip"
                        log_path = self.log_writer.log_paths.get(self.current_token.token_id)
                        if not log_path:
                            logging.debug(f"Opening new log for token {self.current_token.token_id}")
                            log_path = self.log_writer.open_log(node.name, node_ip, self.current_token)
                            
                        self.log_writer.append_to_log(self.current_token.token_id, response, protocol=self.current_token.token_type)
                        logging.info(f"Successfully appended to log: {os.path.basename(log_path)}")
                        self.status_message_signal.emit(f"Command output appended to {os.path.basename(log_path)}", self.STATUS_MSG_SHORT)
                    else:
                        logging.warning(f"Node not found for token {self.current_token.token_id}")
                        self.status_message_signal.emit(f"Node not found for token {self.current_token.token_id}", self.STATUS_MSG_SHORT)
                except Exception as e:
                    logging.error(f"Failed to write to log: {str(e)}", exc_info=True)
                    self.status_message_signal.emit(f"Log write failed: {str(e)}", self.STATUS_MSG_MEDIUM)
        else:
            if response.strip() and self.current_token:
                try:
                    log_path = getattr(self.current_token, 'log_path', None)
                    if log_path:
                        with open(log_path, 'a') as f:
                            f.write(response + "\n")
                        self.status_message_signal.emit(
                            f"Command output appended to {os.path.basename(log_path)}",
                            self.STATUS_MSG_SHORT
                        )
                    else:
                        self.log_writer.append_to_log(
                            self.current_token.token_id,
                            response,
                            protocol=self.current_token.token_type
                        )
                        self.status_message_signal.emit("Command output logged", self.STATUS_MSG_SHORT)
                except Exception as e:
                    logging.error(f"Log write error: {str(e)}")
                    self.status_message_signal.emit(f"Log write failed: {str(e)}", self.STATUS_MSG_MEDIUM)
            elif response.strip():
                self.status_message_signal.emit("Command executed successfully", self.STATUS_MSG_SHORT)
            else:
                self.status_message_signal.emit("Empty response received", self.STATUS_MSG_SHORT)