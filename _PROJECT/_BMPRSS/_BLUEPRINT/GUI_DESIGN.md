# GUI Design Blueprint (v2.0)

## Main Window Structure
```plaintext
┌──────────────────────────────────────────────┐
│                  Menu Bar                    │
├──────────────────────────────────────────────┤
│   Settings:                                  │
│     - Manage Nodes                           │
├──────────────────────────────────────────────┤
│  Output Settings Group                       │
│  ┌────────────────────────────────────────┐  │
│  │ [Output Format: PDF ▾]                 │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  Log Filtering Group                         │
│  ┌────────────────────────────────────────┐  │
│  │ [Show All ▾] [Lines: 50 ]              │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  Buttons: [Select Log Folder]                │
│          [Generate Report]                   │
│          [Generate]                          │
│                                              │
│  Progress Bar                                │
└──────────────────────────────────────────────┘
```

## Node Manager Dialog
```plaintext
┌──────────────────────────── Node Configuration ───────────────────────────┐
│ ┌─────────────────────┐                      ┌──────────────────────────┐ │
│ │ Nodes:              │                      │ Node Configuration:      │ │
│ │  - Node1 (t1,t2)    │                      │  Name: [Node1         ]  │ │
│ │  - Node2 (t3,t4)    │                      │  Tokens: [t1, t2      ]  │ │
│ │                     │                      │                          │ │
│ │ [+ Add Node]        │   <Selection Sync>   │  Log Types:              │ │
│ │ [- Remove Selected] │                      │   ( ) FBC: Fieldbus Logs │ │
│ └─────────────────────┘                      │   ( ) RPC: RPC Logs     │ │
│                                              │   ( ) LOG: Node Logs     │ │
│                                              │   ( ) LIS: Listener Logs │ │
│                                              │                          │ │
│                                              │  Example Files:          │ │
│                                              │   • Node1_t1_fbc1.txt    │ │
│                                              │   • Node1_t2_fbc2.txt    │ │
│                                              │                          │ │
│                                              │  [Save to JSON]          │ │
│                                              │  [Create Files+Folders]  │ │
│                                              └──────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────┘
```

## New Features
1. **Node Manager Integration**
   - Access via Settings → Manage Nodes
   - Complete CRUD operations for nodes
   - Real-time example generation
   - Two-step workflow:
     - Save configuration
     - Create files/folders
   - Support for all log types

2. **File Creation Flow**
   - Direct integration with Log Creator
   - Automatic directory structure generation
   - Progress reporting
   - Error handling feedback

## Best Practices
- **UI/UX Principles**:
  - Follow PyQt dark theme guidelines
  - Group related controls
  - Provide immediate visual feedback
  - Disable actions during processing
- **Thread Management**:
  - Use QThread for file operations
  - Prevent UI freezing
- **Result Display**:
  - Show file creation status
  - Provide creation summary
- **Responsive Design**:
  - Layout proportions (45/55 split)
  - Adaptive widget visibility

## Error Prevention
1. Form validation before saving
2. Type/token dependency checking
3. File existence checks
4. Error messages with resolution steps

## Future Enhancements
1. Drag-and-drop file reorganization
2. Batch editing capabilities
3. Template customization options
4. Directory structure preview
