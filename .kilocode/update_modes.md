# 🧠 Update Modes Workflow

This workflow refines all existing Kilo Code modes by combining local exports, project memory, global memory, and external community insights.

## 🔧 Tool Access

- MCP servers available:
  - `project_memory` (project-local context)
  - `global_memory` (cross-project memory)
  - `sequential_thinking` (structured planning)
  - `firecrawl_mcp` (external knowledge)
  - `context7` (official docs)

## 🔁 Steps

### 1. Load Current Mode Configurations
- Load all mode export files in `.kilocode/`:
  - `analyze-export.yaml`
  - `debug-export.yaml`
  - `architect-export.yaml`
  - `document-export.yaml`
  - `code-export.yaml`
  - `orchestrator-export.yaml`

### 2. Gather External Best Practices
- Use `firecrawl_mcp(...)` to crawl:
  - Official Kilo Code documentation at [kilocode.ai/docs](https://kilocode.ai/docs) for mode guidance
  - Relevant Reddit threads and GitHub discussions for how users leverage Architect, Orchestrator, Debug modes, etc.

### 3. Read Existing Memory Context
- Use `project_memory(action="read")` and `global_memory(action="read")` to fetch:
  - Custom mode overrides
  - Memory-driven workflow adaptations
  - Structural conventions or repeated patterns stored in memory

### 4. Plan Enhancements
- Use `sequential_thinking(...)` with all gathered context to:
  - Detect gaps or inconsistencies in existing mode definitions
  - Suggest enhancements such as context loading steps, tool eligibility, user identity scoping
  - Align modes to documented best practices and community patterns

### 5. Apply Updates
- Implement base mode template with recurrent instruction pattern:
  - Extract 'Remember using global_memory and project_memory if we have solved similar problem' into base template
  - Apply to Code, Debug, and Optimize modes
- Apply inheritance pattern for consistent configuration
- Enforce strict mode boundaries to prevent violations
- Standardize configuration format across all mode files
- Implement transition validation middleware
- Add missing icons to Document and Optimize modes
- Simplify Orchestrator mode configuration
- Use `edit_file(...)` to write improved mode spec back to `.kilocode/`

### 6. Persist Final Memory-Driven Overrides
- If enhancements are deemed reusable:
  - Promote shared patterns to `global_memory` using `global_memory(action="write", data={…})`
- Always update `project_memory` with final local mode adjustments

### 7. Finalize & Backup
- Summarize all mode refinements and reasoning:
  ```ts
  attempt_completion(result="Completed mode optimization: mode updates applied, memory synced, best practices integrated.")
  ```

## 🧩 Enhancement Details

### Base Mode Template
Create a base mode template that extracts the recurrent instruction pattern found in multiple modes:
```yaml
baseModeTemplate:
  customInstructions: >-
    • Remember using global_memory and project_memory if we have solved similar problem, and load whole knowledge from it
```

### Inheritance Pattern
Apply the base template to Code, Debug, and Optimize modes through inheritance:
```yaml
customModes:
  - slug: code
    name: Code
    inherits: baseModeTemplate
    # Additional mode-specific instructions
```

### Strict Boundary Enforcement
Implement explicit role restrictions to prevent mode boundary violations:
```yaml
customModes:
  - slug: architect
    roleRestrictions:
      - Cannot generate implementation code
      - Must only produce architectural designs
```

### Standardized Configuration
Apply consistent YAML structure across all mode files:
```yaml
customModes:
  - slug: [mode-slug]
    name: [Mode Name]
    iconName: [icon-codicon]
    roleDefinition: [Concise role description]
    whenToUse: [Clear usage guidance]
    description: [Brief description]
    groups: [read, edit, browser, command, mcp]
    customInstructions: [Mode-specific instructions]
    source: project
```

### Transition Validation Middleware
Implement validation steps to ensure mode transitions follow the MultiModeWorkflow pattern:
```yaml
transitionValidation:
  - Plan with Architect mode first
  - Implement with Code mode
  - Debug and troubleshoot with Debug mode
  - Use Orchestrator mode for complex multi-step projects
```

### Memory Integration
Update both project_memory and global_memory with mode configuration changes:
- Use `project_memory` for local insights specific to this project
- Use `global_memory` for generalized patterns applicable across projects

MCP servers to be used:
- `project_memory`
- `global_memory`
- `sequential_thinking`
- `firecrawl_mcp`
- `context7`

Memory loading:
- Instruct to load project-specific context using `project_memory` tools
- Load cross-project knowledge using `global_memory` tools

Reasoning & planning:
- Use tools from the `sequential_thinking` MCP server

Community research:
- Use tools from `firecrawl_mcp` MCP server for any additional research needed for documentation.
- Use tools from `context7` MCP server for any official documentation references.

Memory updates before completion:
- Persist task results using:
  - `project_memory` MCP server tools for local insights (e.g., the content of the `update_modes.md` file)
  - `global_memory` MCP server tools for generalized patterns (e.g., best practices for workflow documentation)

Completion:
- Must end with `attempt_completion(result="...")`