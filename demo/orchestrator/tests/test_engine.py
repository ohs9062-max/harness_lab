"""Comprehensive workflow and gate tests for OrchestratorEngine."""

import shutil
import tempfile
import unittest
from pathlib import Path
from demo.orchestrator.engine import OrchestratorEngine
from demo.orchestrator.models import (
    ExecutionMode,
    StageConfig,
    StageStatus,
    TaskPlan,
    TaskType,
)


class TestEngineWorkflows(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="harness_test_")
        self.repo_root = Path(self.temp_dir)

        # Initialize mock git environment
        import subprocess
        subprocess.run(["git", "init"], cwd=str(self.repo_root), capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "TestUser"], cwd=str(self.repo_root), check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(self.repo_root), check=True)

        gitignore = self.repo_root / ".gitignore"
        gitignore.write_text(".harness/\n", encoding="utf-8")

        readme = self.repo_root / "README.md"
        readme.write_text("# Test Repo", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=str(self.repo_root), check=True)
        subprocess.run(["git", "commit", "-m", "initial commit"], cwd=str(self.repo_root), check=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_sample_plan(self, task_id="TASK-TEST-001") -> TaskPlan:
        stages = [
            StageConfig(name="RESEARCH", execution="PARALLEL", agents=["claude", "codex", "gemini"], required=True),
            StageConfig(name="COMPARE", execution="PIPELINE", agents=["gemini"], required=True),
            StageConfig(name="VERIFY", execution="PIPELINE", agents=["codex"], required=True),
            StageConfig(name="SYNTHESIZE", execution="PIPELINE", agents=["claude"], required=True),
            StageConfig(name="REVIEW", execution="PIPELINE", agents=["gemini"], required=True),
            StageConfig(name="FINAL", execution="PIPELINE", agents=["user"], required=True),
        ]
        return TaskPlan(
            task_id=task_id,
            task_type=TaskType.RESEARCH.value,
            execution=ExecutionMode.PARALLEL.value,
            output_artifact="strategy.md",
            stages=stages,
        )

    def test_dry_run_simulation(self):
        plan = self._create_sample_plan("TASK-DRYRUN-001")
        engine = OrchestratorEngine(repo_root=str(self.repo_root), use_fake_agents=True)

        state = engine.run_plan(plan=plan, user_request="Naver blog SEO research", dry_run=True, execute=False)
        self.assertEqual(state.status, "DRY_RUN_COMPLETED")
        self.assertEqual(state.stage_statuses.get("RESEARCH"), StageStatus.DONE.value)
        self.assertEqual(state.stage_statuses.get("REVIEW"), StageStatus.DONE.value)

    def test_full_workflow_success_with_fake_agents(self):
        plan = self._create_sample_plan("TASK-EXEC-SUCCESS-001")
        engine = OrchestratorEngine(
            repo_root=str(self.repo_root),
            use_fake_agents=True,
            fake_options={"force_success": True, "review_verdict": "PASS"},
        )

        state = engine.run_plan(plan=plan, user_request="Full workflow test", dry_run=False, execute=True)
        self.assertEqual(state.status, "DONE")
        self.assertEqual(state.stage_statuses["RESEARCH"], StageStatus.DONE.value)
        self.assertEqual(state.stage_statuses["COMPARE"], StageStatus.DONE.value)
        self.assertEqual(state.stage_statuses["SYNTHESIZE"], StageStatus.DONE.value)
        self.assertEqual(state.stage_statuses["REVIEW"], StageStatus.DONE.value)
        self.assertEqual(state.stage_statuses["FINAL"], StageStatus.DONE.value)

    def test_required_agent_gate_blocking(self):
        """If one required agent in PARALLEL fails, subsequent stages must be blocked."""
        plan = self._create_sample_plan("TASK-GATE-FAIL-001")

        # Engine with failing agents
        engine = OrchestratorEngine(
            repo_root=str(self.repo_root),
            use_fake_agents=True,
            fake_options={"force_success": False, "exit_code": 1},
        )

        state = engine.run_plan(plan=plan, user_request="Test failure gate", dry_run=False, execute=True)
        self.assertEqual(state.status, "BLOCKED")
        self.assertEqual(state.stage_statuses["RESEARCH"], StageStatus.BLOCKED.value)
        # COMPARE and SYNTHESIZE should not be in state.stage_statuses or should remain PENDING
        self.assertNotIn("COMPARE", state.stage_statuses)
        self.assertNotIn("SYNTHESIZE", state.stage_statuses)

    def test_parallel_worktree_isolation(self):
        """Verify that parallel agents are assigned distinct isolated worktree paths."""
        plan = self._create_sample_plan("TASK-ISOLATION-001")
        engine = OrchestratorEngine(repo_root=str(self.repo_root), use_fake_agents=True)

        state = engine.run_plan(plan=plan, user_request="Worktree test", dry_run=False, execute=True)
        wt_claude = state.worktrees.get("RESEARCH_claude")
        wt_codex = state.worktrees.get("RESEARCH_codex")
        wt_gemini = state.worktrees.get("RESEARCH_gemini")

        self.assertIsNotNone(wt_claude)
        self.assertIsNotNone(wt_codex)
        self.assertIsNotNone(wt_gemini)
        # Ensure all 3 paths are distinct
        self.assertNotEqual(wt_claude, wt_codex)
        self.assertNotEqual(wt_codex, wt_gemini)
        self.assertNotEqual(wt_claude, wt_gemini)

    def test_max_review_cycles_blocking(self):
        """Verify that continuous FIX_REQUIRED verdict halts after max_review_cycles."""
        plan = self._create_sample_plan("TASK-REVIEW-LOOP-001")
        engine = OrchestratorEngine(
            repo_root=str(self.repo_root),
            use_fake_agents=True,
            fake_options={"force_success": True, "review_verdict": "FIX_REQUIRED"},
            max_review_cycles=2,
        )

        state = engine.run_plan(plan=plan, user_request="Test review loop", dry_run=False, execute=True)
        self.assertEqual(state.status, "BLOCKED")
        self.assertGreaterEqual(state.review_cycles, 2)


if __name__ == "__main__":
    unittest.main()
