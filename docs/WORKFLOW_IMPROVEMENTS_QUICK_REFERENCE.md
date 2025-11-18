# 11-Phase Workflow Improvement Quick Reference

## Overview
Quick reference guide for implementing improvements to the 11-phase workflow system based on edge case analysis.

---

## P0 (Critical) - Implement Immediately

### 1. Automatic Backup Rotation
**File:** `scripts/backup_manager.py`
**When:** Before every memory write
**Code:**
```python
def backup_memory(memory_path: Path) -> None:
    if memory_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = memory_path.parent / f"{memory_path.stem}_backup_{timestamp}.json"
        shutil.copy(memory_path, backup_path)
        # Keep last 10 backups
        backups = sorted(memory_path.parent.glob(f"{memory_path.stem}_backup_*.json"))
        for old_backup in backups[:-10]:
            old_backup.unlink()
```

### 2. Enhanced Memory Recovery
**File:** `scripts/memory_recovery.py`
**When:** On JSON parse error
**Code:**
```python
def recover_memory(memory_path: Path) -> dict:
    # Stage 1: Try direct parse
    # Stage 2: Try repair
    # Stage 3: Try latest backup
    # Stage 4: Extract partial data
    # Stage 5: Create empty (last resort)
```

### 3. CEPH State Persistence
**File:** `src/core/ceph_tracker.py`
**When:** Every CEPH update
**Code:**
```python
class CEPHTracker:
    def update(self, phase: str, ceph: dict) -> None:
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "ceph": ceph.copy()
        })
        self._save_history()
```

---

## P1 (High) - Implement Within 1 Sprint

### Memory System

**A3: Proactive Size Monitoring**
- Check after LEARN phase
- Warn at 4500 lines (90%)
- Optimize at 5000 lines

**G2: Chunked Loading**
- Load by domain priority
- Limit to 50,000 tokens
- Load recent 10 entities

### Codegraph System

**B1: Progressive Loading**
- Load metadata first
- Load sections with timeout
- Lazy-load relations

**B2: Auto-Rebuild**
- Detect empty codegraph
- Run `scripts/generate_codegraph.py`
- Report success/failure

### Protocol Enforcement

**D1: Validation Schema**
```yaml
SCP-START:
  required: [LOADED, COMPLIANT, READY, NWP]
SCP-PHASE:
  required: [VIOLATIONS, ADJUST, NWP]
```

**E1: Tool Usage Auditing**
- Track all tool calls
- Verify query claims
- Report discrepancies

### Test Phase

**F1: Verification Gate**
```python
class TestVerificationGate:
    def is_blocked(self, phase: str) -> bool:
        if not self.status or self.status.get("verified"):
            return False
        return phase in self.status.get("blocking", [])
```

**F2: Metrics Baseline**
```python
class MetricsBaseline:
    def format_with_delta(self, metrics: dict) -> str:
        # Calculate delta from baseline
        # Format: tests=14/14(+14)|coverage=95%(+5)
```

### Context Management

**G1: Proactive Pruning**
```python
def check_budget(self) -> dict:
    usage_percent = (current_tokens / max_tokens) * 100
    if usage_percent > 95:
        return {"status": "critical", "action": "prune_immediately"}
    elif usage_percent > 80:
        return {"status": "warning", "action": "prune_low_priority"}
```

### Workflow Intelligence

**C1: Guided Decomposition**
```python
def analyze_decomposition(task: str) -> List[str]:
    # Split on: "and", "then", "before", "after"
    # Return subtask suggestions
```

---

## P2 (Medium) - Implement Within 2-3 Sprints

### B3: Configurable Query Limits
- Base on token budget
- Default: 100 results
- Max: 1000 results

### C2: Stack Persistence
- Save stack on NEST/RETURN
- Validate age (<1 hour)
- Resume if fresh

### C3: Adaptive Nesting
- Hard limit: 4 levels
- Allow depth 3 for critical scenarios
- Check token budget (>20%)

### D3: Advanced Passive Detection
- Use spaCy NLP
- Detect passive voice
- Suggest active rewrites

### E2: Query Utilization
- Track query results
- Check usage in code
- Report utilization rate

---

## Implementation Checklist

### Phase 1: Foundation (Weeks 1-2)
- [ ] Create `scripts/backup_manager.py`
- [ ] Create `scripts/memory_recovery.py`
- [ ] Create `src/core/ceph_tracker.py`
- [ ] Add unit tests for recovery
- [ ] Update REMEMBER phase to use backups
- [ ] Document recovery procedures

