"""Automatic role pipeline with real handoffs, checks, review, and fix loops."""

from __future__ import annotations

import concurrent.futures
import json
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
        self.repo_root = Path(repo_root).resolve()
        self.use_fake = use_fake_agents
        self.fake_options = fake_options or {}
        self.max_review_cycles = max_review_cycles
        self.agent_timeout_sec = agent_timeout_sec
        self.auto_discover_checks = auto_discover_checks
        self.explicit_checks = [list(command) for command in (check_commands or [])]
        self.git = GitInspector(str(self.repo_root))
        self.state_mgr = StateManager(str(self.repo_root))
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
        preflight = self.git.preflight()
        initial_snapshot = self.git.snapshot()

        def log(message: str) -> None:
            if progress_callback:
                progress_callback(message)
            else:
                print(f"[Harness] {message}")

        state = RuntimeState(
            task_id=plan.task_id,
            status="RUNNING" if execute else "DRY_RUN",
            user_request=user_request,
            base_commit=preflight.head,
            initial_dirty=preflight.dirty,
            plan=plan.to_dict(),
        )
        self.state_mgr.save_state(state)
        self.state_mgr.append_event(
            plan.task_id, "run.started", base_commit=preflight.head,
            branch=preflight.branch, initial_dirty=preflight.dirty,
        )
        log(f"{plan.task_id} started on {preflight.branch}@{preflight.head[:8]}")

        if dry_run and not execute:
            for stage in plan.stages:
                state.stage_statuses[stage.name] = StageStatus.PENDING.value
            state.status = "DRY_RUN_COMPLETED"
            self._finish_state(state, initial_snapshot)
            log("Dry-run completed; no agent or check process was started.")
            return state

        for stage in plan.stages:
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

        if state.status != "BLOCKED":
            state.status = "DONE"
        self._finish_state(state, initial_snapshot)
        self.state_mgr.append_event(plan.task_id, "run.finished", status=state.status, blocker=state.blocker)
        log(f"Finished with status {state.status}")
        return state

    def _finish_state(self, state: RuntimeState, initial_snapshot: Dict[str, str]) -> None:
        state.changed_files = self._snapshot_delta(initial_snapshot, self.git.snapshot())
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
            path = self.repo_root / item["output_file"]
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
