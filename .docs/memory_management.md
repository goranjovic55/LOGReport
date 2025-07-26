# 🧠 Dual Memory Consolidation Workflow

This document outlines the standardized process for managing and consolidating project and global memory within the system.

## ♻️ Step-by-Step Consolidation Plan

### 1. 🔓 Memory Loading Step

* Use **MCP server tools available on the `global_memory` server** to load global memory (persistent cross-project insights).
* Use **MCP server tools available on the `project_memory` server** to load project-local memory (entities, structures, known issues).
* These tools must be discovered, interpreted, and invoked within the server context using their appropriate invocation interfaces.
* Verify successful loading of both memory contexts before proceeding.

### 2. 👤 Identity-Based Scoping

* Determine the user identity from the current mode:
  * For example: `debug-mode` → `debug_user`, `auto-doc-writer` → `docs_user`
  * If the mode is unknown, fall back to a generic identity like `default_user`
* Use this identity to scope all memory operations consistently across both memory types.
* Validate that the identity is properly set and accessible for all subsequent operations.

### 3. 🎯 Analyze Project Structure

* Scan the following areas, and analyze each independently:
  * Source code (`src/`)
  * Documentation (`.docs/`)
  * Key project metadata (`README.md`, `TODO.md`, `CHANGELOG.md`)
* Document any inconsistencies or issues found during analysis.
* Handle errors gracefully if any area is inaccessible or malformed.

### 4. 🌐 Leverage External References

* Use `firecrawl_mcp(...)` MCP server tools to:
  * Search GitHub, Reddit, SuperUser for domain models and naming conventions
  * Validate or improve the knowledge graph structure
  * Explore how other systems model similar entities
* Use `context7(...)` MCP server tools to:
  * Retrieve official documentation and API standards
  * Compare against language or framework standards
  * Access accurate syntax examples and best practices
* Validate findings from external sources before applying them.

### 5. 🧠 Plan Consolidation

* Use `sequential_thinking(...)` MCP server tools to:
  * Detect duplicated or fragmented entities
  * Spot weak or missing relationships
  * Identify unlinked bugs, configs, or features
  * Identify differences between memories and documentation and source code.
  * Suggest generalization or promotion of reusable insights
* Document the consolidation plan with clear justifications for each proposed change.
* Validate the plan with consistency checks before execution.

### 6. 📅 Knowledge Tracking During Execution

* While performing tasks, record new facts, structural inferences, behaviors, naming decisions, and task outcomes:
  * Use **tools from the `project_memory` MCP server** for project-specific knowledge
  * Use **tools from the `global_memory` MCP server** for reusable abstractions or cross-project patterns
* Track intermediate states and decisions for auditability.
* Handle any errors in knowledge recording without stopping the overall workflow.

### 7. ✏️ Apply Memory Updates

* In `project_memory(...)` MCP server tools, apply changes:
  * Merge duplicates
  * Rename and re-cluster entities
  * Remove or add entities and observations based on documents and source code
  * Link configs, services, modules, or events logically
* In `global_memory(...)` MCP server tools, promote:
  * Generalized concepts
  * Reusable structures
  * Canonical workflows or naming patterns
* Validate each update to ensure consistency and correctness.

### 8. ✅ Validation Steps

* Perform consistency checks on both memory graphs:
  * Verify no broken relationships or orphaned entities
  * Confirm all promoted patterns are correctly applied
  * Check for any conflicts between project and global memory
* Validate that all changes align with the original consolidation plan.
* Handle validation failures with appropriate error reporting and recovery options.

### 9. 🧹 Global Memory Cleanup

* Once key insights are promoted to global memory:
  * Re-analyze for duplication or overlap
  * Use `sequential_thinking(...)` MCP server tools to clean, deduplicate, and restructure
  * Finalize updates to global memory graph
* Ensure global memory remains consistent and optimized.
* Handle any cleanup errors without affecting the overall process.

### 10. 🚪 Session Closure

* Confirm all memory operations are completed:
  * Verify all project-specific insights are properly recorded in `project_memory`
  * Ensure all reusable patterns are correctly promoted to `global_memory`
* Perform final consistency checks on both memory graphs.
* Log session completion with timestamp and summary of operations performed.
* Handle any last-minute errors or inconsistencies that might affect session closure.

### 11. ⚠️ Error Handling and Recovery

* Implement error handling for each major step:
  * Memory loading failures should attempt fallback mechanisms
  * Analysis errors should skip problematic areas but continue with valid ones
  * Update failures should rollback changes and report detailed error information
  * Validation failures should provide recovery options or alternative approaches
* Log all errors with sufficient context for debugging and recovery.
* Ensure graceful degradation when non-critical steps fail.

### 12. 📋 Final Summary

* Summarize everything in a clear `attempt_completion(result="...")` output, including:
  * What was updated and why
  * How memory graphs improved
  * Patterns or reusable abstractions discovered
  * Any issues encountered and how they were resolved
  * Validation results and consistency checks
  * Session closure confirmation and final state of memory graphs