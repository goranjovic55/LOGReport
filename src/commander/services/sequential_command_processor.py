"""
Sequential Command Processor - Handles memory-optimized, mode-adaptive iterative processing
 of FBC/RPC tokens with proper resource management.
"""

import logging
import gc
import weakref
from typing import List, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QCoreApplication
from typing import Tuple
import datetime

from collections import namedtuple
CommandResult = namedtuple('CommandResult', ['token', 'success', 'error', 'log_path'])

from ..models import NodeToken
from ..command_queue import CommandQueue
from ..services.fbc_command_service import FbcCommandService
from ..services.rpc_command_service import RpcCommandService
from ..session_manager import SessionManager



class SequentialCommandProcessor(QObject):
    """
    Processor for sequential execution of FBC/RPC commands with resource management.
    """


    
    # Signals for UI updates
    status_message = pyqtSignal(str, int)  # message, duration
    progress_updated = pyqtSignal(int, int)  # current, total
    processing_finished = pyqtSignal(int, int)  # success_count, total_count
    
    def __init__(self, command_queue: CommandQueue, fbc_service: FbcCommandService,
                 rpc_service: RpcCommandService, session_manager: SessionManager,
                 logging_service, parent=None):
        self._error_messages = []  # Initialize error collection
        super().__init__(parent)
        self.command_queue = command_queue
        self.fbc_service = fbc_service
        self.rpc_service = rpc_service
        self.session_manager = session_manager
        self.logging_service = logging_service
        self.logger = logging.getLogger(__name__)

        # Connect command queue signals
        self.command_queue.command_completed.connect(self._on_command_completed)
        self.command_queue.progress_updated.connect(self._on_progress_updated)

        self._is_processing = False
        self._total_commands = 0
        self._completed_commands = 0
        self._success_count = 0
        self._current_token_index = 0
        self._tokens = []
        self._node_name = ''
        self._telnet_client = None
        self._error_messages = []  # Reset error collection for each run


    def process_fbc_commands(self, node_name: str, tokens: List[NodeToken], 
                           telnet_client=None) -> None:
        """
        Process FBC commands sequentially with resource management.

        Args:
            node_name: Name of the node containing the tokens
            tokens: List of FBC tokens to process
            telnet_client: Optional telnet client to reuse
        """
        if self._is_processing:
            self.logger.warning("SequentialCommandProcessor: Already processing commands")
            self.status_message.emit("Already processing commands", 3000)
            return
            
        self._is_processing = True
        self._total_commands = len(tokens)
        self._completed_commands = 0
        self._success_count = 0
        self._current_token_index = 0
        self._tokens = list(tokens)  # Create a copy to avoid external modifications
        self._node_name = node_name
        self._telnet_client = telnet_client
            
        if not tokens:
            self.logger.info("SequentialCommandProcessor: No FBC tokens to process")
            self._finish_processing()
            return
            
        self.status_message.emit(f"Processing {len(tokens)} FBC commands...", 0)
        self.logger.info(f"SequentialCommandProcessor: Starting processing of {len(tokens)} FBC commands for node {node_name}")

        # Start processing the first token
        self._process_next_token()


    def process_rpc_commands(self, node_name: str, tokens: List[NodeToken], 
                           action: str = "print", telnet_client=None) -> None:
        """
        Process RPC commands sequentially with resource management.

        Args:
            node_name: Name of the node containing the tokens
            tokens: List of RPC tokens to process
            action: Action to perform (print, clear)
            telnet_client: Optional telnet client to reuse
        """
        if self._is_processing:
            self.logger.warning("SequentialCommandProcessor: Already processing commands")
            self.status_message.emit("Already processing commands", 3000)
            return
            
        self._is_processing = True
        self._total_commands = len(tokens)
        self._completed_commands = 0
        self._success_count = 0
        self._current_token_index = 0
        self._tokens = list(tokens)  # Create a copy to avoid external modifications
        self._node_name = node_name
        self._telnet_client = telnet_client
        self._action = action
            
        if not tokens:
            self.logger.info("SequentialCommandProcessor: No RPC tokens to process")
            self._finish_processing()
            return
            
        self.status_message.emit(f"Processing {len(tokens)} RPC commands...", 0)
        self.logger.info(f"SequentialCommandProcessor: Starting processing of {len(tokens)} RPC commands for node {node_name}")

        # Start processing the first token
        self._process_next_token()


    def process_tokens_sequentially(self, node_name: str, tokens: List[NodeToken], 
                                  action: str = "print") -> None:
        """
        Process multiple tokens sequentially with individual context and error isolation.

        This method simulates how a user would process tokens separately through right-click execution,
        maintaining individual token context while providing batch operation convenience. Each token
        is processed in sequence with its own logging context and error handling, ensuring failures
        with one token don't prevent processing of subsequent tokens.

        Args:
            node_name: Name of the node containing the tokens (e.g., "AP01m")
            tokens: List of NodeToken objects to process, each containing:
                - token_id: Unique identifier for the token
                - token_type: Protocol type ("FBC" or "RPC")
                - node_ip: Associated node IP address (optional)
            action: Action to perform for RPC tokens (default: "print"). 
                   Valid values: "print", "clear", "vnc"

        Behavior:
            1. Processes tokens in the order they appear in the node tree
            2. Creates isolated logging context for each token
            3. Maintains individual error tracking (failures don't halt processing)
            4. Generates token-specific log files with consistent naming patterns
            5. Emits progress updates after each token completion

        Error Handling:
            - Individual token failures are logged but don't terminate batch processing
            - Failed tokens are tracked and reported in the final summary
            - Circuit breaker triggers after 3 consecutive failures (see process_sequential_batch)
            - Detailed error messages include token ID and failure context

        Example:
            >>> processor.process_tokens_sequentially(
            ...     node_name="AP01m",
            ...     tokens=[
            ...         NodeToken(token_id="162", token_type="FBC"),
            ...         NodeToken(token_id="163", token_type="RPC")
            ...     ]
            ... )
            # Processes 162_FBC.log then 163_RPC.log with individual contexts

        See Also:
            - [`token_processing.md`](docs/token_processing.md) for workflow documentation
            - [`ContextMenuService._handle_token_command()`](src/commander/services/context_menu_service.py:1) for UI integration
        """        
        
        if self._is_processing:
            self.logger.warning("SequentialCommandProcessor: Already processing commands")
            self.status_message.emit("Already processing commands", 3000)
            return
            
        self._is_processing = True
        self._total_commands = len(tokens)
        self._completed_commands = 0
        self._success_count = 0
        self._current_token_index = 0
        self._tokens = list(tokens)  # Create a copy to avoid external modifications
        self._node_name = node_name
        self._telnet_client = None
        self._action = action
        self._batch_id = self._generate_batch_id()  # Add batch ID for logging
        
        if not tokens:
            self.logger.info("SequentialCommandProcessor: No tokens to process")
            self._finish_processing()
            return
            
        self.status_message.emit(f"Processing {len(tokens)} tokens sequentially...", 0)
        self.logger.info(f"SequentialCommandProcessor: Starting sequential processing of {len(tokens)} tokens for node {node_name}")

        # Start batch logging
        self.logging_service.start_batch_logging(
            batch_id=self._batch_id,
            node_name=node_name,
            token_count=len(tokens)
        )

        # Start processing the first token (batch logging removed)
        self._process_next_token()


    def process_all_fbc_subgroup_commands(self, tokens: List[NodeToken], commandSpec: dict, 
                                        options: dict = None) -> List[dict]:
        """Process all FBC tokens sequentially with isolated logging"""
        return self._process_batch_tokens(tokens, "FBC", commandSpec, options)


    def process_all_rpc_subgroup_commands(self, tokens: List[NodeToken], commandSpec: dict, 
                                        options: dict = None) -> List[dict]:
        """Process all RPC tokens sequentially with isolated logging"""
        return self._process_batch_tokens(tokens, "RPC", commandSpec, options)


    def _process_batch_tokens(self, tokens: List[NodeToken], protocol: str, 
                            commandSpec: dict, options: dict) -> List[dict]:
        """Internal batch processor with common logic"""
        outcomes = []
        batch_id = self._generate_batch_id()
        for token in tokens:
            token_outcome = {"token": token.token_id, "success": False, "error": None, "log_path": ""}
            try: 
                # Prepare context and open log
                context = self._prepare_token_context(token, protocol, batch_id)
                token_outcome["log_path"] = context["log_path"]
                
                # Execute token command
                success, error = self._execute_token(protocol, context["normalized_token"], 
                                                   commandSpec, options, batch_id)
                token_outcome["success"] = success
                token_outcome["error"] = error
            except Exception as e: 
                token_outcome["error"] = str(e)
                self.logger.error(token_outcome["error"])
            finally:
                # Clean up resources after processing this token
                self._release_telnet_client()
                # Move on to next token
                self._current_token_index += 1
        return outcomes


    def _generate_batch_id(self) -> str:
        """Generate unique batch ID for logging"""
        import uuid
        return str(uuid.uuid4())[:8]


    def _prepare_token_context(self, token: NodeToken, protocol: str, batch_id: str) -> dict:
        """
        Prepare context for token processing with isolated logging.

        Args:
            token: NodeToken object to process
            protocol: Token protocol (FBC/RPC)
            batch_id: Batch operation identifier
            
        Returns:
            Context dictionary containing:
                normalized_token: Formatted token
                log_path: Path to token-specific log file
                node_ip: Validated IP address
                batch_id: Batch operation identifier
        """        
        from ..utils.token_utils import validate_ip_address

        try:
            # Normalize token according to protocol rules
            normalized_token = self._normalize_token(token.token_id, protocol)
            
            # Extract and validate node IP
            node_ip = token.node_ip if hasattr(token, 'node_ip') else None
            if not node_ip or not validate_ip_address(node_ip):
                node_ip = "0.0.0.0"  # Default for invalid IPs
                self.logger.warning(f"Invalid node IP for token {token.token_id}, using default")
            
            # Generate unique log path and open log
            log_path = self.logging_service.open_log_for_token(
                token_id=token.token_id,
                node_name=self._node_name,
                node_ip=node_ip,
                protocol=protocol,
                batch_id=batch_id
            )
            
            # Write standardized header with token metadata
            header = (
                f"Token Processing Header:\n"
                f"  Token ID: {token.token_id}\n"
                f"  Node: {self._node_name}\n"
                f"  Timestamp: {datetime.datetime.now().isoformat()}\n"
                f"  Protocol: {protocol}\n"
                f"  Batch ID: {batch_id}\n"
            )
            self.logging_service.log(header)
            
            return {
                "normalized_token": normalized_token,
                "log_path": log_path,
                "node_ip": node_ip,
                "batch_id": batch_id
            }
            
        except Exception as e:
            error_msg = f"Error preparing context for token {token.token_id}: {str(e)}"
            self.logger.error(error_msg)
            # Return minimal context with error indicator
            return {
                "normalized_token": token.token_id,
                "log_path": "",
                "node_ip": "0.0.0.0",
                "batch_id": batch_id,
                "error": error_msg
            )


    def _normalize_token(self, token: str, protocol: str) -> str:
        """Normalize token according to protocol rules"""
        from ..utils.token_utils import normalize_token
        return normalize_token(token, protocol)


    def _execute_token(self, token: NodeToken, context: dict) -> Tuple[bool, Optional[str]]:
        """
        Execute a token command with proper error handling and resource management.

        This is the centralized entry point for all command execution, ensuring consistent
        behavior across FBC and RPC protocols. The method handles:
        - Protocol-specific command execution
        - Resource management (Telnet client)
        - Error classification and reporting
        - Circuit breaker tracking

        Args:
            token: The token to execute
            context: Context dictionary containing normalized token, log path, etc.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            if token.token_type == "FBC":
                # Execute FBC command with Telnet
                try:
                    self.fbc_service.queue_field_bus_command(
                        self._node_name, 
                        context["normalized_token"],
                        self._telnet_client
                    )
                    return True, None
                except TelnetConnectionError as e:
                    error_msg = f"Telnet connection failed for token {token.token_id}: {str(e)}"
                    self.logger.error(error_msg)
                    return False, error_msg
                except CommandTimeoutError as e:
                    error_msg = f"Command timed out for token {token.token_id}: {str(e)}"
                    self.logger.warning(error_msg)
                    return False, error_msg
                    
            elif token.token_type == "RPC":
                # Execute RPC command
                try:
                    self.rpc_service.queue_rpc_command(
                        self._node_name,
                        context["normalized_token"],
                        context.get("action", "print"),
                        telnet_client=None
                    )
                    return True, None
                except RpcConnectionError as e:
                    error_msg = f"RPC connection failed for token {token.token_id}: {str(e)}"
                    self.logger.error(error_msg)
                    return False, error_msg
                except CommandTimeoutError as e:
                    error_msg = f"Command timed out for token {token.token_id}: {str(e)}"
                    self.logger.warning(error_msg)
                    return False, error_msg
                    
            else:
                error_msg = f"Unknown token type {token.token_type} for token {token.token_id}"
                self.logger.warning(f"SequentialCommandProcessor: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Unexpected error executing token {token.token_id}: {str(e)}"
            self.logger.exception(error_msg)  # Log full traceback
            return False, error_msg


    def _process_next_token(self) -> None:
        """
        Process the next token in the sequence with true sequential execution.

        This method has been restructured to implement true sequential execution:
        1. Only processes one token at a time
        2. Does NOT schedule the next token immediately
        3. Relies entirely on command_completed signal to advance processing
        4. Maintains proper state between tokens

        The key change from the previous implementation is the removal of QTimer-based
        scheduling. Instead, token advancement is now strictly controlled by the
        command completion callback mechanism, ensuring:
        - No race conditions between token processing
        - Proper resource cleanup between commands
        - Accurate progress reporting
        - Reliable circuit breaker functionality
        """
        if not self._is_processing or self._current_token_index >= len(self._tokens):
            self._finish_processing()
            return
            
        token = self._tokens[self._current_token_index]
        self.logger.debug(f"SequentialCommandProcessor: Processing token {self._current_token_index + 1}/{len(self._tokens)}: {token.token_id}")

        try:
            # Prepare token context with logging
            context = self._prepare_token_context(token, token.token_type, self._batch_id)
            if 'error' in context:
                raise Exception(context['error'])
                
            self._current_log_path = context['log_path']
            
            # Execute token using centralized method
            success, error = self._execute_token(token, context)
            
            if not success:
                # Handle execution failure without advancing token index
                self._handle_token_failure(token, error)
                
        except Exception as e:
            # Handle preparation or execution failure
            self._handle_token_failure(token, str(e))


    def _handle_token_failure(self, token: NodeToken, error_msg: str) -> None:
        """
        Handle token processing failure with consistent error reporting.

        This method centralizes error handling to ensure:
        - Consistent logging format
        - Proper resource cleanup
        - Accurate error tracking
        - Circuit breaker evaluation

        Args:
            token: The token that failed
            error_msg: Error message describing the failure
        """
        self.logger.error(f"SequentialCommandProcessor: {error_msg}")
        self.status_message.emit(error_msg, 5000)
        log_entry = (
            f"Token Processing Result:\n"
            f"  Token ID: {token.token_id}\n"
            f"  Token Type: {token.token_type}\n"
            f"  Status: Failure\n"
            f"  Error: {error_msg}\n"
        )
        self.logging_service.log(log_entry)
        self._error_messages.append(error_msg)
        
        # Release resources
        self._release_telnet_client()
        
        # Advance to next token (handled by circuit breaker check)
        self._current_token_index += 1
        self._check_circuit_breaker() 


    def _check_circuit_breaker(self) -> None:
        """
        Check if circuit breaker should be triggered and advance token processing.

        The circuit breaker prevents continued processing after multiple failures:
        - Tracks consecutive failures
        - Stops processing after 3 consecutive failures
        - Provides clear error reporting
        - Ensures proper cleanup

        This implementation ensures the circuit breaker works correctly with the
        new sequential execution model by:
        - Evaluating after each token failure
        - Only stopping when threshold is reached
        - Allowing successful tokens to reset the counter
        """
        # Check if we've reached the end
        if self._current_token_index >= len(self._tokens):
            self._finish_processing()
            return
            
        # Check circuit breaker condition (3 consecutive failures)
        if len(self._error_messages) >= 3:
            self.logger.error("Circuit breaker triggered after 3 consecutive failures")
            self._finish_processing()
            return
            
        # Process next token
        self._process_next_token()


    def _on_command_completed(self, command: str, result: str, success: bool, token: NodeToken) -> None:
        """
        Handle completion of a command and advance to next token.

        This is the critical callback that enables true sequential execution:
        - Only advances to next token when command completes
        - Maintains proper state between tokens
        - Ensures resource cleanup between commands
        - Provides accurate progress reporting

        The key changes from previous implementation:
        - Removed QTimer-based scheduling
        - Directly advances token index
        - Uses circuit breaker check for flow control
        - Maintains consistent error tracking
        """
        self._completed_commands += 1
        if success:
            self._success_count += 1
            # Reset error count on success
            if self._error_messages:
                self._error_messages = []
        else:
            # Track failure for circuit breaker
            self._error_messages.append(f"Command failed: {result}")
            
        self.logger.debug(f"SequentialCommandProcessor: Command completed - Success: {success}, Token: {token.token_id}")
        
        # Add token-specific logging
        log_entry = (
            f"Token Processing Result:\n"
            f"  Token ID: {token.token_id}\n"
            f"  Token Type: {token.token_type}\n"
            f"  Command Executed: {command}\n"
            f"  Status: {'Success' if success else 'Failure'}\n"
        )
        if not success:
            log_entry += f"  Error: {result}\n"
        self.logging_service.log(log_entry)
        
        # Close token log
        self.logging_service.close_log_for_token(
            token_id=token.token_id,
            protocol=token.token_type,
            batch_id=self._batch_id
        )
        
        # Release telnet client after each command
        self._release_telnet_client()

        # Advance to next token through circuit breaker check
        self._current_token_index += 1
        self._check_circuit_breaker()


    def _on_progress_updated(self, current: int, total: int) -> None:
        """
        Handle progress update from command queue.

        Args:
            current: Number of completed commands
            total: Total number of commands
        """


    def _finish_processing(self) -> None:
        """Finish processing and emit completion signals."""
        self._is_processing = False
        
        # Report aggregated errors if any
        if self._error_messages:
            error_summary = f"Completed with {len(self._error_messages)} errors. See logs for details."
            self.logger.error(f"SequentialCommandProcessor: {error_summary}")
            self.status_message.emit(error_summary, 5000)
        else:
            self.logger.info(f"SequentialCommandProcessor: Finished processing - {self._success_count}/{self._total_commands} commands successful")
            self.status_message.emit(f"Finished processing {self._success_count}/{self._total_commands} commands", 3000)
            
        self.processing_finished.emit(self._success_count, self._total_commands)
        
        # End batch logging
        self.logging_service.end_batch_logging(
            batch_id=self._batch_id,
            node_name=self._node_name,
            success_count=self._success_count,
            total_count=self._total_commands
        )
        
        # Clean up resources at the right time
        self._process_updatesCompleted = False
        self._current_token = None


    def _perform_periodic_cleanup(self) -> None:
        """Perform periodic cleanup to optimize memory usage."""
        # Process Qt events to prevent UI freezing
        from PyQt6.QtCore import QCoreApplication
        QCoreApplication.processEvents()


    def stop_processing(self) -> None:
        """Stop processing commands."""
        if self._is_processing:
            self.logger.info("SequentialCommandProcessor: Stopping command processing")
            self._is_processing = False
            self.command_queue.clear_queue()
            self._finish_processing()


    def process_sequential_batch(self, tokens: List[NodeToken], 
                                protocol: str, 
                                commandSpec: dict) -> List[CommandResult]:
        """
        Process tokens sequentially with isolated execution and logging
        
        Args:
            tokens: List of validated NodeToken objects
            protocol: 'FBC' or 'RPC' protocol identifier
            command_spec: Dictionary containing command parameters
        
        Returns:
            List of CommandResult objects with individual token outcomes
        """
        results = []
        consecutive_failures = 0
        batch_id = self._generate_batch_id()
        for i, token in enumerate(tokens):
            # Initialize log file for this token
            log_path = self.logging_service.open_log_for_token(
                token.token_id, 
                protocol, 
                batch_id
            )
            
            try:
                # Normalize token according to protocol rules
                normalized_token = self._normalize_token(token.token_id, protocol)
                
                # Execute the token command
                success, error = self._execute_token(
                    protocol,
                    normalized_token,
                    commandSpec,
                    None,  # options not used in this flow
                    batch_id
                )
                
                # Handle circuit breaker for failures
                if not success:
                    consecutive_failures += 1
                    if consecutive_failures >= 3:
                        self.logger.error("Circuit breaker triggered after 3 consecutive failures")
                        # Create result for current token before breaking
                        result = CommandResult(
                            token=token.token_id,
                            success=success,
                            error=error,
                            log_path=log_path
                        )
                        results.append(result)
                        break
                else:
                    consecutive_failures = 0
                    
                # Create result object
                result = CommandResult(
                    token=token.token_id,
                    success=success,
                    error=error,
                    log_path=log_path
                )
                results.append(result)
                
                # Emit progress signal
                self.progress_updated.emit(i + 1, len(tokens))
                
            except Exception as e:
                # Handle token-specific error without aborting entire batch
                error_msg = f"Error processing token {token.token_id}: {str(e)}"
                self.logger.error(error_msg)
                results.append(CommandResult(
                    token=token.token_id,
                    success=False,
                    error=error_msg,
                    log_path=log_path
                ))
                consecutive_failures += 1
                
                if consecutive_failures >= 3:
                    self.logger.error("Circuit breaker triggered after 3 consecutive failures")
                    break
                
            finally:
                # Close log for this token
                self.logging_service.close_log_for_token(token.token_id, protocol, batch_id)
                
                # Clean up resources
                self._release_telnet_client()
                
                # Move circuit breaker check here to break immediately after 3 failures
                if consecutive_failures >= 3:
                    self.logger.error("Circuit breaker triggered after 3 consecutive failures")
                    break
                    
                # Perform periodic cleanup
                if (i + 1) % 10 == 0:
                    self._perform_periodic_cleanup()
                    
            # Check circuit breaker again
            if consecutive_failures >= 3:
                self.logger.error("Circuit breaker triggered after 3 consecutive failures")
                break
                
        return results