# File Processing Blueprint (v2.0)

## Node Configuration Management
- **Configuration Format**: JSON format
- **Path**: `/src/nodes.json`
- **Structure**:
  ```json
  [
    {
      "name": "node_name",
      "tokens": ["token1", "token2"],
      "types": ["FBC", "RPC", "LOG", "LIS"]
    }
  ]
  ```
- **Automatic Generation**:
  - Configuration created programmatically through Node Manager UI
  - Simultaneous generation of JSON and compatible text format

## File Creation Process
1. **Trigger**: "Create Files and Folders" button in Node Manager
2. **File Generation Workflow**:
   ```mermaid
   graph TD
   A[Node Manager] -->|Triggers| B[Save JSON config]
   B --> C[Parse filtered nodes]
   C -->|FBC| D[Create token files]
   C -->|RPC| E[Create token files]
   C -->|LOG| F[Create AL/AP logs]
   C -->|LIS| G[Create IRB/ORB files]
   ```
3. **Directory Structure**:
   ```
   _DIA/
   ├── FBC/        # AP01m_162.txt, AP01m_163.txt
   ├── RPC/        # AP01m_162_rpc.txt, AP01m_163_rpc.txt
   ├── LOG/        # AP01r_log_.txt, AL02_log.txt
   └── LIS/        # AL03/exe1_5irb_5orb.txt, AL03/exe2_5irb_5orb.txt
   ```
4. **File Templates**:
   ```text
   # $FILENAME
   # Log created: $DATETIME
   
   Add log entries below this line
   ```

## Error Handling
- **Validation Checks**:
  - Token verification for FBC/RPC log types
  - Node name prefix validation (AL/AP)
  - JSON schema compliance
- **Exception Handling**:
  ```python
  try:
      # File creation logic
  except PermissionError as e:
      logger.error(f"Access denied: {e}")
      raise FileCreationError("Ensure write permissions")
  except OSError as e:
      logger.error(f"File system error: {e}")
      raise FileCreationError("Disk may be full")
  ```

## Best Practices
1. **Idempotent Operations**: File creation skips existing files
2. **Batch Processing**: Process nodes in type-specific batches
3. **Progress Feedback**: Visual indicators during long operations
4. **Atomic Operations**: Complete file system operations before reporting completion
5. **Path Abstraction**: Platform-agnostic path handling
