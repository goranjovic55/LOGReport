"""
Telnet Command Resolver
Converts user-friendly commands to executable Telnet commands
"""
import re
from typing import Dict

class CommandResolver:
    def __init__(self):
        self.command_map = {
            "ps": self.resolve_ps,
            "fis": self.resolve_fis,
            "rc": self.resolve_rc,
            "%": self.resolve_context_token
        }
        
        self.token_replacement = {
            "ps": "show all",
            "fis": "print_fieldbus {token}0000",
            "rc": "print_fieldbus_rupi_counters {token}0000"
        }
    
    def resolve(self, command: str, context_token: str = "") -> str:
        """Resolves a command using context token if needed"""
        # Clean and normalize input
        command = command.strip().lower()
        
        # Handle empty command
        if not command:
            return ""
            
        # Try exact match first
        if handler := self.command_map.get(command):
            return handler(context_token)
            
        # Process if command ends with reserved keyword
        pattern_match = re.match(r"^(\w+)\s+(\w+)$", command)
        if pattern_match:
            cmd_keyword = pattern_match.group(2)
            if handler := self.command_map.get(cmd_keyword):
                token = pattern_match.group(1)
                return handler(token)
        
        # Try to resolve with context token substitution
        if context_token and command in self.token_replacement:
            return self.token_replacement[command].format(token=context_token)
            
        # Return command as-is if no matches
        return command
        
    # Command handlers
    def resolve_ps(self, token: str = "") -> str:
        return "show all"
        
    def resolve_fis(self, token: str) -> str:
        return f"print_fieldbus {token}0000"
        
    def resolve_rc(self, token: str) -> str:
        return f"print_fieldbus_rupi_counters {token}0000"
        
    def resolve_context_token(self, token: str = "") -> str:
        if not token:
            return ""
        return f"print_fieldbus {token}0000"

class CommandHistory:
    """Manages command history for Telnet sessions"""
    def __init__(self, max_history=100):
        self.history = []
        self.max_history = max_history
        self.current_index = -1
        
    def add(self, command: str):
        """Adds a command to history"""
        if not command:
            return
            
        # Avoid duplicates in immediate sequence
        if not self.history or self.history[-1] != command:
            self.history.append(command)
            
        # Maintain max size
        if len(self.history) > self.max_history:
            self.history.pop(0)
            
        self.reset_position()
        
    def reset_position(self):
        """Resets history navigation position"""
        self.current_index = len(self.history)
        
    def get_previous(self) -> str:
        """Gets previous command in history"""
        if not self.history:
            return ""
            
        if self.current_index > 0:
            self.current_index -= 1
            
        return self.history[self.current_index] if self.current_index >= 0 else ""
        
    def get_next(self) -> str:
        """Gets next command in history"""
        if not self.history or self.current_index >= len(self.history) - 1:
            return ""
            
        self.current_index += 1
        return self.history[self.current_index]
        
    def get_by_index(self, index: int) -> str:
        """Gets command by history index"""
        if 0 <= index < len(self.history):
            return self.history[index]
        return ""
