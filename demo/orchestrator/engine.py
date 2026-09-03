"""Automatic role pipeline with real handoffs, checks, review, and fix loops."""

from __future__ import annotations

import concurrent.futures
import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

from demo.orchestrator.adapters import get_adapter
from demo.orchestrator.checks import CheckRunner
from demo.orchestrator.git_state import GitInspector
from demo.orchestrator.models import (
    AccessMode, AgentExecutionResult, ExecutionMode, ReviewVerdict,
    RuntimeState, StageConfig, StageStatus, TaskPlan,
)
from demo.orchestrator.prompt_builder import build_stage_prompt
from demo.orchestrator.state import StateManager
from demo.orchestrator.worktree import WorktreeManager


class OrchestratorEngine:
    def __init__(
        self,
        repo_root: str,
        use_fake_agents: bool = False,
        fake_options: Optional[Dict[str, Any]] = None,
        max_review_cycles: int = 2,
        agent_timeout_sec: int = 600,
        check_timeout_sec: int = 300,
        check_commands: Optional[Sequence[Sequence[str]]] = None,
        auto_discover_checks: bool = True,
    ):
        self.base_repo = Path(repo_root).resolve()
        self.repo_root = self.base_repo
        self.use_fake = use_fake_agents
        self.fake_options = fake_options or {}
        self.max_review_cycles = max_review_cycles
        self.agent_timeout_sec = agent_timeout_sec
        self.auto_discover_checks = auto_discover_checks
        self.explicit_checks = [list(command) for command in (check_commands or [])]
        self.check_timeout_sec = check_timeout_sec
        self.base_git = GitInspector(str(self.base_repo))
        self.git = self.base_git
        self.state_mgr = StateManager(str(self.base_repo))
        self.worktree_mgr = WorktreeManager(str(self.base_repo))
        self.check_runner = CheckRunner(str(self.repo_root), timeout_sec=check_timeout_sec)
        self._adapters: Dict[str, Any] = {}
        self._stage_sequence = 0

    def run_plan(
        self,
        plan: TaskPlan,
        user_request: str,
        dry_run: bool = True,
        execute: bool = False,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> RuntimeState:
        plan.validate()

        def log(message: str) -> None:
            if progress_callback:
                progress_callback(message)
            else:
                print(f"[Harness] {message}")

        try:
            preflight = self.base_git.preflight()
        except Exception as error:
            state = RuntimeState(
                task_id=plan.task_id, status="BLOCKED", user_request=user_request,
                plan=plan.to_dict(), mode=plan.mode, blocker=f"Git Preflight failed: {error}",
            )
            self.state_mgr.save_state(state)
            self.state_mgr.append_event(plan.task_id, "run.blocked", stage="GIT_PREFLIGHT", reason=state.blocker)
            log(state.blocker)
            return state

        state = RuntimeState(
            task_id=plan.task_id,
            status="RUNNING" if execute else "DRY_RUN",
            user_request=user_request,
            base_commit=preflight.head,
            initial_dirty=preflight.dirty,
            plan=plan.to_dict(),
            mode=plan.mode,
            base_branch=preflight.branch,
            stage_statuses={"DEFINE": StageStatus.DONE.value, "GIT_PREFLIGHT": StageStatus.DONE.value},
        )
        self.state_mgr.save_state(state)
        self.state_mgr.append_event(
            plan.task_id, "run.started", base_commit=preflight.head,
            branch=preflight.branch, initial_dirty=preflight.dirty,
            worktrees=preflight.worktrees, mode=plan.mode,
        )
        log(f"{plan.task_id} started on {preflight.branch}@{preflight.head[:8]}")

        if dry_run and not execute:
            for stage in plan.stages:
                state.stage_statuses[stage.name] = StageStatus.PENDING.value
            state.status = "DRY_RUN_COMPLETED"
            self.state_mgr.write_handoff(state.task_id, state)
            self.state_mgr.save_state(state)
            log("Dry-run completed; no agent or check process was started.")
            return state

        if plan.mode == "A":
            return self._run_mode_a(state, plan, log)
        if plan.mode == "B":
            return self._block_and_finish(state, "DEFINE", "MODE B requires resume_task()", log)
        return self._run_mode_c(state, plan, log)

    def _activate_workspace(self, path: str) -> None:
        self.repo_root = Path(path).resolve()
        self.git = GitInspector(str(self.repo_root))
        self.check_runner = CheckRunner(str(self.repo_root), timeout_sec=self.check_timeout_sec)

    def _run_mode_c(
        self, state: RuntimeState, plan: TaskPlan, log: Callable[[str], None],
    ) -> RuntimeState:
        state.current_stage = "WORKTREE_SETUP"
        state.stage_statuses["WORKTREE_SETUP"] = StageStatus.RUNNING.value
        try:
            worktree = self.worktree_mgr.create(plan.task_id, "pipeline", state.base_commit)
        except Exception as error:
            return self._block_and_finish(state, "WORKTREE_SETUP", str(error), log)
        state.worktrees["pipeline"] = worktree.path
        state.worker_branches["pipeline"] = worktree.branch
        state.active_worktree = worktree.path
        state.active_branch = worktree.branch
        state.stage_statuses["WORKTREE_SETUP"] = StageStatus.DONE.value
        self.state_mgr.append_event(
            state.task_id, "worktree.created", label="pipeline", path=worktree.path,
            branch=worktree.branch, base_commit=state.base_commit,
        )
        self._activate_workspace(worktree.path)
        initial_snapshot = self.git.snapshot()
        self._run_pipeline_stages(state, plan, plan.stages, log)
        if state.status != "BLOCKED":
            try:
                state.checkpoints["pipeline"] = self.worktree_mgr.checkpoint(
                    worktree.path, state.task_id, "pipeline",
                )
                self.state_mgr.append_event(
                    state.task_id, "checkpoint.created", label="pipeline",
                    commit=state.checkpoints["pipeline"],
                )
                state.changed_files = self.worktree_mgr.changed_files(
                    state.base_commit, state.checkpoints["pipeline"], worktree.path,
                )
                state.stage_statuses["CHECKPOINT"] = StageStatus.DONE.value
                state.status = "DONE"
            except Exception as error:
                self._block(state, "CHECKPOINT", str(error), log)
        self._finish_state(state, initial_snapshot)
        self.state_mgr.append_event(state.task_id, "run.finished", status=state.status, blocker=state.blocker)
        log(f"Finished with status {state.status}")
        return state

    def _run_pipeline_stages(
        self, state: RuntimeState, plan: TaskPlan, stages: Sequence[StageConfig],
        log: Callable[[str], None],
    ) -> None:
        for stage in stages:
            if state.mode == "B" and stage.name == "REVIEW":
                stage = self._safe_relay_review_stage(state, stage)
            state.current_stage = stage.name
            state.stage_statuses[stage.name] = StageStatus.RUNNING.value
            self.state_mgr.save_state(state)
            self.state_mgr.append_event(plan.task_id, "stage.started", stage=stage.name, agents=stage.agents)
            log(f"Stage {stage.name}: {', '.join(stage.agents)}")

            if stage.name in {"CHECK", "TEST"}:
                if not self._run_checks(state, stage, log):
                    break
                continue
            if stage.name == "FINAL":
                if not self._final_gate(state, plan, log):
                    break
                continue
            if stage.name == "REVIEW":
                if not self._run_review_loop(state, plan, stage, log):
                    break
                continue
            if not self._run_agent_stage(state, plan, stage, log):
                break

            if state.status == "BLOCKED":
                break

    def _safe_relay_review_stage(self, state: RuntimeState, stage: StageConfig) -> StageConfig:
        writers = {
            str(result["agent"])
            for results in state.agent_results.values()
            for result in results
            if result.get("success") and result.get("stage") in {"IMPLEMENT", "SYNTHESIZE", "FIX"}
        }
        candidates = [agent for agent in stage.agents + stage.fallback_agents if agent not in writers]
        if not candidates:
            candidates = [agent for agent in ("gemini", "claude", "codex") if agent not in writers]
        if not candidates:
            return stage
        if candidates[0] != stage.agents[0]:
            self.state_mgr.append_event(
                state.task_id, "reviewer.reassigned", original=stage.agents,
                selected=candidates[0], reason="relay writer cannot self-review",
            )
        return StageConfig(
            name=stage.name, execution="PIPELINE", agents=[candidates[0]],
            role=stage.role, access=stage.access, required=stage.required,
        )

    def _block_and_finish(
        self, state: RuntimeState, stage: str, reason: str, log: Callable[[str], None],
    ) -> RuntimeState:
        self._block(state, stage, reason, log)
        self.state_mgr.write_handoff(state.task_id, state)
        self.state_mgr.save_state(state)
        self.state_mgr.append_event(state.task_id, "run.finished", status=state.status, blocker=state.blocker)
        return state

    def _run_mode_a(
        self, state: RuntimeState, plan: TaskPlan, log: Callable[[str], None],
    ) -> RuntimeState:
        workers = ("codex", "gemini")
        state.current_stage = "WORKTREE_SETUP"
        state.stage_statuses["WORKTREE_SETUP"] = StageStatus.RUNNING.value
        try:
            for agent in workers:
                ref = self.worktree_mgr.create(plan.task_id, agent, state.base_commit)
                state.worktrees[agent] = ref.path
                state.worker_branches[agent] = ref.branch
                state.worker_status[agent] = StageStatus.PENDING.value
                self.state_mgr.append_event(
                    state.task_id, "worktree.created", label=agent, path=ref.path,
                    branch=ref.branch, base_commit=state.base_commit,
                )
        except Exception as error:
            return self._block_and_finish(state, "WORKTREE_SETUP", str(error), log)
        state.stage_statuses["WORKTREE_SETUP"] = StageStatus.DONE.value

        for agent in workers:
            if not self._run_independent_worker(state, plan, agent, log):
                return self._block_and_finish(
                    state, "WORKER_GATE", f"required MODE A worker failed: {agent}", log,
                )

        state.stage_statuses["INDEPENDENT_WORK"] = StageStatus.DONE.value
        state.stage_statuses["TEST"] = StageStatus.DONE.value
        state.stage_statuses["CHECKPOINT"] = StageStatus.DONE.value
        state.stage_statuses["WORKER_GATE"] = StageStatus.DONE.value
        if not self._run_cross_reviews(state, plan, log):
            return self._block_and_finish(state, "CROSS_REVIEW", state.blocker or "cross review failed", log)
        if not self._run_responses(state, plan, log):
            return self._block_and_finish(state, "RESPONSE", state.blocker or "response failed", log)

        compare = self._build_compare_report(state)
        compare_path = self.state_mgr.write_runtime_markdown(state.task_id, "compare.md", compare)
        state.compare_path = str(compare_path.relative_to(self.base_repo))
        state.stage_statuses["COMPARE"] = StageStatus.DONE.value
        state.current_stage = "WAITING_USER"
        state.status = "WAITING_USER"
        self.state_mgr.append_event(
            state.task_id, "selection.required", options=[
                "SELECT_CODEX", "SELECT_GEMINI", "SELECT_HYBRID", "REWORK", "CANCEL",
            ], compare_path=state.compare_path,
        )
        self.state_mgr.write_handoff(state.task_id, state)
        self.state_mgr.save_state(state)
        log("MODE A comparison complete; waiting for user selection.")
        return state

    def _run_independent_worker(
        self, state: RuntimeState, plan: TaskPlan, agent: str, log: Callable[[str], None],
    ) -> bool:
        worktree = state.worktrees[agent]
        self._activate_workspace(worktree)
        state.current_stage = "INDEPENDENT_WORK"
        state.worker_status[agent] = StageStatus.RUNNING.value
        before = self.git.snapshot()
        prompt = build_stage_prompt(
            task_id=state.task_id, user_request=state.user_request,
            stage_name="IMPLEMENT", agent_name=agent, execution_mode="PIPELINE",
            base_commit=state.base_commit, worktree_path=worktree,
            output_artifact=plan.output_artifact, role="independent MODE A worker",
            access=AccessMode.WRITE.value,
            extra_context={
                "handoff_path": "not available during independent work",
                "output_paths": [], "checks_summary": "No sibling test results are available.",
                "handoff_content": (
                    "Independence gate: do not inspect sibling branches, worktrees, outputs, diffs, or tests."
                ),
            },
        )
        result = self._get_adapter(agent).run(
            prompt=prompt, cwd=worktree, stage="INDEPENDENT_WORK",
            timeout_sec=self.agent_timeout_sec, access=AccessMode.WRITE.value,
        )
        delta = self._snapshot_delta(before, self.git.snapshot())
        result.changed_files = delta
        self._record_result(state, "INDEPENDENT_WORK", result)
        if not result.success or not delta:
            state.worker_status[agent] = StageStatus.FAILED.value
            state.blocker = result.error_message or "worker produced no repository change"
            return False

        checks = self._run_worker_checks(worktree)
        state.worker_tests[agent] = checks
        if any(not item["success"] for item in checks):
            state.worker_status[agent] = StageStatus.FAILED.value
            state.blocker = f"required worker check failed: {agent}"
            return False
        try:
            checkpoint = self.worktree_mgr.checkpoint(worktree, state.task_id, agent)
        except Exception as error:
            state.worker_status[agent] = StageStatus.FAILED.value
            state.blocker = f"checkpoint failed for {agent}: {error}"
            return False
        state.checkpoints[agent] = checkpoint
        state.worker_status[agent] = StageStatus.DONE.value
        self.state_mgr.append_event(
            state.task_id, "worker.finished", agent=agent, checkpoint=checkpoint,
            changed_files=delta, checks=checks,
        )
        self.state_mgr.save_state(state)
        log(f"MODE A worker {agent} completed at {checkpoint[:8]}")
        return True

    def _run_worker_checks(self, worktree: str) -> List[Dict[str, Any]]:
        runner = CheckRunner(worktree, timeout_sec=self.check_timeout_sec)
        commands = list(self.explicit_checks)
        if self.auto_discover_checks:
            commands.extend(runner.discover())
        unique: List[List[str]] = []
        for command in commands:
            if command not in unique:
                unique.append(command)
        return [result.to_dict() for result in runner.run_all(unique)]

    def _record_result(self, state: RuntimeState, stage: str, result: AgentExecutionResult) -> str:
        key = self._next_key(stage)
        self.state_mgr.write_result(state.task_id, key, result)
        state.agent_results[key] = [result.to_dict()]
        state.handoffs.append({
            "stage": stage, "stage_key": key, "agent": result.agent,
            "success": result.success, "output_file": result.output_file,
            "review_verdict": result.review_verdict,
        })
        self.state_mgr.write_handoff(state.task_id, state)
        return key

    def _run_cross_reviews(
        self, state: RuntimeState, plan: TaskPlan, log: Callable[[str], None],
    ) -> bool:
        state.current_stage = "CROSS_REVIEW"
        state.stage_statuses["CROSS_REVIEW"] = StageStatus.RUNNING.value
        pairs = (("gemini", "codex"), ("codex", "gemini"))
        for reviewer, target in pairs:
            diff = self.worktree_mgr.diff(
                state.base_commit, state.checkpoints[target], state.worktrees[target],
            )[:80_000]
            changed = self.worktree_mgr.changed_files(
                state.base_commit, state.checkpoints[target], state.worktrees[target],
            )
            prompt = (
                f"MODE A CROSS_REVIEW. Review {target}'s completed independent result read-only.\n"
                f"TASK-ID: {state.task_id}\nUSER GOAL: {state.user_request}\n"
                f"BASE-COMMIT: {state.base_commit}\nTARGET-BRANCH: {state.worker_branches[target]}\n"
                f"TARGET-CHECKPOINT: {state.checkpoints[target]}\nCHANGED-FILES: {changed}\n"
                f"TEST-RESULTS: {json.dumps(state.worker_tests[target], ensure_ascii=False)}\n"
                "Report concrete findings with severity, file/location, evidence, and required change. "
                "Do not edit, commit, merge, or inspect the other worker result.\n\nDIFF:\n" + diff
            )
            result = self._get_adapter(reviewer).run(
                prompt=prompt, cwd=state.worktrees[target], stage="CROSS_REVIEW",
                timeout_sec=self.agent_timeout_sec, access=AccessMode.READ_ONLY.value,
            )
            self._record_result(state, "CROSS_REVIEW", result)
            key = f"{reviewer}_reviews_{target}"
            state.cross_reviews[key] = {
                "reviewer": reviewer, "target": target, "success": result.success,
                "output_file": result.output_file,
            }
            if not result.success:
                state.blocker = f"cross review failed: {key}"
                return False
        state.stage_statuses["CROSS_REVIEW"] = StageStatus.DONE.value
        log("MODE A cross review completed.")
        return True

    def _run_responses(
        self, state: RuntimeState, plan: TaskPlan, log: Callable[[str], None],
    ) -> bool:
        state.current_stage = "RESPONSE"
        state.stage_statuses["RESPONSE"] = StageStatus.RUNNING.value
        for worker, reviewer in (("codex", "gemini"), ("gemini", "codex")):
            review = state.cross_reviews[f"{reviewer}_reviews_{worker}"]
            review_text = self._read_runtime_output(review["output_file"], 30_000)
            prompt = (
                f"MODE A RESPONSE ROUND 1/1. Respond to findings about your {worker} result.\n"
                f"TASK-ID: {state.task_id}\nCHECKPOINT: {state.checkpoints[worker]}\n"
                "Do not edit files. For every finding use exactly one disposition: "
                "ACCEPT, REJECT, PARTIAL, or NEEDS_TEST. There is no second automatic round.\n\n"
                f"FINDINGS:\n{review_text}"
            )
            result = self._get_adapter(worker).run(
                prompt=prompt, cwd=state.worktrees[worker], stage="RESPONSE",
                timeout_sec=self.agent_timeout_sec, access=AccessMode.READ_ONLY.value,
            )
            self._record_result(state, "RESPONSE", result)
            dispositions = re.findall(r"\b(?:ACCEPT|REJECT|PARTIAL|NEEDS_TEST)\b", result.stdout)
            state.responses[worker] = {
                "round": 1, "success": result.success, "dispositions": dispositions,
                "output_file": result.output_file,
            }
            if not result.success or not dispositions:
                state.blocker = f"invalid MODE A response from {worker}"
                return False
        state.stage_statuses["RESPONSE"] = StageStatus.DONE.value
        log("MODE A response round 1/1 completed.")
        return True

    def _read_runtime_output(self, relative_path: str, max_chars: int) -> str:
        path = (self.base_repo / relative_path).resolve()
        path.relative_to(self.base_repo)
        return path.read_text(encoding="utf-8")[:max_chars]

    def _build_compare_report(self, state: RuntimeState) -> str:
        sections = [
            f"# MODE A Compare — {state.task_id}", "", "## Base", "",
            f"- branch: {state.base_branch}", f"- commit: {state.base_commit}", "",
        ]
        for worker in ("codex", "gemini"):
            changed = self.worktree_mgr.changed_files(
                state.base_commit, state.checkpoints[worker], state.worktrees[worker],
            )
            sections.extend([
                f"## {worker.title()} implementation", "",
                f"- branch: {state.worker_branches[worker]}",
                f"- checkpoint: {state.checkpoints[worker]}",
                f"- changed files: {', '.join(changed) or 'none'}",
                f"- tests: {json.dumps(state.worker_tests[worker], ensure_ascii=False)}", "",
                "### Summary / design / strengths / weaknesses", "",
                self._latest_output_for_agent(state, worker, "INDEPENDENT_WORK"), "",
                "### Cross Review findings", "",
                self._read_runtime_output(
                    state.cross_reviews[
                        f"{'gemini' if worker == 'codex' else 'codex'}_reviews_{worker}"
                    ]["output_file"], 30_000,
                ), "", "### Response", "",
                self._read_runtime_output(state.responses[worker]["output_file"], 20_000), "",
            ])
        sections.extend([
            "## Agreement and remaining differences", "",
            "Use the implementations, cross-review findings, and responses above as the evidence set.", "",
            "## Recommendation", "",
            "The Runner does not select automatically. The user must choose one of the options below.", "",
            "## Selection impact", "",
            "- SELECT_CODEX: Codex integrates the Codex checkpoint onto the current base.",
            "- SELECT_GEMINI: Codex integrates the Gemini checkpoint onto the current base.",
            "- SELECT_HYBRID: Codex integrates both checkpoints following the user's hybrid instruction.",
            "- REWORK: no integration; return to user-directed rework.",
            "- CANCEL: no integration; terminate the task.", "",
        ])
        return "\n".join(sections)

    def _latest_output_for_agent(self, state: RuntimeState, agent: str, stage: str) -> str:
        for item in reversed(state.handoffs):
            if item.get("agent") == agent and item.get("stage") == stage and item.get("output_file"):
                return self._read_runtime_output(item["output_file"], 30_000)
        return "No output recorded."

    def resume_mode_a(
        self, task_id: str, selection: str, user_instruction: str = "",
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> RuntimeState:
        def log(message: str) -> None:
            (progress_callback or (lambda value: print(f"[Harness] {value}")))(message)

        state = self.state_mgr.load_state(task_id)
        if state is None:
            raise ValueError(f"Unknown TASK-ID: {task_id}")
        selection = selection.upper()
        allowed = {"SELECT_CODEX", "SELECT_GEMINI", "SELECT_HYBRID", "REWORK", "CANCEL"}
        if state.mode != "A" or state.status != "WAITING_USER":
            return self._block_and_finish(
                state, "USER_SELECT", "MODE A selection requires WAITING_USER state", log,
            )
        if selection not in allowed:
            return self._block_and_finish(state, "USER_SELECT", f"invalid selection: {selection}", log)
        state.user_selection = selection
        state.stage_statuses["USER_SELECT"] = StageStatus.DONE.value
        self.state_mgr.write_selection(task_id, {
            "task_id": task_id, "selection": selection, "instruction": user_instruction,
        })
        self.state_mgr.append_event(task_id, "selection.recorded", selection=selection)
        if selection == "CANCEL":
            state.status = "CANCELLED"
            state.merge_status = "NOT_RUN"
            self.state_mgr.save_state(state)
            return state
        if selection == "REWORK":
            state.status = "WAITING_REWORK"
            state.merge_status = "NOT_RUN"
            self.state_mgr.save_state(state)
            return state

        preflight = self.base_git.preflight()
        if preflight.head != state.base_commit or preflight.dirty:
            return self._block_and_finish(
                state, "CODEX_MERGE",
                "base changed since MODE A started; integration requires a fresh user decision",
                log,
            )
        required_workers = {"codex", "gemini"}
        if set(state.checkpoints) < required_workers:
            return self._block_and_finish(state, "CODEX_MERGE", "both worker checkpoints are required", log)

        selected = ["codex"] if selection == "SELECT_CODEX" else ["gemini"]
        if selection == "SELECT_HYBRID":
            selected = ["codex", "gemini"]
        compare_text = self._read_runtime_output(state.compare_path or "", 60_000)
        selected_details = "\n".join(
            f"- {worker}: branch={state.worker_branches[worker]} checkpoint={state.checkpoints[worker]} "
            f"worktree={state.worktrees[worker]}"
            for worker in selected
        )
        prompt = f"""MODE A CODEX_MERGE after explicit user selection.
TASK-ID: {task_id}
USER-SELECTION: {selection}
USER-INSTRUCTION: {user_instruction or 'none'}
BASE-BRANCH: {state.base_branch}
BASE-CURRENT-HEAD: {preflight.head}
BASE-DIRTY: {preflight.dirty}
SELECTED RESULTS:
{selected_details}

Integrate exactly the selected result into the base working tree. You are the integration executor, not the decision maker.
For SELECT_HYBRID, use both checkpoints and the instruction/compare evidence; do not invent a third direction.
Do not commit, push, reset, or delete branches. Report changed files and checks.

COMPARE REPORT:
{compare_text}
"""
        self._activate_workspace(str(self.base_repo))
        before = self.git.snapshot()
        result = self._get_adapter("codex").run(
            prompt=prompt, cwd=str(self.base_repo), stage="CODEX_MERGE",
            timeout_sec=self.agent_timeout_sec, access=AccessMode.WRITE.value,
        )
        result.changed_files = self._snapshot_delta(before, self.git.snapshot())
        self._record_result(state, "CODEX_MERGE", result)
        if not result.success or not result.changed_files:
            return self._block_and_finish(
                state, "CODEX_MERGE", result.error_message or "Codex integration made no change", log,
            )
        state.merge_status = "INTEGRATED"
        state.stage_statuses["CODEX_MERGE"] = StageStatus.DONE.value
        state.current_stage = "CHECK"
        state.status = "RUNNING"
        check_stage = StageConfig(
            "CHECK", "PIPELINE", ["system"], "post-selection verifier", "SYSTEM",
        )
        if not self._run_checks(state, check_stage, log):
            return self._block_and_finish(state, "CHECK", state.blocker or "integration checks failed", log)
        plan = TaskPlan.from_dict(state.plan or {})
        if not self._final_gate(state, plan, log):
            return self._block_and_finish(state, "FINAL", state.blocker or "final gate failed", log)
        state.status = "DONE"
        state.current_stage = "FINAL"
        state.changed_files = self._snapshot_delta(before, self.git.snapshot())
        self.state_mgr.write_handoff(task_id, state)
        self.state_mgr.save_state(state)
        self.state_mgr.append_event(task_id, "run.finished", status="DONE", selection=selection)
        return state

    def resume_relay(
        self, task_id: str, next_agent: str,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> RuntimeState:
        def log(message: str) -> None:
            (progress_callback or (lambda value: print(f"[Harness] {value}")))(message)

        state = self.state_mgr.load_state(task_id)
        if state is None:
            raise ValueError(f"Unknown TASK-ID: {task_id}")
        if next_agent not in {"claude", "codex", "gemini"}:
            raise ValueError(f"Invalid relay agent: {next_agent}")
        if not state.active_worktree:
            return self._block_and_finish(state, "GIT_VERIFY", "state has no existing worktree", log)
        worktree = Path(state.active_worktree).resolve()
        if worktree == self.base_repo:
            return self._block_and_finish(state, "GIT_VERIFY", "MODE B cannot write in base worktree", log)
        try:
            inspector = GitInspector(str(worktree))
            evidence = inspector.relay_evidence()
        except Exception as error:
            return self._block_and_finish(state, "GIT_VERIFY", str(error), log)
        discrepancies: List[str] = []
        if state.active_branch and evidence["branch"] != state.active_branch:
            discrepancies.append(f"recorded branch {state.active_branch} != Git branch {evidence['branch']}")
        expected_status = state.relay.get("git_status")
        if expected_status is not None and expected_status != evidence["status"]:
            discrepancies.append("recorded Git status differs from actual Git status; actual Git state used")
        state.git_discrepancies.extend(discrepancies)
        previous_agent = state.relay.get("current_agent") or self._last_successful_writer(state)
        state.mode = "B"
        state.relay.update({
            "previous_agent": previous_agent, "next_agent": next_agent,
            "worktree": str(worktree), "branch": evidence["branch"],
            "checkpoint": evidence["head"], "git_status": evidence["status"],
            "recent_log": evidence["recent_log"], "diff_stat": evidence["diff_stat"],
            "remaining_work": state.current_stage or "first incomplete stage",
        })
        self.state_mgr.append_event(
            task_id, "relay.verified", previous_agent=previous_agent, next_agent=next_agent,
            evidence=evidence, discrepancies=discrepancies,
        )
        plan = TaskPlan.from_dict(state.plan or {})
        start = self._resume_stage_index(state, plan)
        if start is None:
            return self._block_and_finish(state, "RELAY", "no incomplete stage to resume", log)
        stages = [StageConfig.from_dict(stage.__dict__) for stage in plan.stages[start:]]
        relay_stage = next((stage for stage in stages if stage.access != AccessMode.SYSTEM.value), None)
        if relay_stage is not None:
            relay_stage.agents = [next_agent]
            relay_stage.fallback_agents = []
        state.status = "RUNNING"
        state.blocker = None
        self._activate_workspace(str(worktree))
        before = self.git.snapshot()
        self._run_pipeline_stages(state, plan, stages, log)
        if state.status != "BLOCKED":
            if self.git.preflight().dirty:
                try:
                    state.checkpoints["relay"] = self.worktree_mgr.checkpoint(
                        str(worktree), task_id, next_agent,
                    )
                except Exception as error:
                    self._block(state, "CHECKPOINT", str(error), log)
            if state.status != "BLOCKED":
                state.status = "DONE"
        self._finish_state(state, before)
        self.state_mgr.append_event(task_id, "run.finished", status=state.status, mode="B")
        return state

    @staticmethod
    def _resume_stage_index(state: RuntimeState, plan: TaskPlan) -> Optional[int]:
        if state.current_stage:
            for index, stage in enumerate(plan.stages):
                if stage.name == state.current_stage and state.stage_statuses.get(stage.name) != StageStatus.DONE.value:
                    return index
        for index, stage in enumerate(plan.stages):
            if state.stage_statuses.get(stage.name) not in {StageStatus.DONE.value, StageStatus.WAIVED.value}:
                return index
        return None

    def _finish_state(self, state: RuntimeState, initial_snapshot: Dict[str, str]) -> None:
        delta = self._snapshot_delta(initial_snapshot, self.git.snapshot())
        if delta:
            state.changed_files = delta
        self.state_mgr.write_handoff(state.task_id, state)
        self.state_mgr.save_state(state)

    @staticmethod
    def _snapshot_delta(before: Dict[str, str], after: Dict[str, str]) -> List[str]:
        return sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))

    def _next_key(self, stage_name: str) -> str:
        self._stage_sequence += 1
        return f"{self._stage_sequence:03d}-{stage_name.upper()}"

    def _get_adapter(self, agent: str):
        if agent not in self._adapters:
            self._adapters[agent] = get_adapter(
                agent, use_fake=self.use_fake, fake_options=self.fake_options,
            )
        return self._adapters[agent]

    def _run_agent_stage(
        self, state: RuntimeState, plan: TaskPlan, stage: StageConfig,
        log: Callable[[str], None],
    ) -> bool:
        if stage.access == AccessMode.WRITE.value and self.repo_root == self.base_repo:
            return self._block(
                state, stage.name, "worker WRITE stage is forbidden in the base worktree", log,
            )
        key = self._next_key(stage.name)
        prior_paths = [item["output_file"] for item in state.handoffs if item.get("output_file")]
        before = self.git.snapshot()

        def execute(agent: str) -> AgentExecutionResult:
            prompt = build_stage_prompt(
                task_id=plan.task_id,
                user_request=state.user_request,
                stage_name=stage.name,
                agent_name=agent,
                execution_mode=stage.execution,
                base_commit=state.base_commit,
                worktree_path=str(self.repo_root),
                output_artifact=plan.output_artifact,
                role=stage.role,
                access=stage.access,
                extra_context={
                    "handoff_path": str(self.state_mgr.get_task_dir(plan.task_id) / "handoff.json"),
                    "output_paths": prior_paths,
                    "handoff_content": self._handoff_excerpt(state),
                    "checks_summary": self._checks_summary(state),
                },
            )
            return self._get_adapter(agent).run(
                prompt=prompt,
                cwd=str(self.repo_root),
                stage=stage.name,
                timeout_sec=self.agent_timeout_sec,
                access=stage.access,
            )

        if stage.execution == ExecutionMode.PARALLEL.value:
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(stage.agents)) as pool:
                futures = {pool.submit(execute, agent): agent for agent in stage.agents}
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            results.sort(key=lambda item: stage.agents.index(item.agent))
        else:
            results = []
            for agent in stage.agents:
                result = execute(agent)
                results.append(result)
                if stage.required and not result.success:
                    break
            if len(stage.agents) == 1 and results and not results[0].success:
                for fallback in stage.fallback_agents:
                    log(f"{stage.name}: {results[0].agent} failed; trying fallback {fallback}")
                    fallback_result = execute(fallback)
                    results.append(fallback_result)
                    if fallback_result.success:
                        break

        after = self.git.snapshot()
        delta = self._snapshot_delta(before, after)
        for result in results:
            if stage.access == AccessMode.WRITE.value:
                result.changed_files = delta
            self.state_mgr.write_result(plan.task_id, key, result)
            state.handoffs.append({
                "stage": stage.name,
                "stage_key": key,
                "agent": result.agent,
                "success": result.success,
                "output_file": result.output_file,
                "review_verdict": result.review_verdict,
            })
        state.agent_results[key] = [result.to_dict() for result in results]
        self.state_mgr.write_handoff(plan.task_id, state)

        failed = [result for result in results if not result.success]
        required_successes = stage.min_success or (
            len(stage.agents) if stage.execution == ExecutionMode.PARALLEL.value else 1
        )
        stage_succeeded = sum(result.success for result in results) >= required_successes
        if stage.required and not stage_succeeded:
            return self._block(state, stage.name, "; ".join(
                f"{item.agent}: {item.error_message or item.exit_code}" for item in failed
            ), log)
        if stage.access == AccessMode.WRITE.value and stage.required and not delta:
            return self._block(state, stage.name, "write stage completed without changing a repository file", log)

        stage_status = StageStatus.RUNNING.value if stage.name == "REVIEW" else StageStatus.DONE.value
        state.stage_statuses[stage.name] = stage_status
        if stage.name != "REVIEW":
            current_outputs = [result.output_file for result in results if result.output_file]
            self.state_mgr.append_event(plan.task_id, "stage.finished", stage=stage.name, status="DONE", outputs=current_outputs)
        self.state_mgr.save_state(state)
        return True

    def _check_commands(self) -> List[List[str]]:
        commands = list(self.explicit_checks)
        if self.auto_discover_checks:
            commands.extend(self.check_runner.discover())
        unique: List[List[str]] = []
        for command in commands:
            if command not in unique:
                unique.append(command)
        return unique

    def _run_checks(
        self, state: RuntimeState, stage: StageConfig,
        log: Callable[[str], None],
    ) -> bool:
        commands = self._check_commands()
        if not commands:
            state.stage_statuses[stage.name] = StageStatus.WAIVED.value
            self.state_mgr.append_event(state.task_id, "checks.waived", reason="no checks discovered or supplied")
            self.state_mgr.save_state(state)
            log("No deterministic checks discovered; CHECK marked WAIVED.")
            return True
        results = self.check_runner.run_all(commands)
        cycle = state.review_cycles
        for result in results:
            record = {"cycle": cycle, **result.to_dict()}
            state.checks.append(record)
            self.state_mgr.append_event(
                state.task_id, "check.finished", command=result.command,
                exit_code=result.exit_code, success=result.success,
            )
        failed = [result for result in results if not result.success]
        if failed:
            return self._block(
                state, stage.name,
                "deterministic check failed: " + " ".join(failed[0].command), log,
            )
        state.stage_statuses[stage.name] = StageStatus.DONE.value
        self.state_mgr.save_state(state)
        log(f"Deterministic checks passed: {len(results)}")
        return True

    def _run_review_loop(
        self, state: RuntimeState, plan: TaskPlan, review_stage: StageConfig,
        log: Callable[[str], None],
    ) -> bool:
        while True:
            if not self._run_agent_stage(state, plan, review_stage, log):
                return False
            key = next(reversed(state.agent_results))
            results = state.agent_results[key]
            successful_results = [result for result in results if result.get("success")]
            verdicts = [result.get("review_verdict") for result in successful_results]
            if not successful_results:
                return self._block(state, "REVIEW", "no reviewer completed successfully", log)
            if any(verdict is None for verdict in verdicts):
                return self._block(state, "REVIEW", "reviewer omitted or contradicted the explicit verdict", log)
            if ReviewVerdict.BLOCKED.value in verdicts:
                return self._block(state, "REVIEW", "reviewer returned BLOCKED", log)
            if all(verdict == ReviewVerdict.PASS.value for verdict in verdicts):
                state.stage_statuses["REVIEW"] = StageStatus.DONE.value
                self.state_mgr.append_event(state.task_id, "stage.finished", stage="REVIEW", status="DONE")
                self.state_mgr.save_state(state)
                return True

            if state.review_cycles >= self.max_review_cycles:
                return self._block(state, "REVIEW", f"maximum fix cycles exceeded ({self.max_review_cycles})", log)
            state.review_cycles += 1
            log(f"Review requested fixes; starting cycle {state.review_cycles}/{self.max_review_cycles}")
            actual_fixer = self._last_successful_writer(state) or plan.fix_agent
            fix_stage = StageConfig(
                name="FIX", execution="PIPELINE", agents=[actual_fixer], role="fixer",
                access=AccessMode.WRITE.value, required=True,
            )
            state.current_stage = "FIX"
            if not self._run_agent_stage(state, plan, fix_stage, log):
                return False
            check_stage = StageConfig(
                name="CHECK", execution="PIPELINE", agents=["system"], role="deterministic verifier",
                access=AccessMode.SYSTEM.value, required=True,
            )
            state.current_stage = "CHECK"
            if not self._run_checks(state, check_stage, log):
                return False
            state.current_stage = "REVIEW"

    def _final_gate(self, state: RuntimeState, plan: TaskPlan, log: Callable[[str], None]) -> bool:
        if any(stage.name == "REVIEW" for stage in plan.stages) and state.stage_statuses.get("REVIEW") != StageStatus.DONE.value:
            return self._block(state, "FINAL", "independent review has not passed", log)
        if plan.output_artifact:
            artifact = (self.repo_root / plan.output_artifact).resolve()
            try:
                artifact.relative_to(self.repo_root)
            except ValueError:
                return self._block(state, "FINAL", "output artifact escapes repository", log)
            if not artifact.is_file() or artifact.stat().st_size == 0:
                return self._block(state, "FINAL", f"missing output artifact: {plan.output_artifact}", log)
            state.final_artifact = str(artifact.relative_to(self.repo_root))
        state.stage_statuses["FINAL"] = StageStatus.DONE.value
        self.state_mgr.append_event(state.task_id, "final.accepted", artifact=state.final_artifact)
        self.state_mgr.save_state(state)
        log("Final gate passed.")
        return True

    @staticmethod
    def _checks_summary(state: RuntimeState) -> str:
        if not state.checks:
            return "No deterministic checks have run."
        lines = []
        for item in state.checks:
            command = " ".join(item["command"])
            lines.append(f"- cycle {item['cycle']}: exit={item['exit_code']} success={item['success']} `{command}`")
        return "\n".join(lines)

    def _handoff_excerpt(self, state: RuntimeState, max_chars: int = 60_000) -> str:
        chunks: List[str] = []
        remaining = max_chars
        for item in reversed(state.handoffs):
            if not item.get("success") or not item.get("output_file") or remaining <= 0:
                continue
            path = self.base_repo / item["output_file"]
            try:
                content = path.read_text(encoding="utf-8")
            except OSError:
                continue
            output_start = content.find("## Output")
            stderr_start = content.find("## Stderr")
            if output_start >= 0:
                output_end = stderr_start if stderr_start > output_start else len(content)
                primary = content[output_start:output_end][:10_000]
                secondary = content[stderr_start:][:2_000] if stderr_start >= 0 else ""
                excerpt = primary + ("\n" + secondary if secondary else "")
            else:
                excerpt = content[:12_000]
            excerpt = excerpt[:remaining]
            chunks.append(f"### {item['stage']} / {item['agent']}\n{excerpt}")
            remaining -= len(excerpt)
        return "\n\n".join(reversed(chunks)) or "No successful prior stage output."

    @staticmethod
    def _last_successful_writer(state: RuntimeState) -> Optional[str]:
        for results in reversed(list(state.agent_results.values())):
            for result in reversed(results):
                if result.get("success") and result.get("stage") in {"IMPLEMENT", "SYNTHESIZE", "FIX"}:
                    return str(result["agent"])
        return None

    def _block(
        self, state: RuntimeState, stage: str, reason: str,
        log: Callable[[str], None],
    ) -> bool:
        state.status = "BLOCKED"
        state.blocker = reason
        state.stage_statuses[stage] = StageStatus.BLOCKED.value
        self.state_mgr.append_event(state.task_id, "stage.blocked", stage=stage, reason=reason)
        self.state_mgr.save_state(state)
        log(f"BLOCKED at {stage}: {reason}")
        return False
