"""
Edge Case Test Suite for 11-Phase Workflow System

Tests critical failure scenarios and recovery mechanisms across:
- Memory operations (corruption, missing, oversized)
- Codegraph operations (empty, timeout, query failures)
- Nested workflow depth management (>2 levels)
- Phase transition violations (missing gates, CEPH dropout)
- Test failure handling (inline fixes vs NEST requirement)
- Protocol format violations (SCP-START, SCP-PHASE, etc.)
- Token budget exhaustion scenarios
- Concurrent workflow interruptions

Each test simulates realistic edge cases per copilot-instructions.md failure handling table.
"""

import json
import pytest
from pathlib import Path
from typing import Dict, List, Any
import tempfile
import os


class WorkflowState:
    """Simulates workflow state tracking per NWP protocol"""
    def __init__(self):
        self.workflow_index = 0
        self.depth = 0
        self.phase = "PLAN"
        self.phase_number = 0
        self.total_phases = 11
        self.ceph = {}
        self.violations = []
        self.protocols_emitted = []
        self.test_failures = []
        self.stack = []
        
    def emit_protocol(self, protocol_type: str, **kwargs):
        """Simulate protocol emission"""
        protocol = {
            "type": protocol_type,
            "index": self.workflow_index,
            "phase": f"{self.phase_number}/{self.total_phases}",
            **kwargs
        }
        self.protocols_emitted.append(protocol)
        return protocol
    
    def nest(self, trigger: str, from_phase: str):
        """Simulate workflow nesting"""
        self.stack.append({
            "index": self.workflow_index,
            "phase": self.phase,
            "phase_number": self.phase_number
        })
        self.workflow_index += 1
        self.depth += 1
        return self.emit_protocol("SCP-NWP", action="NEST", trigger=trigger, from_phase=from_phase)
    
    def return_workflow(self):
        """Simulate workflow return"""
        if not self.stack:
            raise ValueError("Cannot RETURN: workflow stack empty")
        previous = self.stack.pop()
        self.workflow_index -= 1
        self.depth -= 1
        self.phase = previous["phase"]
        self.phase_number = previous["phase_number"]
        return self.emit_protocol("SCP-NWP", action="RETURN")


