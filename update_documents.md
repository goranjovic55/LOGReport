# Update Documents Workflow

This document outlines the systematic documentation maintenance and validation process for ensuring accurate, comprehensive, and well-integrated project documentation.

## Overview

The Update Documents Workflow ensures documentation accuracy and completeness through structured analysis-validation-gap detection-documentation-integration cycles. This system enables continuous improvement of project documentation quality and prevents documentation drift from implementation.

**CORE PATTERN**: Analysis → Validation → Gap Detection → Documentation → Integration

## Workflow Activation

### Trigger Conditions
Documentation update activates when:
- **Post-implementation**: Major features or architecture changes completed
- **Documentation drift**: >30% discrepancy between docs and code detected
- **Gap detection**: Missing documentation for >20% of public APIs or components
- **Periodic audit**: Quarterly scheduled documentation reviews
- **Memory insights**: New patterns identified requiring documentation

### Scope Definition
- **Target areas**: Outdated docs, missing documentation, architectural changes
- **Quality baseline**: Current documentation coverage and accuracy scores
- **Goals**: Achieve comprehensive coverage, eliminate inaccuracies, improve discoverability
- **Success metrics**: Coverage ≥90%, accuracy ≥95%, integration score ≥85%

## Documentation Phases

### Phase 1: Analysis
**Goal**: Understand current implementation and documentation state

**Process**:
1. **Code Analysis**: Map current codebase structure and public interfaces
2. **Documentation Inventory**: Catalog existing documentation and its scope
3. **Architecture Assessment**: Identify architectural patterns and decisions
4. **API Discovery**: Enumerate public APIs, components, and services

### Phase 2: Validation
**Goal**: Compare documentation against actual implementation

**Process**:
1. **Accuracy Verification**: Validate documented behavior against code reality
2. **Example Testing**: Verify code examples and usage patterns work correctly
3. **Link Validation**: Check internal and external documentation links
4. **Version Alignment**: Ensure documentation matches current implementation version

### Phase 3: Gap Detection
**Goal**: Identify missing, incomplete, or outdated documentation

**Process**:
1. **Coverage Analysis**: Identify undocumented components and APIs
2. **Completeness Review**: Check for missing sections in existing docs
3. **Outdated Content**: Flag documentation that no longer reflects implementation
4. **User Journey Gaps**: Identify missing documentation for common user workflows

### Phase 4: Documentation
**Goal**: Create, update, and improve documentation content

**Content Types**:
- **API Documentation**: Complete interface documentation with examples
- **Architecture Documentation**: System design, patterns, and decisions
- **User Guides**: Step-by-step workflows and tutorials
- **Developer Documentation**: Setup, contribution guidelines, and internal patterns

**Quality Standards**:
- Clear, concise writing with consistent terminology
- Working code examples and usage patterns
- Proper cross-referencing and navigation
- Version-appropriate content

### Phase 5: Integration
**Goal**: Ensure documentation is discoverable and well-connected

**Process**:
1. **Memory Integration**: Link documentation to project and global memory
2. **Cross-Referencing**: Create proper internal links and navigation
3. **Discoverability**: Ensure docs are findable through search and browsing
4. **Validation Testing**: Verify documentation serves its intended purpose

## Documentation Categories

### Primary Documentation Types
- **Architecture**: Design patterns, system blueprints, ADRs, technical decisions
- **API Reference**: Interface documentation, parameters, examples, error handling
- **User Guides**: Installation, configuration, usage workflows, troubleshooting
- **Developer**: Contributing guidelines, code standards, internal patterns, testing

### Documentation Quality Metrics
- **Coverage**: Percentage of public APIs and components documented
- **Accuracy**: Correctness of documented behavior vs. implementation
- **Completeness**: Presence of required sections (purpose, usage, examples)
- **Freshness**: Documentation age relative to last code changes

## Validation Algorithm

**Pattern**: Inventory → Compare → Identify → Prioritize → Document

**Process**:
1. Create comprehensive documentation inventory
2. Compare documented behavior against code implementation
3. Identify gaps, inaccuracies, and improvement opportunities
4. Prioritize updates based on impact and usage frequency
5. Execute documentation updates with validation

**Quality Gates**: Coverage ≥90%, accuracy ≥95%, broken links = 0

## Pattern Recognition

**Documentation Patterns**:
- Identify common documentation structures across components
- Standardize documentation templates and formats
- Create reusable documentation patterns for similar components
- Track documentation effectiveness and user feedback

## Orchestrator Integration

### Delegation Pattern
```
new_task(
  message="DOCUMENTATION UPDATE CYCLE
  OBJECTIVE: Analyze and update project documentation for accuracy and completeness
  CONTEXT: {recent_changes_and_current_docs_state}
  FOCUS: {target_components_or_documentation_areas}
  TARGETS: Coverage ≥90%, accuracy ≥95%, zero broken links",
  mode="mcp-document"
)
```

### Quality Gates
- **Pre-update**: Backup existing documentation and create baseline metrics
- **During update**: Validate examples and verify accuracy continuously
- **Post-update**: Test documentation effectiveness and user workflows

## Success Criteria

### Quality Thresholds
**Minimum**: Coverage ≥70%, accuracy ≥85%, major gaps eliminated
**Good**: Coverage ≥85%, accuracy ≥90%, navigation improved, examples verified
**Excellent**: Coverage ≥90%, accuracy ≥95%, comprehensive cross-referencing, user-tested

### Validation Report Template
```json
{
  "documentation_update_id": "docs_update_2025_08_15",
  "trigger": "post_implementation",
  "analysis_completed": true,
  "metrics": {
    "before": {
      "coverage_score": 65,
      "accuracy_score": 78,
      "broken_links": 12,
      "outdated_sections": 8
    },
    "after": {
      "coverage_score": 92,
      "accuracy_score": 96,
      "broken_links": 0,
      "outdated_sections": 1
    },
    "improvements": {
      "coverage_gain": "+27%",
      "accuracy_improvement": "+18%",
      "links_fixed": "100%"
    }
  },
  "updates_performed": {
    "docs_created": 5,
    "docs_updated": 12,
    "examples_added": 8,
    "links_fixed": 12
  }
}
```

## Best Practices

- Analyze code structure before updating documentation
- Validate examples and code snippets for accuracy
- Maintain consistent terminology and formatting
- Create clear navigation and cross-references
- Test documentation from user perspective
- Integrate documentation insights into project memory
