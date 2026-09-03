"""End-to-end engine tests with isolated Git repositories and fake agents."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from demo.orchestrator.engine import OrchestratorEngine
from demo.orchestrator.models import AccessMode, RuntimeState, StageConfig, TaskPlan


class TestEngineWorkflows(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="harness_test_")
        self.repo_root = Path(self.temp_dir)
        subprocess.run(["git", "init", "-q"], cwd=self.repo_root, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo_root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo_root, check=True)
        (self.repo_root / ".gitignore").write_text(".harness/\n", encoding="utf-8")
        (self.repo_root / "README.md").write_text("# fixture\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.repo_root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=self.repo_root, check=True)
        self.initial_head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True,
        ).stdout.strip()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def plan(self, task_id: str = "TASK-TEST-001") -> TaskPlan:
        return TaskPlan(
            task_id=task_id,
            task_type="DEVELOPMENT",
            mode="C",
            output_artifact="",
            fix_agent="codex",
            stages=[
                StageConfig("DESIGN", "PIPELINE", ["claude"], "planner", "READ_ONLY"),
                StageConfig("IMPLEMENT", "PIPELINE", ["codex"], "implementer", "WRITE"),
                StageConfig("TEST", "PIPELINE", ["codex"], "tester", "READ_ONLY"),
                StageConfig("CHECK", "PIPELINE", ["system"], "checker", "SYSTEM"),
                StageConfig("REVIEW", "PIPELINE", ["gemini"], "reviewer", "READ_ONLY"),
                StageConfig("FINAL", "PIPELINE", ["system"], "finalizer", "SYSTEM"),
            ],
        )

    def engine(self, **kwargs) -> OrchestratorEngine:
        return OrchestratorEngine(
            str(self.repo_root), use_fake_agents=True, auto_discover_checks=False, **kwargs,
        )

    def test_dry_run_starts_no_workers(self):
        state = self.engine().run_plan(self.plan("TASK-DRY"), "implement", dry_run=True, execute=False)
        self.assertEqual(state.status, "DRY_RUN_COMPLETED")
        self.assertFalse(state.agent_results)

    def test_successful_pipeline_hands_outputs_to_next_stages(self):
        state = self.engine(fake_options={"review_verdict": "PASS"}).run_plan(
            self.plan("TASK-SUCCESS"), "implement", dry_run=False, execute=True,
        )
        self.assertEqual(state.status, "DONE")
        self.assertEqual(state.stage_statuses["CHECK"], "WAIVED")
        self.assertTrue(any(item["stage"] == "DESIGN" for item in state.handoffs))
        handoff = json.loads((self.repo_root / ".harness/runs/TASK-SUCCESS/handoff.json").read_text())
        self.assertGreaterEqual(len(handoff["outputs"]), 3)
        self.assertEqual(subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.repo_root, capture_output=True, text=True, check=True,
        ).stdout.strip(), self.initial_head, "base branch must remain unchanged")
        self.assertNotEqual(state.checkpoints["pipeline"], self.initial_head)
        self.assertNotEqual(Path(state.active_worktree), self.repo_root)

    def test_required_agent_failure_blocks_pipeline(self):
        state = self.engine(fake_options={"force_success": False}).run_plan(
            self.plan("TASK-FAIL"), "implement", dry_run=False, execute=True,
        )
        self.assertEqual(state.status, "BLOCKED")
        self.assertEqual(state.stage_statuses["DESIGN"], "BLOCKED")
        self.assertNotIn("IMPLEMENT", state.stage_statuses)

    def test_pipeline_uses_fallback_after_primary_failure(self):
        plan = self.plan("TASK-FALLBACK")
        plan.stages[0].fallback_agents = ["gemini"]
        engine = self.engine(fake_options={"review_verdict": "PASS"})
        original = engine._get_adapter

        def adapter(agent):
            value = original(agent)
            if agent == "claude":
                value.force_success = False
            return value

        engine._get_adapter = adapter
        state = engine.run_plan(plan, "implement", dry_run=False, execute=True)
        self.assertEqual(state.status, "DONE")
        design = [item for item in state.handoffs if item["stage"] == "DESIGN"]
        self.assertEqual([(item["agent"], item["success"]) for item in design], [("claude", False), ("gemini", True)])

    def test_parallel_stage_allows_explicit_quorum(self):
        plan = self.plan("TASK-QUORUM")
        plan.stages.insert(0, StageConfig(
            "ANALYZE", "PARALLEL", ["claude", "gemini"], "analyst", "READ_ONLY", min_success=1,
        ))
        plan.stages[1].agents = ["gemini"]
        engine = self.engine(fake_options={"review_verdict": "PASS"})
        original = engine._get_adapter

        def adapter(agent):
            value = original(agent)
            if agent == "claude":
                value.force_success = False
            return value

        engine._get_adapter = adapter
        state = engine.run_plan(plan, "analyze and implement", dry_run=False, execute=True)
        self.assertEqual(state.status, "DONE")

    def test_missing_review_verdict_blocks(self):
        state = self.engine(fake_options={"review_verdict": None}).run_plan(
            self.plan("TASK-NO-VERDICT"), "implement", dry_run=False, execute=True,
        )
        self.assertEqual(state.status, "BLOCKED")
        self.assertIn("verdict", state.blocker)

    def test_review_fallback_ignores_failed_primary_verdict(self):
        plan = self.plan("TASK-REVIEW-FALLBACK")
        plan.stages[4].fallback_agents = ["fake"]
        engine = self.engine(fake_options={"review_verdict": "PASS"})
        original = engine._get_adapter

        def adapter(agent):
            value = original(agent)
            if agent == "gemini":
                value.force_success = False
            return value

        engine._get_adapter = adapter
        state = engine.run_plan(plan, "implement", dry_run=False, execute=True)
        self.assertEqual(state.status, "DONE")

    def test_fix_then_fresh_review_passes(self):
        state = self.engine(fake_options={"review_sequence": ["FIX_REQUIRED", "PASS"]}).run_plan(
            self.plan("TASK-FIX"), "implement", dry_run=False, execute=True,
        )
        self.assertEqual(state.status, "DONE")
        self.assertEqual(state.review_cycles, 1)
        self.assertTrue((Path(state.active_worktree) / "fake-fix.txt").exists())

    def test_fix_uses_the_actual_fallback_implementer(self):
        plan = self.plan("TASK-ACTUAL-FIXER")
        plan.stages[1].fallback_agents = ["claude"]
        engine = self.engine(fake_options={"review_sequence": ["FIX_REQUIRED", "PASS"]})
        original = engine._get_adapter

        def adapter(agent):
            value = original(agent)
            if agent == "codex":
                value.force_success = False
            return value

        engine._get_adapter = adapter
        state = engine.run_plan(plan, "implement", dry_run=False, execute=True)
        self.assertEqual(state.status, "DONE")
        self.assertEqual((Path(state.active_worktree) / "fake-fix.txt").read_text(), "claude completed FIX\n")

    def test_repeated_fix_required_hits_cycle_limit(self):
        state = self.engine(
            fake_options={"review_verdict": "FIX_REQUIRED"}, max_review_cycles=1,
        ).run_plan(self.plan("TASK-LIMIT"), "implement", dry_run=False, execute=True)
        self.assertEqual(state.status, "BLOCKED")
        self.assertIn("maximum fix cycles", state.blocker)

    def test_failed_deterministic_check_stops_before_review(self):
        state = self.engine(
            fake_options={"review_verdict": "PASS"},
            check_commands=[[sys.executable, "-c", "raise SystemExit(7)"]],
        ).run_plan(self.plan("TASK-CHECK-FAIL"), "implement", dry_run=False, execute=True)
        self.assertEqual(state.status, "BLOCKED")
        self.assertEqual(state.stage_statuses["CHECK"], "BLOCKED")
        self.assertFalse(any(item["stage"] == "REVIEW" for item in state.handoffs))

    def test_parallel_read_outputs_are_isolated(self):
        plan = self.plan("TASK-PARALLEL")
        plan.stages.insert(0, StageConfig(
            "ANALYZE", "PARALLEL", ["claude", "gemini"], "analyst", AccessMode.READ_ONLY.value,
        ))
        state = self.engine(fake_options={"review_verdict": "PASS"}).run_plan(
            plan, "analyze and implement", dry_run=False, execute=True,
        )
        design_outputs = [item["output_file"] for item in state.handoffs if item["stage"] == "ANALYZE"]
        self.assertEqual(len(design_outputs), 2)
        self.assertEqual(len(set(design_outputs)), 2)
        self.assertTrue(all((self.repo_root / path).is_file() for path in design_outputs))

    def test_handoff_excerpt_prioritizes_output_over_long_stderr(self):
        path = self.repo_root / ".harness/runs/TASK-EXCERPT/outputs/001-DESIGN/claude.md"
        path.parent.mkdir(parents=True)
        path.write_text("# DESIGN\n\n## Output\nIMPORTANT DESIGN\n\n## Stderr\n" + "x" * 20_000)
        state = RuntimeState(
            task_id="TASK-EXCERPT", status="RUNNING", user_request="x",
            handoffs=[{"stage": "DESIGN", "agent": "claude", "success": True, "output_file": str(path.relative_to(self.repo_root))}],
        )
        excerpt = self.engine()._handoff_excerpt(state)
        self.assertIn("IMPORTANT DESIGN", excerpt)
        self.assertLess(len(excerpt), 13_000)


if __name__ == "__main__":
    unittest.main()