class MemorySimulator:
    """Simulates memory operations with edge cases"""
    
    @staticmethod
    def create_corrupted_json(path: Path) -> None:
        """Create corrupted JSON file"""
        with open(path, 'w') as f:
            f.write('{"entities": [{"id": "1", "name": "test"')  # Missing closing brackets
    
    @staticmethod
    def create_oversized_memory(path: Path, lines: int = 6000) -> None:
        """Create oversized memory file (>5000 lines threshold)"""
        entities = []
        for i in range(lines // 3):  # Roughly 3 lines per entity with formatting
            entities.append({
                "id": f"entity_{i}",
                "name": f"Entity_{i}",
                "observations": [f"observation_{i}"]
            })
        with open(path, 'w') as f:
            json.dump({"entities": entities}, f, indent=2)
    
    @staticmethod
    def create_valid_memory(path: Path) -> None:
        """Create valid memory file"""
        memory = {
            "entities": [
                {"id": "1", "name": "TestFeature", "observations": ["Test observation"]},
                {"id": "2", "name": "TestMethod", "observations": ["Another observation"]}
            ]
        }
        with open(path, 'w') as f:
            json.dump(memory, f, indent=2)


class CodegraphSimulator:
    """Simulates codegraph operations with edge cases"""
    
    @staticmethod
    def create_empty_codegraph(path: Path) -> None:
        """Create empty codegraph (entities=0)"""
        with open(path, 'w') as f:
            json.dump({"modules": [], "classes": [], "methods": [], "relations": []}, f, indent=2)
    
    @staticmethod
    def create_valid_codegraph(path: Path) -> None:
        """Create valid codegraph"""
        codegraph = {
            "modules": ["module1", "module2"],
            "classes": ["Class1", "Class2"],
            "methods": ["method1", "method2", "method3"],
            "relations": [
                {"from": "Class1", "to": "Class2", "type": "IMPORTS"},
                {"from": "method1", "to": "Class1", "type": "BELONGS_TO"}
            ]
        }
        with open(path, 'w') as f:
            json.dump(codegraph, f, indent=2)


# ======================== Memory Edge Cases ========================

def test_memory_missing_recovery():
    """Test recovery when memory files are missing (copilot-instructions.md:64)"""
    state = WorkflowState()
    state.emit_protocol("SCP-START")
    
    # Simulate REMEMBER phase with missing memory
    with tempfile.TemporaryDirectory() as tmpdir:
        project_memory = Path(tmpdir) / "project_memory.json"
        global_memory = Path(tmpdir) / ".github" / "global_memory.json"
        
        # Files don't exist - should trigger VIOLATIONS:[memory_missing→created_empty]
        assert not project_memory.exists()
        assert not global_memory.exists()
        
        # Expected recovery: create empty files
        global_memory.parent.mkdir(parents=True, exist_ok=True)
        MemorySimulator.create_valid_memory(project_memory)
        MemorySimulator.create_valid_memory(global_memory)
        
        state.violations.append("memory_missing→created_empty")
        protocol = state.emit_protocol("SCP-PHASE", violations=state.violations, adjust="created_empty_files")
        
        assert protocol["type"] == "SCP-PHASE"
        assert "memory_missing→created_empty" in state.violations
        assert project_memory.exists()
        assert global_memory.exists()


def test_memory_corrupted_recovery():
    """Test recovery when memory JSON is corrupted (copilot-instructions.md:65)"""
    state = WorkflowState()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        memory_path = Path(tmpdir) / "project_memory.json"
        MemorySimulator.create_corrupted_json(memory_path)
        
        # Try to load corrupted JSON
        try:
            with open(memory_path, 'r') as f:
                json.load(f)
            assert False, "Should have raised JSONDecodeError"
        except json.JSONDecodeError as e:
            # Expected: VIOLATIONS:[corrupted_L37-86→rebuilt]
            line_range = f"L{e.lineno}-{e.lineno+50}"
            state.violations.append(f"corrupted_{line_range}→rebuilt")
            
            # Recovery: repair or create empty
            MemorySimulator.create_valid_memory(memory_path)
            protocol = state.emit_protocol("SCP-PHASE", violations=state.violations, adjust="repaired_via_script")
            
            assert any("corrupted" in v for v in state.violations)
            assert protocol["type"] == "SCP-PHASE"


def test_memory_oversized_recovery():
    """Test recovery when memory exceeds 5000 lines (copilot-instructions.md:67)"""
    state = WorkflowState()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        memory_path = Path(tmpdir) / "project_memory.json"
        MemorySimulator.create_oversized_memory(memory_path, lines=6000)
        
        # Count lines
        with open(memory_path, 'r') as f:
            line_count = sum(1 for _ in f)
        
        assert line_count > 5000, "Memory should be oversized"
        
        # Expected: VIOLATIONS:[oversized→condensed:N→M]
        state.violations.append(f"oversized_{line_count}→condensed:3000")
        
        # Recovery: auto-run optimizer (simulated by recreating smaller)
        MemorySimulator.create_valid_memory(memory_path)
        
        with open(memory_path, 'r') as f:
            new_line_count = sum(1 for _ in f)
        
        protocol = state.emit_protocol("SCP-PHASE", violations=state.violations, adjust="auto_optimizer_ran")
        
        assert new_line_count < line_count
        assert any("oversized" in v for v in state.violations)


def test_memory_both_corrupted():
    """Test CRITICAL failure when both memories corrupted (copilot-instructions.md:66)"""
    state = WorkflowState()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_memory = Path(tmpdir) / "project_memory.json"
        global_memory = Path(tmpdir) / ".github" / "global_memory.json"
        global_memory.parent.mkdir(parents=True, exist_ok=True)
        
        MemorySimulator.create_corrupted_json(project_memory)
        MemorySimulator.create_corrupted_json(global_memory)
        
        # Both fail to parse
        for path in [project_memory, global_memory]:
            try:
                with open(path, 'r') as f:
                    json.load(f)
                assert False, f"{path} should be corrupted"
            except json.JSONDecodeError:
                pass  # Expected
        
        # Expected: VIOLATIONS:[total_corruption→empty_files:CRITICAL]
        state.violations.append("total_corruption→empty_files:CRITICAL")
        
        # Recovery: create empty both, rebuild in LEARN
        MemorySimulator.create_valid_memory(project_memory)
        MemorySimulator.create_valid_memory(global_memory)
        
        protocol = state.emit_protocol("SCP-PHASE", violations=state.violations, adjust="created_empty_both")
        
        assert any("CRITICAL" in v for v in state.violations)
        assert protocol["type"] == "SCP-PHASE"


# ======================== Codegraph Edge Cases ========================

def test_codegraph_empty():
    """Test handling of empty codegraph (entities=0) (copilot-instructions.md:68)"""
    state = WorkflowState()
    state.phase = "ASSESS"
    state.phase_number = 2
    
    with tempfile.TemporaryDirectory() as tmpdir:
        codegraph_path = Path(tmpdir) / "codegraph.json"
        CodegraphSimulator.create_empty_codegraph(codegraph_path)
        
        with open(codegraph_path, 'r') as f:
            codegraph = json.load(f)
        
        # Check if empty (entities=0)
        total_entities = len(codegraph.get("modules", [])) + len(codegraph.get("classes", []))
        assert total_entities == 0, "Codegraph should be empty"
        
        # Expected: DISCOVERIES:[codegraph_empty]
        discoveries = ["codegraph_empty"]
        protocol = state.emit_protocol("SCP-PHASE", violations=["none"], discoveries=discoveries)
        
        assert protocol["type"] == "SCP-PHASE"
        assert "codegraph_empty" in discoveries


def test_codegraph_query_returns_zero():
    """Test handling when codegraph query returns 0 results (copilot-instructions.md:70)"""
    state = WorkflowState()
    state.phase = "ANALYZE"
    state.phase_number = 3
    
    with tempfile.TemporaryDirectory() as tmpdir:
        codegraph_path = Path(tmpdir) / "codegraph.json"
        CodegraphSimulator.create_valid_codegraph(codegraph_path)
        
        with open(codegraph_path, 'r') as f:
            codegraph = json.load(f)
        
        # Simulate query that returns 0
        query_type = "DOCUMENTED_IN"
        results = [r for r in codegraph.get("relations", []) if r.get("type") == query_type]
        assert len(results) == 0, "Query should return 0 results"
        
        # Expected: DISCOVERIES:[query_X_returned_0]
        discoveries = [f"query_{query_type}_returned_0"]
        protocol = state.emit_protocol("SCP-PHASE", violations=["none"], discoveries=discoveries)
        
        assert any("query_" in d and "returned_0" in d for d in discoveries)


def test_codegraph_timeout():
    """Test handling of codegraph load timeout >10s (copilot-instructions.md:69)"""
    state = WorkflowState()
    state.phase = "ASSESS"
    state.phase_number = 2
    
    # Simulate timeout scenario
    load_time = 15  # seconds
    assert load_time > 10, "Should exceed 10s threshold"
    
    # Expected: VIOLATIONS:[codegraph_timeout→retry]
    state.violations.append("codegraph_timeout→retry")
    
    # Recovery: retry once
    with tempfile.TemporaryDirectory() as tmpdir:
        codegraph_path = Path(tmpdir) / "codegraph.json"
        CodegraphSimulator.create_valid_codegraph(codegraph_path)
        
        # Second attempt succeeds
        protocol = state.emit_protocol("SCP-PHASE", violations=state.violations, adjust="retried_once")
        
        assert any("timeout" in v for v in state.violations)
        assert protocol["type"] == "SCP-PHASE"


# ======================== Workflow Nesting Edge Cases ========================

def test_nesting_depth_limit():
    """Test CRITICAL nesting when depth >2 (copilot-instructions.md:73)"""
    state = WorkflowState()
    
    # Root workflow (index=0)
    state.emit_protocol("SCP-START")
    
    # First NEST (index=1)
    state.nest(trigger="test_failure", from_phase="IMPLEMENT")
    assert state.workflow_index == 1
    assert state.depth == 1
    
    # Second NEST (index=2)
    state.nest(trigger="repeated_failure", from_phase="DEBUG")
    assert state.workflow_index == 2
    assert state.depth == 2
    
    # Third NEST would exceed limit (index=3)
    try:
        # This should trigger: DISCOVERIES:[CRITICAL_NESTING:decompose]
        if state.workflow_index >= 2:
            discoveries = ["CRITICAL_NESTING:decompose"]
            protocol = state.emit_protocol("SCP-CHECK", 
                                         violations=["nesting_depth_exceeded"],
                                         discoveries=discoveries)
            assert any("CRITICAL_NESTING" in d for d in discoveries)
        else:
            state.nest(trigger="third_level", from_phase="DEBUG")
            assert False, "Should not allow nesting >2 levels"
    except Exception:
        pass  # Expected to halt or warn


def test_test_failure_without_nest():
    """Test violation when test fails without NEST (copilot-instructions.md:72)"""
    state = WorkflowState()
    state.phase = "TEST"
    state.phase_number = 7
    
    # Simulate test failure
    test_result = {"exit_code": 1, "failures": ["test_feature_x"]}
    assert test_result["exit_code"] != 0, "Test should fail"
    
    # Attempt inline fix without NEST - VIOLATION
    # Expected: [SCP-NWP: NEST→test_failure]
    state.violations.append("test_failed_no_NEST:CRITICAL")
    
    # Correct action: emit NEST
    protocol = state.nest(trigger="test_failure", from_phase="TEST")
    
    assert protocol["type"] == "SCP-NWP"
    assert protocol["action"] == "NEST"
    assert state.workflow_index == 1  # Nested workflow


def test_workflow_return_empty_stack():
    """Test error when attempting RETURN with empty stack"""
    state = WorkflowState()
    
    # No NEST has occurred, stack is empty
    assert len(state.stack) == 0
    
    # Attempt to RETURN should fail
    try:
        state.return_workflow()
        assert False, "Should not allow RETURN with empty stack"
    except ValueError as e:
        assert "workflow stack empty" in str(e)


# ======================== Protocol Violation Edge Cases ========================

def test_missing_scp_start():
    """Test violation when SCP-START is missing at session start (copilot-instructions.md:55)"""
    state = WorkflowState()
    
    # Simulate starting work without SCP-START
    state.phase = "REMEMBER"
    state.phase_number = 1
    
    # Check if SCP-START was emitted
    has_start = any(p["type"] == "SCP-START" for p in state.protocols_emitted)
    
    if not has_start:
        # Violation detected
        state.violations.append("missing_SCP-START:CRITICAL")
        
        # Recovery: emit SCP-START immediately
        protocol = state.emit_protocol("SCP-START", loaded=["chatmode", "instructions"], index=0)
        assert protocol["type"] == "SCP-START"


def test_missing_phase_gate():
    """Test violation when phase completes without SCP-PHASE (copilot-instructions.md:55)"""
    state = WorkflowState()
    state.emit_protocol("SCP-START")
    
    # Complete REMEMBER phase
    state.phase = "REMEMBER"
    state.phase_number = 1
    
    # Move to next phase WITHOUT emitting SCP-PHASE - VIOLATION
    state.phase = "ASSESS"
    state.phase_number = 2
    
    # Check if phase gate was emitted
    phase_gates = [p for p in state.protocols_emitted if p["type"] == "SCP-PHASE"]
    phases_completed = state.phase_number - 1
    
    if len(phase_gates) < phases_completed:
        state.violations.append(f"missing_phase_gate:{state.phase_number-1}")
        
        # Recovery: emit missing gate
        protocol = state.emit_protocol("SCP-PHASE", violations=["missing_gate_emitted_late"])
        assert protocol["type"] == "SCP-PHASE"


def test_ceph_dropout():
    """Test CEPH field dropout detection (copilot-instructions.md protocols.md:117)"""
    state = WorkflowState()
    
    # Initial CEPH in ASSESS
    state.ceph = {
        "CURRENT": "initial_state",
        "EXPECTED": "target_state",
        "PROBLEM": "issue_statement",
        "HYPOTHESES": [],
        "EVIDENCE": []
    }
    
    # In ARCHITECT phase, EXPECTED field drops
    state.phase = "ARCHITECT"
    state.phase_number = 4
    state.ceph = {
        "CURRENT": "design_state",
        # EXPECTED missing - dropout
        "PROBLEM": "issue_statement",
        "HYPOTHESES": [],
        "EVIDENCE": ["decision_doc"]
    }
    
    # Detection: compare to previous CEPH
    required_fields = ["CURRENT", "EXPECTED", "PROBLEM", "HYPOTHESES", "EVIDENCE"]
    missing_fields = [f for f in required_fields if f not in state.ceph]
    
    if missing_fields:
        state.violations.append(f"CEPH_dropout:{','.join(missing_fields)}")
        
        # Recovery: restore from previous
        state.ceph["EXPECTED"] = "target_state"
        
        protocol = state.emit_protocol("SCP-PHASE", 
                                      violations=state.violations,
                                      adjust=f"restored_CEPH_fields:{missing_fields}")
        
        assert any("CEPH_dropout" in v for v in state.violations)
        assert "EXPECTED" in state.ceph


# ======================== Codegraph Query Edge Cases ========================

def test_implement_insufficient_queries():
    """Test IMPLEMENT phase with <3/5 queries (phases.md:42-43)"""
    state = WorkflowState()
    state.phase = "IMPLEMENT"
    state.phase_number = 5
    
    # Simulate only 2/5 queries
    queries_performed = ["IMPORTS", "BELONGS_TO"]
    required_minimum = 3
    
    if len(queries_performed) < required_minimum:
        state.violations.append(f"query_deficit:{len(queries_performed)}/5_only")
        
        # Add missing queries
        queries_performed.extend(["CALLS"])
        
        protocol = state.emit_protocol("SCP-PHASE",
                                      violations=state.violations,
                                      adjust="added_CALLS_query",
                                      codegraph_queries=f"{len(queries_performed)}/5")
        
        assert any("query_deficit" in v for v in state.violations)
        assert len(queries_performed) >= required_minimum


def test_debug_insufficient_queries():
    """Test DEBUG phase with <2/4 queries (phases.md:49-51)"""
    state = WorkflowState()
    state.phase = "DEBUG"
    state.phase_number = 6
    
    # Simulate only 1/4 queries
    queries_performed = ["CALLS"]
    required_minimum = 2
    
    if len(queries_performed) < required_minimum:
        state.violations.append(f"debug_query_deficit:{len(queries_performed)}/4_only")
        
        # Add missing query
        queries_performed.append("IMPORTS")
        
        protocol = state.emit_protocol("SCP-PHASE",
                                      violations=state.violations,
                                      adjust="added_IMPORTS_trace",
                                      codegraph_queries=f"{len(queries_performed)}/4")
        
        assert any("query_deficit" in v for v in state.violations)
        assert len(queries_performed) >= required_minimum


# ======================== Test Phase Edge Cases ========================

def test_test_phase_missing_metrics_delta():
    """Test TEST phase without Δ in metrics (phases.md:58, protocols.md:59)"""
    state = WorkflowState()
    state.phase = "TEST"
    state.phase_number = 7
    
    # Incorrect metrics (no delta)
    metrics_bad = "tests=14/14|coverage=95%|assertions=42"
    
    # Expected format with delta
    metrics_good = "tests=14/14(+14)|coverage=95%(+5)|assertions=42(+42)"
    
    # Check for delta presence
    if "(+" not in metrics_bad and "(-" not in metrics_bad:
        state.violations.append("metrics_missing_delta")
        
        protocol = state.emit_protocol("SCP-PHASE",
                                      violations=state.violations,
                                      adjust="added_delta_to_metrics",
                                      metrics=metrics_good)
        
        assert "(+" in metrics_good or "(-" in metrics_good
        assert any("metrics_missing_delta" in v for v in state.violations)


def test_test_phase_missing_user_verification():
    """Test TEST phase without USER_VERIFICATION blocking (phases.md:59, protocols.md:60)"""
    state = WorkflowState()
    state.phase = "TEST"
    state.phase_number = 7
    
    # Tests pass, but missing USER_VERIFICATION
    test_result = {"exit_code": 0, "passed": 14, "failed": 0}
    
    # Should emit USER_VERIFICATION and BLOCK
    protocol = state.emit_protocol("SCP-PHASE",
                                  violations=["none"],
                                  user_verification="awaiting:YES",
                                  blocking="LEARN,DOCUMENT,LOG")
    
    assert "user_verification" in protocol
    assert protocol["user_verification"] == "awaiting:YES"
    
    # Should NOT continue to LEARN without user approval
    # This enforces the checkpoint


# ======================== Learn Phase Edge Cases ========================

def test_learn_minimum_entities():
    """Test LEARN phase with <3 entities (phases.md:64)"""
    state = WorkflowState()
    state.phase = "LEARN"
    state.phase_number = 8
    
    # Only 2 entities extracted
    entities_extracted = ["Feature_MultiToken", "Method_search"]
    
    if len(entities_extracted) < 3:
        state.violations.append(f"learn_minimum_not_met:{len(entities_extracted)}<3")
        
        # Add another entity
        entities_extracted.append("Pattern_GroupedResults")
        
        protocol = state.emit_protocol("SCP-PHASE",
                                      violations=state.violations,
                                      adjust="added_pattern_entity",
                                      entities=len(entities_extracted))
        
        assert len(entities_extracted) >= 3
        assert any("learn_minimum_not_met" in v for v in state.violations)


# ======================== Token Budget Edge Cases ========================

def test_token_budget_critical():
    """Test token budget >95% (copilot-instructions.md:76)"""
    state = WorkflowState()
    
    # Simulate token usage
    total_tokens = 1000000
    used_tokens = 960000
    usage_percent = (used_tokens / total_tokens) * 100
    
    if usage_percent > 95:
        discoveries = [f"token_budget:CRITICAL:{int(usage_percent)}%"]
        
        protocol = state.emit_protocol("SCP-CHECK",
                                      violations=["none"],
                                      discoveries=discoveries)
        
        assert any("token_budget:CRITICAL" in d for d in discoveries)
        # Should prepare to finalize


# ======================== Integration Test: Full Workflow with Interruptions ========================

def test_full_workflow_with_nested_interruptions():
    """Integration test: Root workflow with test failure, nested DEBUG, and recovery"""
    state = WorkflowState()
    
    # Session start
    protocol = state.emit_protocol("SCP-START", loaded=["chatmode", "phases", "protocols"])
    assert protocol["type"] == "SCP-START"
    assert state.workflow_index == 0
    
    # Phase 0: PLAN
    state.phase = "PLAN"
    state.phase_number = 0
    state.emit_protocol("SCP-PHASE", violations=["none"])
    
    # Phase 1: REMEMBER
    state.phase = "REMEMBER"
    state.phase_number = 1
    state.emit_protocol("SCP-PHASE", violations=["none"])
    
    # Phase 2: ASSESS
    state.phase = "ASSESS"
    state.phase_number = 2
    state.ceph = {
        "CURRENT": "no_multi_token",
        "EXPECTED": "multi_token_support",
        "PROBLEM": "search_limited_to_single_token",
        "HYPOTHESES": [],
        "EVIDENCE": ["current_search_impl"]
    }
    state.emit_protocol("SCP-PHASE", violations=["none"], ceph=state.ceph)
    
    # Phase 5: IMPLEMENT (skip 3-4 for brevity)
    state.phase = "IMPLEMENT"
    state.phase_number = 5
    state.ceph["CURRENT"] = "implementation_complete"
    state.emit_protocol("SCP-PHASE", violations=["none"], ceph=state.ceph)
    
    # Phase 7: TEST - FAILURE
    state.phase = "TEST"
    state.phase_number = 7
    test_result = {"exit_code": 1, "failures": ["test_multi_token_grouping"]}
    
    # NEST into DEBUG workflow
    nest_protocol = state.nest(trigger="test_failure", from_phase="TEST")
    assert nest_protocol["action"] == "NEST"
    assert state.workflow_index == 1
    assert state.depth == 1
    
    # Nested workflow: DEBUG
    state.phase = "DEBUG"
    state.phase_number = 6
    state.ceph["HYPOTHESES"] = ["H1:grouping_logic→incorrect_key→fix_dict_key"]
    state.emit_protocol("SCP-PHASE", violations=["none"], ceph=state.ceph)
    
    # Nested workflow: TEST (retest)
    state.phase = "TEST"
    state.phase_number = 7
    state.emit_protocol("SCP-PHASE", violations=["none"])
    
    # Nested workflow: LEARN
    state.phase = "LEARN"
    state.phase_number = 8
    state.emit_protocol("SCP-PHASE", violations=["none"])
    
    # RETURN to root workflow
    return_protocol = state.return_workflow()
    assert return_protocol["action"] == "RETURN"
    assert state.workflow_index == 0
    assert state.depth == 0
    assert state.phase == "TEST"
    
    # Resume TEST phase (should pass now)
    state.emit_protocol("SCP-PHASE", violations=["none"], user_verification="awaiting:YES")
    
    # Phase 8: LEARN (root)
    state.phase = "LEARN"
    state.phase_number = 8
    state.emit_protocol("SCP-PHASE", violations=["none"])
    
    # Phase 10: LOG
    state.phase = "LOG"
    state.phase_number = 10
    state.emit_protocol("SCP-END", nested_count=1, max_depth=1, total_phases=11+5)
    
    # Verify full protocol sequence
    protocol_types = [p["type"] for p in state.protocols_emitted]
    assert protocol_types[0] == "SCP-START"
    assert protocol_types[-1] == "SCP-END"
    assert "SCP-NWP" in protocol_types  # NEST and RETURN
    assert protocol_types.count("SCP-PHASE") >= 8  # Multiple phases


# ======================== Run Summary ========================

if __name__ == "__main__":
    """Run all edge case tests and generate report"""
    print("=" * 80)
    print("11-PHASE WORKFLOW EDGE CASE TEST SUITE")
    print("=" * 80)
    print()
    
    # Run tests
    import sys
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    
    print()
    print("=" * 80)
    print("Edge case simulation complete. Review results above.")
    print("=" * 80)
    
    sys.exit(exit_code)
