# Context Menu Architecture

This document details the architecture and implementation of the context menu system in the LOGReport application, with a focus on the filtering mechanism that controls command visibility.

## Overview

The context menu system provides users with a right-click interface to execute commands on nodes and log files. The system has been enhanced with a filtering mechanism that dynamically controls which commands are visible based on node type, section type, and other contextual factors.

## Core Components

### CommanderWindow
The main GUI interface that manages the display and interaction with context menus. It handles the right-click events and delegates to the appropriate service classes.

- **Location**: `src/commander/commander_window.py`
- **Responsibilities**:
  - Managing the node tree display
  - Handling right-click events on nodes
  - Coordinating with service classes to build context menus
  - Displaying the final context menu to the user

### ContextMenuFilterService
The central service that determines command visibility through configuration-driven rules.

- **Location**: `src/commander/services/context_menu_filter.py`
- **Responsibilities**:
  - Loading filtering rules from configuration
  - Evaluating rules against current context (node name, section type, command type)
  - Determining whether a command should be shown or hidden
  - Providing a flexible, maintainable way to control menu visibility

### Configuration File
The filtering rules are defined in `config/menu_filter_rules.json`, allowing for easy modification without code changes.

```json
{
  "rules": [
    {
      "description": "Hide AP01m FBC commands",
      "node_name": "AP01m",
      "section_type": "FBC",
      "action": "hide",
      "command_type": "all"
    }
  ],
  "metadata": {
    "version": "1.0",
    "description": "Context menu filtering rules"
  }
}
```

## Filtering Mechanism

The filtering system works by evaluating a set of rules in sequence, with the first matching rule determining the outcome. Rules can match on:

- **Node Name**: Exact match, wildcard patterns (*, ?), or regular expressions
- **Section Type**: FBC, RPC, or other section types
- **Command Type**: Specific command types or "all" for any command

The evaluation follows these steps:
1. When a context menu is requested, the system gathers the current context (node name, section type, etc.)
2. Each rule is evaluated in order until a match is found
3. The action ("show" or "hide") from the first matching rule is applied
4. If no rules match, the command is shown by default

## Implementation Details

The `ContextMenuFilterService` class implements the filtering logic with the following key methods:

- `should_show_command(node_name, section_type, command_type)`: Main entry point that determines visibility
- `_rule_matches(rule, node_name, section_type, command_type)`: Checks if a rule applies to the current context
- `_matches_pattern(value, pattern)`: Handles pattern matching with support for exact, wildcard, and regex patterns

## Usage Example

To hide a specific command type for a node pattern:

```json
{
  "description": "Hide print commands for maintenance nodes",
  "node_name": "MNT*",
  "section_type": "FBC",
  "action": "hide",
  "command_type": "print"
}
```

## Benefits

This architecture provides several advantages:

1. **Flexibility**: Rules can be modified without code changes
2. **Maintainability**: Centralized control of menu visibility
3. **Scalability**: Easy to add new rules for different node types
4. **Consistency**: Uniform approach to command filtering across the application
5. **Configurability**: Environment-specific rules can be deployed through configuration

## Future Enhancements

Potential improvements to the system include:
- GUI for managing filter rules
- Rule validation and testing tools
- Performance optimization for large rule sets
- Integration with user roles/permissions
- Logging of rule evaluations for debugging