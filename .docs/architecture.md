# LOGReport Architecture Documentation

## Core Components

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
#### FbcCommandService
- Handles FBC protocol commands
- Implements specific FBC command logic
- Manages FBC session state

#### RpcCommandService  
- Handles RPC protocol commands
- Implements RPC command execution
- Manages RPC session state

### Command Queue
- Centralized command processing
- Ensures thread-safe command execution
- Manages command prioritization

### Log Writer
- Handles all log file operations
- Features:
  - Size-based rotation (10MB max, 5 backups)
  - Consistent log formatting
  - Thread-safe operations

## Architectural Principles

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