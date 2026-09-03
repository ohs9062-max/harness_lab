"""V3 MODE A/B/C protocol tests using fake agents and temporary Git repos."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from demo.orchestrator.coordinator import Coordinator
from demo.orchestrator.engine import OrchestratorEngine
from demo.orchestrator.models import RuntimeState, StageConfig, TaskPlan


class TestV3Modes(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="harness_modes_")
        self.root = Path(self.temp_dir)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Harness Test"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "harness@example.invalid"], cwd=self.root, check=True)
        (self.root / ".gitignore").write_text(".harness/\n", encoding="utf-8")
        (self.root / "README.md").write_text("# fixture\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=self.root, check=True)
        self.base = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True,
            text=True, check=True,
        ).stdout.strip()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def engine(self, **kwargs):
        return OrchestratorEngine(
            str(self.root), use_fake_agents=True, auto_discover_checks=False,
            fake_options={"review_verdict": "PASS"}, **kwargs,
        )

    def plan_a(self, task_id):
        return Coordinator(str(self.root)).create_deterministic_plan(task_id, "로그인 기능 구현", mode="A")

    def plan_c(self, task_id):
        return Coordinator(str(self.root)).create_deterministic_plan(task_id, "코드 구현", mode="C")

    def run_a(self, task_id):
        engine = self.engine()
        state = engine.run_plan(self.plan_a(task_id), "A로 로그인 기능 만들어", dry_run=False, execute=True)
        return engine, state

    def test_a1_two_required_workers_checkpoint_review_response_compare_then_wait(self):
        _, state = self.run_a("TASK-A1")
        self.assertEqual(state.status, "WAITING_USER")
        self.assertEqual(set(state.worktrees), {"codex", "gemini"})
        self.assertEqual(set(state.checkpoints), {"codex", "gemini"})
        self.assertEqual(state.worker_status, {"codex": "DONE", "gemini": "DONE"})
        self.assertEqual(len(state.cross_reviews), 2)
        self.assertEqual(len(state.responses), 2)
        self.assertTrue((self.root / state.compare_path).is_file())
        self.assertEqual(self.base, subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True,
            text=True, check=True,
        ).stdout.strip())
        self.assertEqual(state.merge_status, "PENDING")

    def test_a2_required_gemini_failure_blocks_before_cross_review(self):
        engine = self.engine()
        original = engine._get_adapter

        def adapter(agent):
            value = original(agent)
            if agent == "gemini":
                value.force_success = False
            return value

        engine._get_adapter = adapter
        state = engine.run_plan(self.plan_a("TASK-A2"), "A로 구현", dry_run=False, execute=True)
        self.assertEqual(state.status, "BLOCKED")
        self.assertFalse(state.cross_reviews)
        self.assertIsNone(state.compare_path)
        self.assertEqual(state.merge_status, "PENDING")

    def test_a3_select_gemini_runs_codex_integration(self):
        engine, waiting = self.run_a("TASK-A3")
        state = engine.resume_mode_a(waiting.task_id, "SELECT_GEMINI")
        self.assertEqual(state.status, "DONE")
        self.assertEqual(state.user_selection, "SELECT_GEMINI")
        self.assertEqual(state.merge_status, "INTEGRATED")
        prompts = [item for item in engine._adapters["codex"].prompts if item["stage"] == "CODEX_MERGE"]
        self.assertEqual(len(prompts), 1)
        self.assertIn(waiting.checkpoints["gemini"], prompts[0]["prompt"])
        self.assertEqual(prompts[0]["cwd"], str(self.root))

    def test_a4_select_hybrid_passes_both_results_and_compare(self):
        engine, waiting = self.run_a("TASK-A4")
        state = engine.resume_mode_a(waiting.task_id, "SELECT_HYBRID", "둘의 장점 결합")
        self.assertEqual(state.status, "DONE")
        prompt = [item for item in engine._adapters["codex"].prompts if item["stage"] == "CODEX_MERGE"][0]["prompt"]
        self.assertIn(waiting.checkpoints["codex"], prompt)
        self.assertIn(waiting.checkpoints["gemini"], prompt)
        self.assertIn("둘의 장점 결합", prompt)
        self.assertIn("COMPARE REPORT", prompt)

    def test_a5_selection_before_waiting_cannot_integrate(self):
        engine = self.engine()
        state = RuntimeState(
            task_id="TASK-A5", status="RUNNING", user_request="x", mode="A",
            base_commit=self.base, plan=self.plan_a("TASK-A5").to_dict(),
        )
        engine.state_mgr.save_state(state)
        blocked = engine.resume_mode_a("TASK-A5", "SELECT_CODEX")
        self.assertEqual(blocked.status, "BLOCKED")
        self.assertNotIn("codex", engine._adapters)

    def test_a6_independent_prompts_do_not_contain_sibling_results(self):
        engine, state = self.run_a("TASK-A6")
        codex_prompt = [item for item in engine._adapters["codex"].prompts if item["stage"] == "INDEPENDENT_WORK"][0]["prompt"]
        gemini_prompt = [item for item in engine._adapters["gemini"].prompts if item["stage"] == "INDEPENDENT_WORK"][0]["prompt"]
        self.assertNotIn(state.worker_branches["gemini"], codex_prompt)
        self.assertNotIn(state.worker_branches["codex"], gemini_prompt)
        self.assertNotIn(state.checkpoints["gemini"], codex_prompt)
        self.assertNotIn(state.checkpoints["codex"], gemini_prompt)

    def _interrupted_c_state(self, engine, task_id, expected_status=None):
        plan = self.plan_c(task_id)
        ref = engine.worktree_mgr.create(task_id, "pipeline", self.base)
        state = RuntimeState(
            task_id=task_id, status="RUNNING", user_request="코드 이어서 구현",
            base_commit=self.base, base_branch="master", mode="C", plan=plan.to_dict(),
            current_stage="IMPLEMENT", stage_statuses={"DESIGN": "DONE", "IMPLEMENT": "RUNNING"},
            active_worktree=ref.path, active_branch=ref.branch,
            worktrees={"pipeline": ref.path}, worker_branches={"pipeline": ref.branch},
            relay={"current_agent": "codex", "git_status": expected_status or []},
        )
        engine.state_mgr.save_state(state)
        return state

    def test_b1_gemini_continues_same_branch_and_worktree_from_remaining_stage(self):
        engine = self.engine()
        interrupted = self._interrupted_c_state(engine, "TASK-B1")
        state = engine.resume_relay("TASK-B1", "gemini")
        self.assertEqual(state.status, "DONE")
        self.assertEqual(state.mode, "B")
        self.assertEqual(state.active_worktree, interrupted.active_worktree)
        self.assertEqual(state.active_branch, interrupted.active_branch)
        implement = [item for item in engine._adapters["gemini"].prompts if item["stage"] == "IMPLEMENT"]
        self.assertEqual(implement[0]["cwd"], interrupted.active_worktree)
        self.assertTrue(any(item["stage"] == "REVIEW" for item in engine._adapters["claude"].prompts))

    def test_b2_actual_git_state_wins_and_mismatch_is_recorded(self):
        engine = self.engine()
        interrupted = self._interrupted_c_state(engine, "TASK-B2", expected_status=[])
        (Path(interrupted.active_worktree) / "surprise.txt").write_text("actual Git state\n")
        state = engine.resume_relay("TASK-B2", "gemini")
        self.assertEqual(state.status, "DONE")
        self.assertTrue(state.git_discrepancies)
        self.assertIn("surprise.txt", state.changed_files)

    def test_c1_all_agents_use_one_pipeline_worktree_not_base(self):
        engine = self.engine()
        state = engine.run_plan(self.plan_c("TASK-C1"), "C로 해", dry_run=False, execute=True)
        self.assertEqual(state.status, "DONE")
        self.assertNotEqual(Path(state.active_worktree), self.root)
        self.assertEqual(state.worker_branches["pipeline"], "task/TASK-C1/pipeline")
        for agent in ("claude", "codex", "gemini"):
            self.assertTrue(engine._adapters[agent].prompts)
            self.assertTrue(all(item["cwd"] == state.active_worktree for item in engine._adapters[agent].prompts))

    def test_c2_fix_check_fresh_review_stays_in_pipeline_worktree(self):
        engine = OrchestratorEngine(
            str(self.root), use_fake_agents=True, auto_discover_checks=False,
            fake_options={"review_sequence": ["FIX_REQUIRED", "PASS"]},
        )
        state = engine.run_plan(self.plan_c("TASK-C2"), "C로 수정", dry_run=False, execute=True)
        self.assertEqual(state.status, "DONE")
        self.assertEqual(state.review_cycles, 1)
        fix = [item for item in engine._adapters["codex"].prompts if item["stage"] == "FIX"]
        review = [item for item in engine._adapters["gemini"].prompts if item["stage"] == "REVIEW"]
        self.assertEqual(len(fix), 1)
        self.assertEqual(len(review), 2)
        self.assertTrue(all(item["cwd"] == state.active_worktree for item in fix + review))

    def test_git1_non_git_blocks_before_any_worker(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = OrchestratorEngine(directory, use_fake_agents=True, auto_discover_checks=False)
            plan = Coordinator(directory).create_deterministic_plan("TASK-GIT1", "구현", mode="C")
            state = engine.run_plan(plan, "구현", dry_run=False, execute=True)
            self.assertEqual(state.status, "BLOCKED")
            self.assertIn("Git Preflight", state.blocker)
            self.assertFalse(engine._adapters)

    def test_git2_base_worker_write_is_blocked(self):
        engine = self.engine()
        plan = self.plan_c("TASK-GIT2")
        state = RuntimeState(
            task_id="TASK-GIT2", status="RUNNING", user_request="x",
            base_commit=self.base, mode="C", plan=plan.to_dict(),
        )
        success = engine._run_agent_stage(state, plan, plan.stages[1], lambda _: None)
        self.assertFalse(success)
        self.assertEqual(state.status, "BLOCKED")
        self.assertFalse(engine._adapters)


if __name__ == "__main__":
    unittest.main()
