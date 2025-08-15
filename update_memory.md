# Memory Optimization Workflow

This document outlines the cyclical memory optimization process for maintaining high-quality, well-connected memory graphs.

## Overview

The Memory Optimization Workflow ensures optimal connectivity and semantic coherence through structured analysis-prune-reconnect-cluster cycles. This system enables continuous improvement of both project-specific and global memory.

**CORE PATTERN**: Trigger Assessment → Cyclical Optimization → Convergence Validation → Results Integration

## Workflow Activation

### Trigger Conditions
Memory optimization activates when:
- **Post-task completion**: Significant insights generated
- **Memory growth**: >50 new entities since last optimization
- **Periodic maintenance**: Weekly scheduled cycles
- **Quality degradation**: Connectivity score <80%
- **Orphan detection**: >10 unconnected nodes

### Scope Definition
- **Target areas**: Recent entities, orphaned nodes, weak clusters
- **Quality baseline**: Current connectivity and coherence scores
- **Goals**: Reduce redundancy, improve navigation, strengthen boundaries
- **Success metrics**: Connectivity ≥90%, coherence ≥85%, efficiency +20%

## Optimization Phases

### Phase 1: Analysis
**Goal**: Identify optimization opportunities

**Process**:
1. **Graph Topology**: Map node connections and identify orphans
2. **Domain Boundaries**: Analyze clustering and cross-domain relationships
3. **Redundancy Detection**: Find duplicates and circular dependencies
4. **Quality Assessment**: Calculate connectivity and coherence metrics

### Phase 2: Pruning
**Goal**: Remove redundancies and optimize structure

**Process**:
1. **Duplicate Elimination**: Merge identical entities, preserve best content
2. **Weak Connection Removal**: Remove low-relevance relationships
3. **Content Optimization**: Compress descriptions, remove outdated information

### Phase 3: Reconnection
**Goal**: Connect ALL entities and create observations

**Process**:
1. **Universal Connection**: Connect every entity to at least 2 other entities (NO orphans allowed)
2. **Domain Assignment**: Organize entities into appropriate clusters
3. **Hierarchical Structure**: Build domain taxonomies and abstraction layers
4. **Semantic Bridges**: Connect related concepts across domains
5. **Observation Creation**: Create higher-level observations from patterns in multiple memories
6. **Memory Condensation**: Merge related memories into observations when ≥3 similar entities exist

### Phase 4: Clustering
**Goal**: Organize into coherent, navigable domains

**Domains**:
- **Architecture**: Design patterns, system blueprints, decisions
- **Implementation**: Code patterns, services, components
- **Quality**: Testing strategies, debugging, optimization
- **Process**: Workflows, methodologies, best practices

**Validation**:
- Each cluster ≥5 entities
- Intra-cluster connectivity ≥80%
- Clear boundaries, minimal overlap

### Phase 5: Validation
**Goal**: Measure improvements

**Metrics**:
- Connectivity score (target: 100% - ALL entities connected)
- Path length between entities (target: ≤3 hops)
- Orphaned nodes (target: 0 - MANDATORY)
- Domain coherence (target: ≥85%)
- Observations created from memory patterns (target: ≥1 per 5 similar memories)
- Memory condensation ratio (target: 10-15% reduction through observation creation)

## Convergence Algorithm

**Pattern**: Analysis → Score → Decision → Report

**Process**:
1. Execute analysis phase
2. Calculate optimization score (connectivity + coherence + efficiency)
3. If improvement >5%: continue optimization cycles
4. If improvement ≤5%: optimization complete

**Limits**: Maximum 10 cycles, connectivity = 100%, coherence ≥85%, ZERO orphans (all entities connected)

## Pattern Recognition

**Cross-Project Patterns**:
- Identify patterns in ≥2 project contexts
- Analyze stability and reusability
- Promote validated patterns to global memory
- Track adoption and lifecycle

## Orchestrator Integration

### Delegation Pattern
```
new_task(
  message="MEMORY OPTIMIZATION CYCLE
  OBJECTIVE: Optimize memory graph through cyclical optimization
  CONTEXT: {completion_insights_and_memory_state}
  FOCUS: {target_domains_or_entities}
  TARGETS: Connectivity = 100%, coherence ≥85%, ZERO orphans, create observations from patterns",
  mode="mcp-memory"
)
```

### Quality Gates
- **Pre-optimization**: Create memory snapshot backup
- **During optimization**: Monitor progress and quality metrics
- **Post-optimization**: Validate integrity and achievement

## Success Criteria

### Quality Thresholds
**Minimum**: Connectivity = 100%, orphans = 0, coherence ≥80%
**Good**: Connectivity = 100%, orphans = 0, coherence ≥85%, observations created from ≥3 memory patterns
**Excellent**: Connectivity = 100%, orphans = 0, coherence ≥90%, memories condensed into observations, efficiency +25%

### Report Template
```json
{
  "optimization_id": "memory_opt_2025_08_15",
  "iterations": 4,
  "convergence": true,
  "before": {"connectivity": 72, "orphans": 23, "coherence": 68, "total_entities": 156},
  "after": {"connectivity": 100, "orphans": 0, "coherence": 87, "total_entities": 142},
  "improvements": {"connectivity": "+28%", "efficiency": "+23.5%", "condensed": "14 entities into 6 observations"},
  "actions": {"merged": 35, "connected": 127, "observations_created": 6, "condensed": 14}
}
```

## Best Practices

- Load memory context before optimization
- Execute phases sequentially
- Validate improvements before persisting
- Monitor convergence to prevent loops
- Preserve critical connections
- Document outcomes for reference
