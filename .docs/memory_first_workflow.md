# Dual Memory Consolidation Workflow

This document outlines the standardized process for managing and consolidating knowledge within both project-specific and global memory systems. This workflow ensures that insights are properly captured, validated, and shared across contexts.

## Overview

The Dual Memory Consolidation Workflow is a structured approach to knowledge management that leverages both local project memory and global cross-project memory. This system enables teams to maintain project-specific details while promoting reusable patterns and best practices across the organization.

## Workflow Steps

### 1. Context Recall
Begin every task by loading relevant memory contexts:
- Use `project_memory` tools to load project-local knowledge
- Use `global_memory` tools to load cross-project insights
- Scope all operations under the current mode's user identity (e.g., `document_user` for Document mode)

### 2. Knowledge Tracking
During task execution, record new insights:
- Document structural inferences, behaviors, and naming decisions
- Use `project_memory` for project-specific knowledge
- Use `global_memory` for reusable abstractions and cross-project patterns

### 3. Dependency Resolution
Trace upstream/downstream implications:
- Use `code-graph-mcp` server tools to generate formal code dependency and call graphs
- Respect modular boundaries and interface contracts
- Validate architectural assumptions against existing patterns

### 4. Sequential Reasoning
Plan complex tasks using structured thinking:
- Use `sequential_thinking` MCP server to break down steps
- Forecast risks and identify potential failure points
- Validate assumptions before implementation

### 5. External Validation
Leverage community knowledge:
- Use `firecrawl_mcp` to explore community-backed solutions
- Search GitHub, Reddit, and technical forums for similar implementations
- Validate proposed solutions against industry norms

### 6. Official Sources
Access authoritative documentation:
- Use `context7` MCP server to retrieve accurate syntax and API definitions
- Verify implementation details against official specifications
- Document sources for future reference

### 7. Final Consolidation
At task completion:
- Update `project_memory` with task-specific outcomes
- Persist generalized patterns to `global_memory`
- Ensure all updates reflect final outcomes and are scoped under the mode's user identity

## Best Practices

- **Load memory before planning**: Always begin with context recall
- **Plan before executing**: Use sequential reasoning for complex tasks
- **Validate before updating**: Ensure accuracy before persisting knowledge
- **Distinguish contexts**: Keep project-specific and reusable knowledge separate
- **Persist for continuity**: Ensure knowledge is available for future tasks

## MCP Server Directory

| MCP Server Name | Purpose |
|----------------|---------|
| `project_memory` | Project-local memory graph (task-specific updates) |
| `global_memory` | Persistent cross-project memory (reusable insights) |
| `sequential_thinking` | Stepwise planning server |
| `firecrawl_mcp` | Community reference and error resolution server |
| `context7` | Official documentation, language, and API standard references |
| `code-graph-mcp` | Code graph analysis: indexes codebase, lists entities and relationships, outputs full JSON dependency/call graph |

## Example Implementation

```python
# Example of memory-first workflow in code
def execute_task():
    # 1. Load contexts
    project_context = load_project_memory()
    global_context = load_global_memory()
    
    # 2. Plan with sequential reasoning
    plan = create_sequential_plan(project_context, global_context)
    
    # 3. Execute with validation
    for step in plan:
        validate_step(step)
        execute_step(step)
        track_outcome(step)
    
    # 4. Consolidate knowledge
    update_project_memory(final_outcomes)
    update_global_memory(generalized_patterns)