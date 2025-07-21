from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool
from typing import List, Optional
from .models import NodeToken
from .session_manager import SessionConfig, SessionType
import logging
import socket
import time

logger = logging.getLogger(__name__)

def log_with_exc_info(msg, *args, **kwargs):
    exc_info = kwargs.pop('exc_info', None)
    if exc_info is None and 'exc' in kwargs:
        exc_info = kwargs.pop('exc')
    logger.log(msg, *args, exc_info=exc_info, **kwargs)

@dataclass
class QueuedCommand:
    """Represents a command in the execution queue"""
    command: str
    token: NodeToken
    status: str = 'pending'  # pending|processing|completed|failed
    telnet_client: object = None   # Optional active telnet client to use

class CommandWorkerSignals(QObject):
    finished = pyqtSignal(object, str)  # Emits (worker, result)
    command_completed = pyqtSignal(str, str, bool)  # Emits (command, result, success)

class CommandWorker(QRunnable):
    """Worker for executing a single command in a thread"""
    
    def __init__(self, command: str, token: NodeToken, telnet_session=None):
        super().__init__()
        self.command = command
        self.token = token
        self.telnet_session = telnet_session
        self.result = None
        self.success = False
        self.signals = CommandWorkerSignals()
        
    def run(self):
        """Execute the command and store the result"""
        logging.debug(f"CommandWorker.run: Starting execution of command: {self.command}")
        logging.debug(f"CommandWorker.run: Node: {self.token.name} ({self.token.ip_address})")
        logging.debug(f"CommandWorker.run: Token: {self.token.token_id} ({self.token.token_type})")
        
        try:
            # Enhanced session verification with socket-level checks
            max_retries = 3
            retry_delay = 1.0  # Increased delay for more reliable reconnection
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    if not self.telnet_session:
                        logging.error("CommandWorker.run: No telnet session available")
                        raise ConnectionError("No telnet session available")
                        
                    # Attempt to reconnect if session is disconnected
                    if not self.telnet_session.is_connected:
                        logging.debug("CommandWorker.run: Session disconnected, attempting to reconnect")
                        try:
                            self.telnet_session.connect()
                        except Exception as e:
                            logging.error(f"CommandWorker.run: Reconnect failed: {str(e)}")
                            raise ConnectionError(f"Reconnect failed: {str(e)}")
                            
                    # Check both application-level and socket-level connection
                    if not self.telnet_session.is_connected:
                        logging.error("CommandWorker.run: Application reports disconnected after reconnect attempt")
                        raise ConnectionError("Application reports disconnected after reconnect attempt")
                        
                    sock = self.telnet_session.connection.get_socket()
                    if not sock:
                        logging.error("CommandWorker.run: No socket available")
                        raise ConnectionError("No socket available")
                        
                    # Skip socket test to prevent ConnectionAbortedError
                    logging.debug("CommandWorker.run: Skipping socket test to prevent connection issues")
                    break
                    
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logging.warning(
                            f"Connection verification failed (attempt {attempt + 1}/{max_retries}): {str(e)}\n"
                            f"Command: {self.command}\n"
                            f"Node: {self.token.name} ({self.token.ip_address})"
                        )
                        time.sleep(retry_delay)
                        continue
                        
                    # Final attempt failed
                    error_msg = (
                        f"Telnet connection verification failed after {max_retries} attempts\n"
                        f"Command: {self.command}\n"
                        f"Token: {self.token.token_id} ({self.token.token_type})\n"
                        f"Node: {self.token.name} ({self.token.ip_address})\n"
                        f"Last error: {str(last_error)}"
                    )
                    logging.error(error_msg)
                    raise ConnectionError(error_msg)
                
            # Execute command via Telnet session
            logging.debug(f"CommandWorker.run: Sending command to telnet session: {self.command}")
            self.result = self.telnet_session.send_command(self.command)
            logging.debug(f"CommandWorker.run: Raw response received (length={len(self.result)}): {self.result[:200]}{'...' if len(self.result) > 200 else ''}")
            
            # Verify command execution
            if not self.result:
                logging.warning("Empty response received from command execution")
                # Consider empty response as successful but log warning
                self.success = True
            elif "error" in self.result.lower():
                raise ValueError(f"Command returned error response: {self.result[:200]}")
            else:
                if len(self.result) < 10:  # Minimum expected response length
                    logging.warning(f"CommandWorker.run: Unexpectedly short response: {len(self.result)} chars")
                self.success = True
            logging.info(f"CommandWorker.run: Command executed successfully: {self.command}")
            logging.debug(f"CommandWorker.run: Final processed response length: {len(self.result)}")
            
        except Exception as e:
            import traceback
            error_details = (
                f"CommandWorker.run: Command failed: {self.command}\n"
                f"Token: {self.token.token_id} ({self.token.token_type})\n"
                f"Node: {self.token.name} ({self.token.ip_address})\n"
                f"Error: {str(e)}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            logging.error(error_details)
            self.result = f"Command failed: {str(e)}"
            self.success = False
            # Re-raise to ensure proper error propagation
            raise
        finally:
            logging.debug(f"CommandWorker.run: Finished command: {self.command}, success={self.success}")
            self.signals.finished.emit(self, self.result)
            self.signals.command_completed.emit(self.command, self.result, self.success)

class CommandQueue(QObject):
    """Manages a queue of commands to execute with progress tracking"""
    
    command_completed = pyqtSignal(str, str, bool)  # command, result, success
    progress_updated = pyqtSignal(int, int)    # current, total
    
    def __init__(self, session_manager=None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.queue: List[QueuedCommand] = []
        self.thread_pool = QThreadPool.globalInstance()
        self.completed_count = 0
        self.session_manager = session_manager
        
    def add_command(self, command: str, token: NodeToken, telnet_client=None):
        """Add a command to the queue with associated token"""
        qc = QueuedCommand(
            command=command,
            token=token,
            telnet_client=telnet_client
        )
        self.queue.append(qc)
        logging.debug(f"CommandQueue.add_command: Added command '{command}' for token {token.token_id}")
        logging.debug(f"CommandQueue.add_command: Token details - type: {token.token_type}, node: {token.name} ({token.ip_address})")
        logging.debug(f"CommandQueue.add_command: Current queue size: {len(self.queue)}")
        logging.debug(f"CommandQueue.add_command: QueuedCommand object created: {qc}")
        
        # Automatically start processing when adding first command
        if len(self.queue) == 1:
            self.start_processing()
        
    def start_processing(self):
        """Start processing all commands in the queue"""
        if not self.session_manager:
            logging.error("CommandQueue.start_processing: No session_manager available - cannot process commands")
            return

        logging.info(f"CommandQueue.start_processing: Starting processing of {len(self.queue)} commands")
        logging.debug(f"CommandQueue.start_processing: Queue contents: {[qc.command for qc in self.queue]}")
        logging.debug(f"CommandQueue.start_processing: Thread pool status - active threads: {self.thread_pool.activeThreadCount()}, max threads: {self.thread_pool.maxThreadCount()}")
        
        self.completed_count = 0
        total = len(self.queue)
        if total == 0:
            logging.info("CommandQueue.start_processing: Queue is empty, nothing to process")
            return
            
        # Update all commands to processing status
        for idx, item in enumerate(self.queue):
            item.status = 'processing'
            logging.debug(f"CommandQueue.start_processing: Marked command {idx+1}/{total} as processing: {item.command}")
            
        # Create and start workers for each command
        for idx, item in enumerate(self.queue):
            telnet_session = None
            # Prioritize using the provided telnet_client if available
            if item.telnet_client:
                telnet_session = item.telnet_client
                logging.debug(f"CommandQueue.start_processing: Using provided telnet client for command {idx+1}: {item.command} (connected: {telnet_session.is_connected})")
                # Add debug log about client reuse
                if telnet_session == self.parent().active_telnet_client:
                    logging.debug("CommandQueue.start_processing: Reusing active manual Telnet connection")
            else:
                try:
                    # Get telnet session from session manager
                    session_key = f"{item.token.name}_{item.token.token_type}"
                    config = SessionConfig(
                        host=item.token.ip_address,
                        port=23,
                        session_type=SessionType.TELNET
                    )
                    telnet_session = self.session_manager.get_or_create_session(
                        session_key,
                        SessionType.TELNET,
                        config
                    )
                    if not telnet_session:
                        logging.error(f"CommandQueue.start_processing: Failed to create session for {session_key}")
                        item.status = 'failed'
                        continue
                        
                    logging.debug(f"CommandQueue.start_processing: Created session for {session_key} at {item.token.ip_address}:23")
                except Exception as e:
                    logging.error(f"CommandQueue.start_processing: Error creating session for {session_key}: {str(e)}")
                    item.status = 'failed'
                    continue

            worker = CommandWorker(item.command, item.token, telnet_session)
            logging.debug(f"CommandQueue.start_processing: Created worker for command {idx+1}/{total}: {item.command} (token {item.token.token_id})")
            worker.setAutoDelete(True)
            worker.signals.finished.connect(lambda w=worker: self._handle_worker_finished(w))
            self.thread_pool.start(worker)
            logging.debug(f"CommandQueue.start_processing: Started worker for command {idx+1}/{total}")
        
    def _handle_worker_finished(self, worker: CommandWorker):
        """Handle completion of a worker thread"""
        self.completed_count += 1
        success = worker.success
        command = worker.command
        result = worker.result
        
        # Log command execution result with error details if failed
        log_msg = (
            f"Command {'completed' if success else 'failed'}: {command}\n"
            f"Node: {getattr(worker.token, 'name', 'N/A')} "
            f"({getattr(worker.token, 'ip_address', 'N/A')})\n"
            f"Token: {worker.token.token_id} ({worker.token.token_type})\n"
        )
        if not success:
            log_msg += f"ERROR DETAILS: {result}\n"
        log_msg += f"Result: {result[:500]}{'...' if len(result) > 500 else ''}"
        logging.info(log_msg)
        
        # Update command status
        updated = False
        for idx, item in enumerate(self.queue):
            if item.command == command:
                item.status = 'completed' if success else 'failed'
                logging.debug(f"CommandQueue._handle_worker_finished: Updated status for command {idx+1}/{len(self.queue)}: {command} -> {item.status}")
                updated = True
                break
        
        if not updated:
            logging.error(f"CommandQueue._handle_worker_finished: Could not find command in queue: {command}")
        
        # Emit progress update
        remaining = len(self.queue) - self.completed_count
        logging.debug(f"CommandQueue._handle_worker_finished: Progress: {self.completed_count}/{len(self.queue)} completed, {remaining} remaining")
        self.progress_updated.emit(self.completed_count, len(self.queue))
        
        # Emit command completion with result
        # Ensure error details are properly propagated
        self.command_completed.emit(command, result, success)
        logging.debug(f"CommandQueue._handle_worker_finished: Emitted completion signal for command: {command} (success={success})")
        
        # If this was the last command, emit final completion signal
        if self.completed_count >= len(self.queue):
            logging.info("CommandQueue._handle_worker_finished: All commands processed")
        
    def validate_token(self, token: NodeToken) -> bool:
        """Validate token has required fields"""
        return bool(token and token.token_id and token.token_type)