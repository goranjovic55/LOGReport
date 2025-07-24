"""Service for managing context menu filtering rules."""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Pattern, Union
import re

class ContextMenuFilterService:
    """Service for managing context menu filtering rules based on configuration."""
    
    def __init__(self, config_path: str = "config/menu_filter_rules.json"):
        """
        Initialize the filter service with configuration file.
        
        Args:
            config_path: Path to JSON configuration file containing filtering rules
        """
        self.config_path = Path(config_path)
        self.rules = []
        self._load_rules()
    
    def _load_rules(self) -> None:
        """Load filtering rules from configuration file."""
        try:
            if not self.config_path.exists():
                logging.warning(f"Filter configuration file not found: {self.config_path}")
                # Create default configuration
                self._create_default_config()
                return
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            self.rules = config.get('rules', [])
            logging.info(f"Loaded {len(self.rules)} context menu filtering rules from {self.config_path}")
            
        except Exception as e:
            logging.error(f"Failed to load menu filter rules: {e}")
            self.rules = []
    
    def _create_default_config(self) -> None:
        """Create a default configuration file with common filtering rules."""
        default_config = {
            "rules": [
                {
                    "description": "Hide AP01m FBC token commands",
                    "node_name": "AP01m",
                    "section_type": "FBC",
                    "action": "allow",
                    "command_type": "all",
                    "command_category": "token"
                },
                {
                    "description": "Show FBC/RPC subgroup menus",
                    "section_type": ["FBC", "RPC"],
                    "action": "show",
                    "command_type": "all",
                    "command_category": "subgroup"
                }
            ],
            "metadata": {
                "version": "1.0",
                "description": "Context menu filtering rules"
            }
        }
        
        try:
            # Create directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
                
            logging.info(f"Created default filter configuration at {self.config_path}")
            
        except Exception as e:
            logging.error(f"Failed to create default filter configuration: {e}")
    
    def should_show_command(self,
                          node_name: str,
                          section_type: str,
                          command_type: str = "all",
                          command_category: str = "all") -> bool:
        """
        Determine if a command should be shown in the context menu.
        
        Args:
            node_name: Name of the node
            section_type: Type of section (FBC, RPC, etc.)
            command_type: Type of command
            command_category: Category of command (token, subgroup, all)
            
        Returns:
            True if command should be shown, False otherwise
        """
        # Default to showing commands
        show = True
        
        for rule in self.rules:
            try:
                # Check if rule applies to this context
                if self._rule_matches(rule, node_name, section_type, command_type, command_category):
                    action = rule.get('action', 'show').lower()
                    if action == 'hide':
                        show = False
                    elif action == 'show':
                        show = True
                    break  # First matching rule takes precedence
                    
            except Exception as e:
                logging.error(f"Error evaluating filter rule: {e}")
                continue
                
        return show

    def is_visible(self, section_type: str, node_name: str) -> bool:
        """
        Determine if a menu section should be visible.
        
        Args:
            section_type: Type of section (FBC, RPC, etc.)
            node_name: Name of the node
            
        Returns:
            True if section should be visible, False otherwise
        """
        return self.should_show_command(
            node_name=node_name,
            section_type=section_type,
            command_type="all",
            command_category="all"
        )
    
    def _rule_matches(self,
                      rule: Dict,
                      node_name: str,
                      section_type: str,
                      command_type: str,
                      command_category: str = "all") -> bool:
        """
        Check if a rule matches the current context.
        
        Args:
            rule: Filter rule to evaluate
            node_name: Current node name
            section_type: Current section type
            command_type: Current command type
            
        Returns:
            True if rule matches, False otherwise
        """
        # Check node name (exact match or pattern)
        node_match = self._matches_pattern(node_name, rule.get('node_name'))
        if not node_match:
            return False
            
        # Check section type (exact match or pattern)
        section_match = self._matches_pattern(section_type, rule.get('section_type'))
        if not section_match:
            return False
            
        # Check command type (exact match or pattern)
        cmd_match = self._matches_pattern(command_type, rule.get('command_type', 'all'))
        if not cmd_match:
            return False
            
            
        # Check command category (exact match or pattern)
        category_match = self._matches_pattern(command_category, rule.get('command_category', 'all'))
        if not category_match:
            return False
            
        return True
    
    def _matches_pattern(self, value: str, pattern: Optional[Union[str, List[str]]]) -> bool:
        """
        Check if a value matches a pattern (exact, wildcard, or regex).
        
        Args:
            value: Value to check
            pattern: Pattern to match against (string, list of strings, or None)
            
        Returns:
            True if value matches pattern, False otherwise
        """
        if pattern is None:
            return True
            
        if isinstance(pattern, list):
            return any(self._matches_pattern(value, p) for p in pattern)
            
        if isinstance(pattern, str):
            # Exact match
            if pattern == value:
                return True
                
            # Wildcard match (* and ?)
            if '*' in pattern or '?' in pattern:
                regex = pattern.replace('.', '\\.').replace('*', '.*').replace('?', '.')
                return bool(re.match(f"^{regex}$", value))
                
            # Regex match (surrounded by /)
            if pattern.startswith('/') and pattern.endswith('/'):
                try:
                    regex = pattern[1:-1]
                    return bool(re.match(regex, value))
                except re.error:
                    logging.warning(f"Invalid regex pattern: {pattern}")
                    return False
                    
        return False