### Phase 2: Enforcement (Weeks 3-4)
- [ ] Create protocol validation schema
- [ ] Create `src/core/query_auditor.py`
- [ ] Create `src/core/verification_gate.py`
- [ ] Create `src/core/metrics_baseline.py`
- [ ] Add integration tests
- [ ] Update TEST phase with gate

### Phase 3: Scaling (Weeks 5-6)
- [ ] Add memory size monitoring
- [ ] Create `src/core/codegraph_loader.py` (progressive)
- [ ] Add auto-rebuild to ASSESS phase
- [ ] Create `src/core/context_manager.py`
- [ ] Add chunked memory loading
- [ ] Performance tests for large projects

### Phase 4: Intelligence (Weeks 7-8)
- [ ] Create `src/core/decomposer.py`
- [ ] Add query utilization tracking
- [ ] Integrate spaCy for passive detection
- [ ] Add configurable query limits
- [ ] Create quality metrics dashboard

### Phase 5: Resilience (Weeks 9-10)
- [ ] Add workflow stack persistence
- [ ] Implement adaptive nesting
- [ ] Add interrupt/resume tests
- [ ] Update all documentation
- [ ] Create training materials

---

## Testing Strategy

### Unit Tests
```python
# tests/workflow/test_backups.py
def test_backup_rotation()
def test_backup_limit_10()

# tests/workflow/test_recovery.py
def test_recovery_stages()
def test_partial_extraction()

# tests/workflow/test_ceph_persistence.py
def test_ceph_history()
def test_dropout_detection()
```

### Integration Tests
```python
# tests/integration/test_verification_gate.py
def test_blocked_progression()
def test_user_approval()

# tests/integration/test_codegraph_loading.py
def test_progressive_load()
def test_timeout_handling()
```

### Performance Tests
```python
# tests/performance/test_large_memory.py
def test_10000_line_memory()
def test_chunked_loading_speed()

# tests/performance/test_context_budget.py
def test_pruning_efficiency()
```

---

## Monitoring Setup

### Metrics to Track
```python
{
    "memory": {
        "project_lines": 3245,
        "global_lines": 620,
        "last_backup": "2m ago",
        "recovery_success_rate": 0.973
    },
    "codegraph": {
        "entities": 1247,
        "load_time_seconds": 3.2,
        "query_success_rate": 0.991
    },
    "workflow": {
        "protocol_compliance": 1.0,
        "query_requirement_compliance": 0.987,
        "ceph_dropout_incidents": 3
    },
    "token_budget": {
        "current_usage": 0.327,
        "peak_24h": 0.543,
        "exhaustion_incidents": 0
    }
}
```

### Alerts
- Memory corruption → immediate
- Token budget >95% → warning
- Test verification bypassed → critical
- CEPH dropout → warning
- Nesting depth >2 → info

---

## Configuration Examples

### `.workflow_config.json`
```json
{
    "memory": {
        "backup_count": 10,
        "size_warning_threshold": 4500,
        "size_critical_threshold": 5000
    },
    "codegraph": {
        "load_timeout_seconds": 10,
        "progressive_load_threshold_mb": 10,
        "query_result_limit": 100
    },
    "nesting": {
        "max_depth": 2,
        "adaptive_depth_enabled": true,
        "adaptive_max_depth": 4
    },
    "token_budget": {
        "total": 1000000,
        "warning_threshold": 0.80,
        "critical_threshold": 0.95,
        "prune_priority_cutoff": 3
    }
}
```

---

## Quick Commands

### Run Edge Case Tests
```bash
python -m pytest tests/workflow/test_edge_cases_11_phase.py -v
```

### Generate Backup
```bash
python scripts/backup_manager.py --memory project_memory.json
```

### Recover Memory
```bash
python scripts/memory_recovery.py --file project_memory.json --stage all
```

### Check Memory Size
```bash
python scripts/check_memory_size.py --warn 4500 --critical 5000
```

### Rebuild Codegraph
```bash
python scripts/generate_codegraph.py --progressive --timeout 60
```

### View Metrics
```bash
python scripts/view_metrics.py --dashboard
```

---

## Support Resources

- **Full Analysis:** `docs/WORKFLOW_EDGE_CASE_ANALYSIS.md`
- **Test Suite:** `tests/workflow/test_edge_cases_11_phase.py`
- **Execution Report:** `docs/EDGE_CASE_SIMULATION_REPORT.md`
- **Instructions:** `.github/instructions/phases.md`, `protocols.md`

---

**Last Updated:** 2025-01-18  
**Version:** 1.0
