# 11-Phase Workflow Edge Case Analysis and Improvement Suggestions

## Executive Summary

This document presents a comprehensive analysis of edge case scenarios for the 11-phase workflow system implemented in the LOGReport repository. Based on simulation testing and analysis of the instruction files (phases.md, protocols.md, copilot-instructions.md), we identify critical failure patterns and propose actionable improvements to enhance robustness, error recovery, and developer experience.

## Table of Contents

1. [Edge Case Categories](#edge-case-categories)
2. [Critical Findings](#critical-findings)
3. [Improvement Suggestions](#improvement-suggestions)
4. [Priority Recommendations](#priority-recommendations)
5. [Implementation Roadmap](#implementation-roadmap)

---

## Edge Case Categories

### 1. Memory System Failures

**Edge Cases Tested:**
- Missing memory files (project_memory.json, global_memory.json)
- Corrupted JSON (parse errors, incomplete data)
- Oversized memory (>5000 lines)
- Both memories corrupted simultaneously (CRITICAL)

**Current Handling (per copilot-instructions.md:64-67):**
```
Missing:    Create empty → VIOLATIONS:[memory_missing→created_empty]
Corrupted:  Repair script → VIOLATIONS:[corrupted_LX-Y→rebuilt]
Oversized:  Auto-optimizer → VIOLATIONS:[oversized_N→condensed:M]
Both:       Empty both → VIOLATIONS:[total_corruption→empty_files:CRITICAL]
```

**Issues Identified:**
- No automatic backup restoration before creating empty files
- Repair script dependency not documented (which script? where?)
- Auto-optimizer path resolution unclear (searches .github/ for global)
- Loss of data when both corrupted (only creates empty, no recovery attempt)

### 2. Codegraph System Failures

**Edge Cases Tested:**
- Empty codegraph (entities=0)
- Query returns 0 results
- Load timeout (>10s)
- Query result truncation (>1000 results)

**Current Handling (per copilot-instructions.md:68-71):**
```
Empty:       Valid state → DISCOVERIES:[codegraph_empty]
Query=0:     Valid state → DISCOVERIES:[query_X_returned_0]
Timeout:     Retry once → VIOLATIONS:[codegraph_timeout→retry]
Truncation:  First 100 → DISCOVERIES:[query_truncated:N→100]
```

**Issues Identified:**
- No guidance on rebuilding empty codegraph
- Single retry for timeout may be insufficient (network issues)
- Truncation limit (100 results) may be too restrictive for large projects
- No progressive loading strategy for large codegraphs

### 3. Workflow Nesting Violations

**Edge Cases Tested:**
- Nesting depth >2 levels
- Test failure without NEST (inline fixes)
- RETURN with empty stack
- Concurrent nested interruptions

**Current Handling (per copilot-instructions.md:72-73):**
```
Depth>2:       HALT → DISCOVERIES:[CRITICAL_NESTING:decompose]
Test no NEST:  MANDATORY → [SCP-NWP: NEST→test_failure]
Empty stack:   ERROR (implementation dependent)
```

**Issues Identified:**
- Hard limit of 2 may be too restrictive for complex debugging
- No automatic decomposition suggestions when depth limit hit
- Test failure detection relies on keyword scanning (brittle)
- No stack persistence across session interruptions

### 4. Protocol Format Violations

**Edge Cases Tested:**
- Missing SCP-START at session init
- Missing SCP-PHASE gates between phases
- CEPH field dropout (EXPECTED, PROBLEM, etc.)
- Malformed protocol tags

**Current Handling (per copilot-instructions.md:55-56, protocols.md:117):**
```
Missing START:  Violation → emit immediately
Missing PHASE:  Violation → emit + block
CEPH dropout:   Detect → restore from previous
Format error:   Auto-correct → rewrite
```

**Issues Identified:**
- Pre-send verification relies on pattern matching (fragile)
- CEPH restoration assumes previous response accessible (may not be)
- No validation schema for protocol structure
- Passive language detection ("I'll", "Would you") too simplistic

### 5. Query Requirement Violations

**Edge Cases Tested:**
- IMPLEMENT with <3/5 codegraph queries
- DEBUG with <2/4 codegraph queries
- Queries without actual tool usage
- Query results not utilized in decisions

**Current Handling (per phases.md:42-43, 49-51):**
```
IMPLEMENT: 3/5 minimum or SCP-PHASE blocks
DEBUG:     2/4 minimum or SCP-PHASE blocks
Track:     Emit CODEGRAPH_QUERIES:[N/M]
```

**Issues Identified:**
- No enforcement mechanism (relies on self-reporting)
- Count-based metric doesn't ensure query quality
- No verification that query results influenced implementation
- Ambiguity about what constitutes a "query" (file read vs semantic search)

### 6. Test Phase Violations

**Edge Cases Tested:**
- Metrics without delta (Δ)
- Missing USER_VERIFICATION:[awaiting:YES]
- Continuing to LEARN/DOC/LOG without user approval
- Test pass without coverage metrics

**Current Handling (per phases.md:55-60, protocols.md:59-60):**
```
Missing Δ:       Violation → add delta
No verification: Violation → emit + BLOCK
Continue early:  BLOCK next phases
```

**Issues Identified:**
- Delta calculation requires baseline tracking (may not exist)
- User verification blocking is conceptual (no actual gate mechanism)
- No timeout for user response (indefinite wait)
- Coverage metrics not required (only tests pass/fail)

### 7. Memory Learning Violations

**Edge Cases Tested:**
- LEARN with <3 entities
- Duplicate entity extraction
- Malformed entity structure
- Entity size limits

**Current Handling (per phases.md:64):**
```
<3 entities: BLOCK finalization → VIOLATIONS:[learn_minimum_not_met:N<3]
```

**Issues Identified:**
- Arbitrary minimum of 3 (may not apply to small changes)
- No quality check on entities (duplication, relevance)
- No size limits per entity (could bloat memory)
- No validation of entity structure before appending

### 8. Token Budget Exhaustion

**Edge Cases Tested:**
- Context >95% used
- Large file operations near limit
- Deep nesting consuming context
- Memory/codegraph loading overhead

**Current Handling (per copilot-instructions.md:76):**
```
>95%: DISCOVERIES:[token_budget:CRITICAL:95%] → prepare finalize
```

**Issues Identified:**
- Only warns, no proactive mitigation
- No chunking strategy for large operations
- No prioritization of essential vs nice-to-have context
- Deep nesting amplifies token usage (CEPH carried through)

---

## Critical Findings

### Finding 1: Catastrophic Memory Loss Scenarios

**Problem:** When both project and global memories are corrupted, the system creates empty files without attempting any recovery, leading to total loss of accumulated knowledge.

**Impact:** CRITICAL - Loss of months/years of distilled patterns and learnings.

**Evidence:** 
- copilot-instructions.md:66: "Create empty both, continue, rebuild in LEARN"
- No backup strategy mentioned
- LEARN phase may not recover all lost knowledge

**Root Cause:** Defensive failure handling prioritizes continuing work over data integrity.

### Finding 2: Workflow Nesting Depth Limitation

**Problem:** Hard limit of 2 nesting levels may be insufficient for complex debugging scenarios requiring multiple layers of investigation.

**Impact:** HIGH - Forces premature abandonment of deep investigation paths.

**Evidence:**
- copilot-instructions.md:73: "Nesting depth >2 → HALT, report critical nesting"
- protocols.md:93: "Depth>2: DISCOVERIES:[CRITICAL_NESTING:decompose_problem]"
- No decomposition guidance provided

**Root Cause:** Token budget concerns and complexity management.

### Finding 3: Query Requirement Enforcement Gap

**Problem:** Codegraph query minimums (3/5 for IMPLEMENT, 2/4 for DEBUG) rely on self-reporting without verification, allowing compliance theater.

**Impact:** MEDIUM - Quality degradation when queries are logged but not meaningfully used.

**Evidence:**
- phases.md:42-43: "Track: Emit `CODEGRAPH_QUERIES:[N/5]` during work"
- No tool usage verification
- No query result utilization check

**Root Cause:** Trust-based system without enforcement mechanism.

### Finding 4: Test Phase Checkpoint Not Actually Blocking

**Problem:** USER_VERIFICATION:[awaiting:YES] is documented to BLOCK subsequent phases, but there's no actual enforcement mechanism preventing continuation.

**Impact:** MEDIUM - Tests may pass locally but fail in other environments if verification skipped.

**Evidence:**
- protocols.md:60: "USER_VERIFICATION:[awaiting:YES] = END RESPONSE"
- phases.md:55: "🛑 CHECKPOINT: Present, emit USER_VERIFICATION:[awaiting:YES], BLOCKING:[LEARN,DOCUMENT,LOG], END RESPONSE"
- Relies on AI agent adherence, no tooling gate

**Root Cause:** Protocol is instructional rather than enforced by tooling.

### Finding 5: CEPH Dropout Detection Fragility

**Problem:** CEPH field restoration assumes previous response is accessible in context, which may not be true in long sessions or after interruptions.

**Impact:** MEDIUM - CEPH evolution tracking lost, reducing workflow quality.

**Evidence:**
- protocols.md:117: "ADJUST:[CEPH_dropout:field→restore_from_L{line}]"
- No persistent CEPH storage between responses
- Line number references become invalid after context shifts

**Root Cause:** Stateful protocol in stateless conversation system.

---

## Improvement Suggestions

### Category A: Memory System Resilience

#### A1: Implement Automatic Backup Rotation

**Description:** Create timestamped backups before any memory write operation.

**Implementation:**
```python
# Before writing memory:
def backup_memory(memory_path: Path) -> None:
    if memory_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = memory_path.parent / f"{memory_path.stem}_backup_{timestamp}.json"
        shutil.copy(memory_path, backup_path)
        
        # Rotate: keep last 10 backups
        backups = sorted(memory_path.parent.glob(f"{memory_path.stem}_backup_*.json"))
        for old_backup in backups[:-10]:
            old_backup.unlink()
```

**Benefits:**
- Prevents catastrophic data loss
- Enables temporal rollback
- Minimal storage overhead (~50MB for 10 backups)

**Priority:** P0 (Critical)

#### A2: Enhanced Memory Corruption Recovery

**Description:** Multi-stage recovery strategy before resorting to empty files.

**Implementation:**
```python
def recover_memory(memory_path: Path) -> dict:
    # Stage 1: Try direct parse
    try:
        return json.loads(memory_path.read_text())
    except json.JSONDecodeError:
        pass
    
    # Stage 2: Try repair (fix common issues)
    try:
        return repair_json(memory_path)
    except:
        pass
    
    # Stage 3: Try latest backup
    backups = sorted(memory_path.parent.glob(f"{memory_path.stem}_backup_*.json"))
    for backup in reversed(backups):
        try:
            return json.loads(backup.read_text())
        except:
            continue
    
    # Stage 4: Extract partial data
    try:
        return extract_partial_entities(memory_path)
    except:
        pass
    
    # Stage 5: Create empty (last resort)
    return {"entities": []}
```

**Benefits:**
- Maximizes data recovery
- Documents recovery path in VIOLATIONS
- Reduces CRITICAL failures

**Priority:** P0 (Critical)

#### A3: Memory Size Monitoring and Proactive Optimization

**Description:** Monitor memory size after each LEARN phase and proactively optimize before hitting 5000 line threshold.

**Implementation:**
```python
# After LEARN phase:
def check_memory_size(memory_path: Path) -> dict:
    line_count = sum(1 for _ in open(memory_path))
    
    if line_count > 4500:  # 90% of threshold
        return {
            "status": "warning",
            "action": "optimize_recommended",
            "lines": line_count
        }
    elif line_count > 5000:
        return {
            "status": "critical",
            "action": "optimize_required",
            "lines": line_count
        }
    
    return {"status": "ok", "lines": line_count}
```

**Benefits:**
- Prevents oversized memory emergencies
- Allows scheduled optimization windows
- Maintains performance

**Priority:** P1 (High)

### Category B: Codegraph Reliability

#### B1: Progressive Codegraph Loading

**Description:** Load codegraph in chunks for large projects to avoid timeout.

**Implementation:**
```python
def load_codegraph_progressive(codegraph_path: Path, timeout: int = 10) -> dict:
    """Load codegraph with timeout protection"""
    start = time.time()
    
    # Load metadata first
    with open(codegraph_path) as f:
        header = json.loads(f.readline())  # First line: metadata
    
    if header.get("size_mb", 0) > 10:  # Large codegraph
        # Load in sections
        sections = ["modules", "classes", "methods"]
        codegraph = {}
        
        for section in sections:
            if time.time() - start > timeout:
                return {"status": "partial", "loaded": list(codegraph.keys())}
            
            codegraph[section] = load_section(codegraph_path, section)
        
        # Relations loaded on-demand
        codegraph["relations"] = LazyRelationLoader(codegraph_path)
        return codegraph
    
    # Small codegraph: load normally
    return json.loads(codegraph_path.read_text())
```

**Benefits:**
- Eliminates timeout failures
- Scales to large projects
- On-demand relation loading reduces memory

**Priority:** P1 (High)

#### B2: Empty Codegraph Auto-Rebuild

**Description:** When codegraph is empty, automatically trigger rebuild instead of just reporting.

**Implementation:**
```python
# In ASSESS phase:
if codegraph_empty():
    discoveries.append("codegraph_empty:triggering_rebuild")
    
    # Run codegraph generator
    result = subprocess.run(
        ["python", "scripts/generate_codegraph.py"],
        capture_output=True,
        timeout=60
    )
    
    if result.returncode == 0:
        codegraph = load_codegraph(codegraph_path)
        adjust.append("codegraph_rebuilt:success")
    else:
        violations.append("codegraph_rebuild_failed:CRITICAL")
```

**Benefits:**
- Automatic recovery from empty codegraph
- No manual intervention required
- Maintains ASSESS phase quality

**Priority:** P1 (High)

#### B3: Configurable Query Result Limits

**Description:** Make truncation limit configurable based on context budget.

**Implementation:**
```python
def query_codegraph(
    query_type: str,
    max_results: int = None,
    token_budget_remaining: int = None
) -> List[dict]:
    """Query with dynamic result limiting"""
    
    if max_results is None:
        if token_budget_remaining:
            # Estimate: 50 tokens per result
            max_results = min(100, token_budget_remaining // 50)
        else:
            max_results = 100
    
    results = execute_query(query_type)
    
    if len(results) > max_results:
        discoveries.append(
            f"query_truncated:{len(results)}→{max_results}:incomplete"
        )
        return results[:max_results]
    
    return results
```

**Benefits:**
- Adaptive to token budget
- Prevents context overflow
- Documents truncation clearly

**Priority:** P2 (Medium)

### Category C: Workflow Nesting Improvements

#### C1: Guided Decomposition for Deep Nesting

**Description:** When nesting depth hits limit, provide automated decomposition suggestions.

**Implementation:**
```python
def check_nesting_depth(workflow_index: int, current_task: str) -> dict:
    if workflow_index >= 2:
        # Analyze task for decomposition
        suggestions = analyze_decomposition(current_task)
        
        return {
            "status": "limit_reached",
            "current_depth": workflow_index,
            "suggestions": [
                "Create separate task for: " + s
                for s in suggestions
            ],
            "action": "HALT_AND_DECOMPOSE"
        }
    
    return {"status": "ok", "depth": workflow_index}

def analyze_decomposition(task_description: str) -> List[str]:
    """Extract subtasks for decomposition"""
    # Pattern: "Fix X and Y and Z" → ["Fix X", "Fix Y", "Fix Z"]
    # Pattern: "Debug A then refactor B" → ["Debug A", "Refactor B"]
    
    subtasks = []
    
    # Split on conjunctions
    for conjunction in [" and ", " then ", " before ", " after "]:
        if conjunction in task_description.lower():
            parts = task_description.split(conjunction)
            subtasks.extend(p.strip() for p in parts)
    
    return subtasks if subtasks else [task_description]
```

**Benefits:**
- Actionable guidance when depth limit hit
- Maintains investigation continuity across tasks
- Reduces frustration from hard limits

**Priority:** P1 (High)

#### C2: Stack Persistence Across Sessions

**Description:** Persist workflow stack to allow resumption after interruptions.

**Implementation:**
```python
# At each NEST/RETURN:
def persist_workflow_stack(stack: List[dict], path: Path) -> None:
    """Save workflow stack to disk"""
    stack_data = {
        "timestamp": datetime.now().isoformat(),
        "stack": stack,
        "version": "1.0"
    }
    
    with open(path, 'w') as f:
        json.dump(stack_data, f, indent=2)

def restore_workflow_stack(path: Path) -> List[dict]:
    """Restore workflow stack from disk"""
    if not path.exists():
        return []
    
    with open(path) as f:
        data = json.load(f)
    
    # Validate not stale (>1 hour old)
    timestamp = datetime.fromisoformat(data["timestamp"])
    if datetime.now() - timestamp > timedelta(hours=1):
        return []  # Stale, start fresh
    
    return data["stack"]
```

**Benefits:**
- Session interruption resilience
- Enables pause/resume workflows
- Maintains nesting context

**Priority:** P2 (Medium)

#### C3: Adaptive Nesting Depth Limits

**Description:** Allow depth >2 for specific scenarios with token budget checks.

**Implementation:**
```python
def can_nest_deeper(
    current_depth: int,
    token_budget_remaining: int,
    nest_reason: str
) -> bool:
    """Decide if deeper nesting is allowed"""
    
    # Hard limit: 4 levels maximum
    if current_depth >= 4:
        return False
    
    # Token budget check: need 20% remaining
    if token_budget_remaining < 0.20:
        return False
    
    # Allow depth 3 for critical scenarios
    critical_reasons = [
        "repeated_test_failure",
        "architecture_investigation",
        "security_vulnerability"
    ]
    
    if current_depth == 2 and nest_reason in critical_reasons:
        discoveries.append(f"depth_3_allowed:{nest_reason}:token_budget={token_budget_remaining*100:.0f}%")
        return True
    
    return False
```

**Benefits:**
- Flexibility for complex scenarios
- Token budget awareness
- Clear criteria for exceptions

**Priority:** P2 (Medium)

### Category D: Protocol Enforcement

#### D1: Protocol Validation Schema

**Description:** Implement JSON Schema validation for protocol structures.

**Implementation:**
```yaml
# protocol_schema.yaml
SCP-START:
  required:
    - LOADED
    - COMPLIANT
    - READY
    - NWP
  format:
    LOADED: "array of strings"
    COMPLIANT: "array of strings"
    READY: "string"
    NWP: "object with index and depth"

SCP-PHASE:
  required:
    - VIOLATIONS
    - ADJUST
    - NWP
  optional:
    - CEPH
    - LEARNINGS
    - ARTIFACTS
  format:
    VIOLATIONS: "array or 'none'"
    ADJUST: "array or 'none'"
```

```python
def validate_protocol(protocol_text: str, protocol_type: str) -> dict:
    """Validate protocol against schema"""
    schema = load_schema(protocol_type)
    parsed = parse_protocol(protocol_text)
    
    errors = []
    
    # Check required fields
    for field in schema["required"]:
        if field not in parsed:
            errors.append(f"missing_required_field:{field}")
    
    # Check format
    for field, expected_format in schema["format"].items():
        if field in parsed:
            actual_format = type(parsed[field]).__name__
            if actual_format != expected_format:
                errors.append(f"wrong_format:{field}:{expected_format}→{actual_format}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "protocol": parsed
    }
```

**Benefits:**
- Catch malformed protocols before emission
- Standardized validation
- Self-documenting structure

**Priority:** P1 (High)

#### D2: CEPH State Persistence

**Description:** Store CEPH history separately to enable reliable dropout detection.

**Implementation:**
```python
class CEPHTracker:
    """Persistent CEPH state tracking"""
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.history_file = Path(f".ceph_history_{workflow_id}.json")
        self.history = self._load_history()
    
    def update(self, phase: str, ceph: dict) -> None:
        """Record CEPH update"""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "ceph": ceph.copy()
        })
        self._save_history()
    
    def detect_dropout(self, current_ceph: dict) -> List[str]:
        """Detect missing fields compared to last CEPH"""
        if not self.history:
            return []
        
        last_ceph = self.history[-1]["ceph"]
        required_fields = ["CURRENT", "EXPECTED", "PROBLEM", "HYPOTHESES", "EVIDENCE"]
        
        dropouts = []
        for field in required_fields:
            if field in last_ceph and field not in current_ceph:
                dropouts.append(field)
        
        return dropouts
    
    def restore_field(self, field: str) -> Any:
        """Restore dropped field from history"""
        for entry in reversed(self.history):
            if field in entry["ceph"]:
                return entry["ceph"][field]
        return None
```

**Benefits:**
- Reliable CEPH dropout detection
- Survives context limitations
- Enables CEPH auditing

**Priority:** P1 (High)

#### D3: Automated Passive Language Detection

**Description:** Use NLP to detect passive constructions, not just keyword matching.

**Implementation:**
```python
import spacy

nlp = spacy.load("en_core_web_sm")

def detect_passive_language(text: str) -> List[dict]:
    """Detect passive voice using NLP"""
    doc = nlp(text)
    passive_constructions = []
    
    for token in doc:
        # Passive voice: auxiliary verb + past participle
        if token.dep_ == "auxpass":
            # Find the main verb
            for child in token.head.children:
                if child.dep_ == "nsubjpass":
                    passive_constructions.append({
                        "text": token.head.text,
                        "sentence": token.sent.text,
                        "suggestion": rewrite_active(token.sent)
                    })
    
    # Also check for specific phrases
    passive_phrases = [
        "I'll", "I will", "Would you", "Could you", 
        "Let me", "Let's", "I can"
    ]
    
    for phrase in passive_phrases:
        if phrase in text:
            passive_constructions.append({
                "text": phrase,
                "type": "passive_phrase"
            })
    
    return passive_constructions
```

**Benefits:**
- More accurate passive detection
- Provides rewrite suggestions
- Reduces false positives

**Priority:** P2 (Medium)

### Category E: Query Verification

#### E1: Tool Usage Auditing

**Description:** Track actual tool calls to verify codegraph query claims.

**Implementation:**
```python
class QueryAuditor:
    """Audit codegraph query usage"""
    
    def __init__(self):
        self.queries_performed = []
        self.tool_calls = []
    
    def record_tool_call(self, tool: str, args: dict) -> None:
        """Record tool usage"""
        self.tool_calls.append({
            "timestamp": datetime.now().isoformat(),
            "tool": tool,
            "args": args
        })
    
    def verify_queries(self, claimed_queries: List[str]) -> dict:
        """Verify claimed queries match tool usage"""
        actual_queries = [
            call["args"].get("query_type")
            for call in self.tool_calls
            if call["tool"] == "codegraph_query"
        ]
        
        missing = set(claimed_queries) - set(actual_queries)
        extra = set(actual_queries) - set(claimed_queries)
        
        return {
            "claimed": len(claimed_queries),
            "actual": len(actual_queries),
            "verified": len(set(claimed_queries) & set(actual_queries)),
            "missing": list(missing),
            "extra": list(extra),
            "compliant": len(missing) == 0
        }
```

**Benefits:**
- Enforces query requirements
- Prevents compliance theater
- Provides audit trail

**Priority:** P1 (High)

#### E2: Query Result Utilization Tracking

**Description:** Verify query results influenced implementation decisions.

**Implementation:**
```python
def track_query_utilization(query_results: List[dict], implementation_code: str) -> dict:
    """Check if query results were used"""
    
    utilized = []
    unutilized = []
    
    for result in query_results:
        # Check if result entities appear in implementation
        entity_name = result.get("name", "")
        
        if entity_name in implementation_code:
            utilized.append(entity_name)
        else:
            unutilized.append(entity_name)
    
    utilization_rate = len(utilized) / len(query_results) if query_results else 0
    
    return {
        "total_results": len(query_results),
        "utilized": len(utilized),
        "unutilized": len(unutilized),
        "utilization_rate": utilization_rate,
        "warning": utilization_rate < 0.5  # Less than 50% used
    }
```

**Benefits:**
- Ensures queries add value
- Identifies irrelevant queries
- Improves query quality over time

**Priority:** P2 (Medium)

### Category F: Test Phase Enforcement

#### F1: Automated User Verification Gate

**Description:** Implement actual blocking mechanism for USER_VERIFICATION.

**Implementation:**
```python
class TestVerificationGate:
    """Enforce test verification checkpoint"""
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.verification_file = Path(f".verification_{workflow_id}.json")
        self.status = self._load_status()
    
    def request_verification(self, test_results: dict) -> None:
        """Request user verification"""
        self.status = {
            "workflow_id": self.workflow_id,
            "timestamp": datetime.now().isoformat(),
            "test_results": test_results,
            "verified": False,
            "blocking": ["LEARN", "DOCUMENT", "LOG"]
        }
        self._save_status()
        
        print("=" * 80)
        print("🛑 USER VERIFICATION REQUIRED")
        print("=" * 80)
        print(f"Tests: {test_results['passed']}/{test_results['total']} passed")
        print(f"Coverage: {test_results.get('coverage', 'N/A')}")
        print()
        print("Please verify test results before proceeding.")
        print("Commands: 'approve', 'reject [reason]'")
        print("=" * 80)
    
    def is_blocked(self, phase: str) -> bool:
        """Check if phase is blocked"""
        if not self.status or self.status.get("verified"):
            return False
        
        return phase in self.status.get("blocking", [])
    
    def verify(self, approved: bool, reason: str = "") -> None:
        """Record verification"""
        self.status["verified"] = True
        self.status["approved"] = approved
        self.status["reason"] = reason
        self.status["verification_timestamp"] = datetime.now().isoformat()
        self._save_status()
```

**Benefits:**
- Actual enforcement, not conceptual
- Clear user interface
- Prevents premature progression

**Priority:** P1 (High)

#### F2: Baseline Tracking for Metrics Delta

**Description:** Maintain baseline metrics to calculate deltas accurately.

**Implementation:**
```python
class MetricsBaseline:
    """Track test metrics over time"""
    
    def __init__(self, project_root: Path):
        self.baseline_file = project_root / ".test_baseline.json"
        self.baseline = self._load_baseline()
    
    def update(self, metrics: dict) -> dict:
        """Update baseline and calculate delta"""
        
        # Calculate deltas
        deltas = {}
        for key in ["tests_passed", "coverage_percent", "assertions"]:
            current = metrics.get(key, 0)
            previous = self.baseline.get(key, 0)
            deltas[key] = current - previous
        
        # Update baseline
        self.baseline.update(metrics)
        self.baseline["last_updated"] = datetime.now().isoformat()
        self._save_baseline()
        
        return deltas
    
    def format_with_delta(self, metrics: dict) -> str:
        """Format metrics with delta"""
        deltas = self.update(metrics)
        
        def delta_str(value: float, key: str) -> str:
            delta = deltas[key]
            sign = "+" if delta >= 0 else ""
            return f"{value}({sign}{delta})"
        
        return (
            f"tests={metrics['tests_passed']}/{metrics['tests_total']}"
            f"({'+' if deltas['tests_passed'] > 0 else ''}{deltas['tests_passed']})"
            f"|coverage={metrics['coverage_percent']}%"
            f"({'+' if deltas['coverage_percent'] > 0 else ''}{deltas['coverage_percent']})"
            f"|assertions={metrics['assertions']}"
            f"({'+' if deltas['assertions'] > 0 else ''}{deltas['assertions']})"
        )
```

**Benefits:**
- Accurate delta calculation
- Historical tracking
- Automatic formatting

**Priority:** P1 (High)

### Category G: Token Budget Management

#### G1: Proactive Context Pruning

**Description:** Monitor token usage and prune low-value content when nearing limits.

**Implementation:**
```python
class ContextManager:
    """Manage token budget proactively"""
    
    def __init__(self, max_tokens: int = 1000000):
        self.max_tokens = max_tokens
        self.current_tokens = 0
        self.content_priority = {}
    
    def track(self, content_type: str, tokens: int, priority: int) -> None:
        """Track content by priority"""
        self.content_priority[content_type] = {
            "tokens": tokens,
            "priority": priority  # 0=highest, 5=lowest
        }
        self.current_tokens += tokens
    
    def check_budget(self) -> dict:
        """Check token budget status"""
        usage_percent = (self.current_tokens / self.max_tokens) * 100
        
        if usage_percent > 95:
            return {
                "status": "critical",
                "percent": usage_percent,
                "action": "prune_immediately"
            }
        elif usage_percent > 80:
            return {
                "status": "warning",
                "percent": usage_percent,
                "action": "prune_low_priority"
            }
        
        return {"status": "ok", "percent": usage_percent}
    
    def prune_content(self, keep_priority_below: int = 3) -> int:
        """Remove low-priority content"""
        tokens_freed = 0
        
        for content_type, info in list(self.content_priority.items()):
            if info["priority"] >= keep_priority_below:
                tokens_freed += info["tokens"]
                del self.content_priority[content_type]
        
        self.current_tokens -= tokens_freed
        return tokens_freed
```

**Benefits:**
- Prevents sudden context overflow
- Maintains high-priority content
- Enables long-running workflows

**Priority:** P1 (High)

#### G2: Chunked Memory/Codegraph Loading

**Description:** Load large memories and codegraphs in relevant chunks only.

**Implementation:**
```python
def load_memory_selective(
    memory_path: Path,
    domains_needed: List[str],
    max_tokens: int = 50000
) -> dict:
    """Load only relevant memory sections"""
    
    with open(memory_path) as f:
        full_memory = json.load(f)
    
    filtered_memory = {"entities": []}
    tokens_used = 0
    
    # Priority 1: Entities in needed domains
    for entity in full_memory.get("entities", []):
        entity_domain = entity.get("domain", "")
        
        if any(domain in entity_domain for domain in domains_needed):
            entity_tokens = estimate_tokens(json.dumps(entity))
            
            if tokens_used + entity_tokens <= max_tokens:
                filtered_memory["entities"].append(entity)
                tokens_used += entity_tokens
    
    # Priority 2: Recent entities (last 10)
    recent_entities = sorted(
        full_memory.get("entities", []),
        key=lambda e: e.get("last_updated", ""),
        reverse=True
    )[:10]
    
    for entity in recent_entities:
        if entity not in filtered_memory["entities"]:
            entity_tokens = estimate_tokens(json.dumps(entity))
            
            if tokens_used + entity_tokens <= max_tokens:
                filtered_memory["entities"].append(entity)
                tokens_used += entity_tokens
    
    return {
        "memory": filtered_memory,
        "tokens_used": tokens_used,
        "total_entities": len(full_memory.get("entities", [])),
        "loaded_entities": len(filtered_memory["entities"])
    }
```

**Benefits:**
- Reduces token consumption
- Maintains relevance
- Scales to large memories

**Priority:** P1 (High)

---

## Priority Recommendations

### P0 (Critical) - Implement Immediately

1. **A1: Automatic Backup Rotation** - Prevents catastrophic data loss
2. **A2: Enhanced Memory Corruption Recovery** - Multi-stage recovery before empty files
3. **D2: CEPH State Persistence** - Reliable dropout detection

**Rationale:** These address catastrophic failure scenarios that result in irreversible data loss or workflow quality degradation.

### P1 (High) - Implement Within 1 Sprint

1. **A3: Memory Size Monitoring** - Proactive optimization
2. **B1: Progressive Codegraph Loading** - Eliminates timeouts
3. **B2: Empty Codegraph Auto-Rebuild** - Automatic recovery
4. **C1: Guided Decomposition** - Actionable nesting limit guidance
5. **D1: Protocol Validation Schema** - Standardized validation
6. **E1: Tool Usage Auditing** - Enforces query requirements
7. **F1: Automated User Verification Gate** - Actual blocking mechanism
8. **F2: Baseline Tracking for Metrics** - Accurate deltas
9. **G1: Proactive Context Pruning** - Prevents token overflow
10. **G2: Chunked Memory Loading** - Scales to large projects

**Rationale:** These significantly improve robustness, enforce critical requirements, and enable scaling to larger projects.

### P2 (Medium) - Implement Within 2-3 Sprints

1. **B3: Configurable Query Limits** - Adaptive truncation
2. **C2: Stack Persistence** - Session resumption
3. **C3: Adaptive Nesting Limits** - Flexibility for complex scenarios
4. **D3: Advanced Passive Detection** - More accurate language checks
5. **E2: Query Result Utilization** - Ensures queries add value

**Rationale:** These enhance quality and developer experience but are not critical for core functionality.

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

**Goal:** Prevent catastrophic failures

**Deliverables:**
- A1: Backup rotation implemented
- A2: Multi-stage recovery implemented
- D2: CEPH persistence implemented
- Unit tests for all recovery scenarios

**Success Metrics:**
- 100% recovery rate for single memory corruption
- 80%+ recovery rate for dual memory corruption
- CEPH dropout false positives reduced to <5%

### Phase 2: Enforcement (Weeks 3-4)

**Goal:** Enforce critical requirements

**Deliverables:**
- D1: Protocol validation schema
- E1: Tool usage auditing
- F1: User verification gate
- F2: Metrics baseline tracking
- Integration tests for enforcement

**Success Metrics:**
- 100% protocol validation before emission
- Query deficit violations detected immediately
- No TEST phase progression without verification

### Phase 3: Scaling (Weeks 5-6)

**Goal:** Enable large project support

**Deliverables:**
- A3: Memory monitoring
- B1: Progressive codegraph loading
- B2: Auto-rebuild for empty codegraph
- G1: Proactive context pruning
- G2: Chunked loading
- Performance tests for large projects

**Success Metrics:**
- Support for 10,000+ line memories
- Codegraph load success rate >95%
- Token budget exhaustion reduced by 50%

### Phase 4: Intelligence (Weeks 7-8)

**Goal:** Improve workflow quality

**Deliverables:**
- C1: Guided decomposition
- E2: Query utilization tracking
- D3: Advanced passive detection
- B3: Configurable limits
- Quality metrics dashboard

**Success Metrics:**
- Decomposition suggestions >80% helpful
- Query utilization rate >70%
- Passive language violations reduced by 60%

### Phase 5: Resilience (Weeks 9-10)

**Goal:** Handle interruptions gracefully

**Deliverables:**
- C2: Stack persistence
- C3: Adaptive nesting
- Interrupt/resume testing
- Documentation updates
- Training materials

**Success Metrics:**
- 100% workflow resumption after interruption
- Depth 3 workflows succeed in critical scenarios
- Developer satisfaction >4/5

---

## Metrics and Monitoring

### Key Performance Indicators (KPIs)

1. **Memory Health**
   - Corruption recovery success rate (target: >95%)
   - Backup restoration rate (target: >90%)
   - Oversized memory incidents (target: <1/month)

2. **Workflow Quality**
   - Protocol compliance rate (target: 100%)
   - CEPH dropout incidents (target: <5%)
   - Query requirement violations (target: 0%)

3. **Developer Experience**
   - Average workflow completion time (baseline: establish)
   - Nesting depth limit hits (target: <10/month)
   - Token budget exhaustion (target: <5/month)

4. **System Reliability**
   - Codegraph load success rate (target: >98%)
   - Test verification bypass rate (target: 0%)
   - Critical failures per month (target: 0)

### Monitoring Dashboard

```
11-Phase Workflow Health Dashboard
===================================

Memory System:
  ✓ Project Memory: 3,245 lines (65% of limit)
  ✓ Global Memory: 620 lines (12% of limit)
  ✓ Last Backup: 2 minutes ago
  ✓ Recovery Success Rate: 97.3% (30d)

Codegraph System:
  ✓ Entities: 1,247 (modules:45, classes:312, methods:890)
  ✓ Load Time: 3.2s (avg: 4.1s)
  ✓ Query Success Rate: 99.1% (30d)
  ✗ Empty Codegraph Incidents: 2 (this week)

Workflow Compliance:
  ✓ Protocol Validation: 100% (30d)
  ✓ Query Requirements: 98.7% (30d)
  ✓ User Verification: 100% (30d)
  ✗ CEPH Dropout: 3 incidents (30d)

Token Budget:
  ✓ Current Usage: 327,450 / 1,000,000 (32.7%)
  ✓ Peak Usage (24h): 543,210 (54.3%)
  ✓ Exhaustion Incidents: 0 (30d)

Nesting:
  ✓ Current Depth: 0
  ✓ Depth Limit Hits: 1 (30d)
  ✓ Avg. Nesting per Workflow: 0.7
```

---

## Conclusion

The 11-phase workflow system is well-designed and comprehensive, but edge case analysis reveals opportunities for significant robustness improvements. The proposed enhancements focus on:

1. **Data integrity** - Preventing catastrophic loss through backups and recovery
2. **Enforcement** - Moving from trust-based to verified compliance
3. **Scalability** - Supporting larger projects without degradation
4. **Resilience** - Handling interruptions and edge cases gracefully
5. **Intelligence** - Providing actionable guidance when limits are hit

Implementation of P0 and P1 improvements would elevate the system from good to excellent, providing production-grade reliability suitable for mission-critical workflows.

### Next Steps

1. Review and prioritize recommendations with stakeholders
2. Create implementation tickets for Phase 1
3. Establish baseline metrics before changes
4. Implement P0 improvements immediately
5. Schedule regular edge case testing (quarterly)
6. Iterate based on real-world usage patterns

---

**Document Version:** 1.0  
**Date:** 2025-01-18  
**Author:** Edge Case Analysis Team  
**Status:** Ready for Review
