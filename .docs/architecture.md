# LOGReport Architecture Documentation

## Core Components

### NetworkSession (Base Class)
- Abstract base class for all session types
- Defines common interface for command execution and connection management
- Enforces standardized error handling across all protocols
- Provides connection health monitoring and retry mechanisms

### NodeToken
- Represents tokens and their attributes
- Handles token validation and processing
- Key properties: token_id, node_name, token_type (FBC/RPC)

### Node
- Manages node configurations and connections
- Contains node metadata and status
- Handles communication with physical nodes

### CommanderWindow
- Main UI orchestrator
- Responsibilities:
  - Command execution flow
  - User interaction handling
  - Log display and management
  - Status updates

### Command Services
- Consolidated service layer for all command processing
- Unified interface for FBC and RPC commands
- Standardized error handling and response processing
- Centralized command queuing and execution

#### FbcCommandService
- Implements FBC-specific command logic
- Inherits from base CommandService
- Manages FBC session state through NetworkSession

#### RpcCommandService
- Implements RPC-specific command execution
- Inherits from base CommandService
- Manages RPC session state through NetworkSession

### Command Queue
- Centralized command processing
- Ensures thread-safe command execution
- Manages command prioritization

### TelnetOperations
- Consolidated Telnet functionality across the application
- Implements robust connection handling with retry logic
- Standardized prompt pattern matching and response parsing
- Centralized error handling for Telnet operations
- Manages connection timeouts and session recovery

### Log Writer
- Handles all log file operations
- Features:
  - Size-based rotation (10MB max, 5 backups)
  - Consistent log formatting
  - Thread-safe operations

## Architectural Principles

### Hierarchical Service Taxonomy
- Services organized in a hierarchical structure:
  - Base CommandService for common functionality
  - Protocol-specific services (FbcCommandService, RpcCommandService) for specialized logic
  - NetworkSession as the foundation for all network operations
- Clear inheritance and composition relationships
- Reduced code duplication through shared base classes

### Modular Design
- Clear separation between:
  - UI layer (CommanderWindow)
  - Business logic (Command Services)
  - Data access (Log Writer)
- Minimal cross-component dependencies

### Interface Contracts
- Well-defined interfaces between components
- Explicit service contracts for command execution
- Standardized error handling

### Thread Safety
- Centralized command queue for thread management
- Synchronized access to shared resources
- Atomic operations for critical sections

## Data Flow

1. User initiates command via UI
2. CommanderWindow validates and formats request
3. Command added to Command Queue
4. Appropriate Command Service processes request
5. Results logged via Log Writer
6. Status updates propagated back to UI

## Error Handling
- Centralized error handling in CommanderWindow
- Service-specific error recovery
- Comprehensive logging of failures