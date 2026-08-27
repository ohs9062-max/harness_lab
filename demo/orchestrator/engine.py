"""Orchestrator V1 Core Engine."""

from __future__ import annotations

import concurrent.futures
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from demo.orchestrator.adapters import get_adapter
from demo.orchestrator.models import (
    AgentExecutionResult,
    ExecutionMode,
    ReviewVerdict,
    RuntimeState,
    StageConfig,
    StageStatus,
    TaskPlan,
)
from demo.orchestrator.prompt_builder import build_stage_prompt
from demo.orchestrator.state import StateManager
from demo.orchestrator.worktree import WorktreeManager


class OrchestratorEngine:
    """
    Core engine that executes multi-agent Stage Plans with:
    - Worktree isolation
    - Parallel / Pipeline execution
    - Required Agent Gates
    - Checkpoint management
    - Review & Fix loop
    - Full State & Log tracking
    """

    def __init__(
        self,
        repo_root: str,
        use_fake_agents: bool = False,
        fake_options: Optional[Dict[str, Any]] = None,
        max_review_cycles: int = 2,
    ):
        self.repo_root = Path(repo_root).resolve()
        self.use_fake = use_fake_agents
        self.fake_options = fake_options or {}
        self.max_review_cycles = max_review_cycles

        self.worktree_mgr = WorktreeManager(str(self.repo_root))
        self.state_mgr = StateManager(str(self.repo_root))

    def run_plan(
        self,
        plan: TaskPlan,
        user_request: str,
        dry_run: bool = True,
        execute: bool = False,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> RuntimeState:
        """Execute the entire Stage Plan."""
        def log(msg: str):
            if progress_callback:
                progress_callback(msg)
            else:
                print(f"[Orchestrator] {msg}")

        base_commit = self.worktree_mgr.get_current_head()
        state = RuntimeState(
            task_id=plan.task_id,
            status="RUNNING" if execute else "DRY_RUN",
            user_request=user_request,
            plan=plan.to_dict(),
        )
        self.state_mgr.save_state(state)

        log(f"Starting Task: {plan.task_id} (Type: {plan.task_type}, Mode: {'EXECUTE' if execute else 'DRY-RUN'})")
        log(f"Base Commit: {base_commit}")

        # Track checkpoint commits created by workers
        worker_checkpoints: Dict[str, str] = {}
        stage_idx = 0

        while stage_idx < len(plan.stages):
            stage = plan.stages[stage_idx]
            state.current_stage = stage.name
            log(f"\n▶ Stage [{stage.name}] (Mode: {stage.execution}, Agents: {stage.agents}, Required: {stage.required})")

            if stage.name.upper() == "FINAL":
                stage.status = StageStatus.DONE.value
                state.stage_statuses[stage.name] = stage.status
                self.state_mgr.save_state(state)
                log(f"✔ Stage [{stage.name}] completed. Deliverable: artifacts/{plan.output_artifact}")
                stage_idx += 1
                continue

            # 1. Prepare Worktrees
            agent_worktrees: Dict[str, str] = {}
            for ag in stage.agents:
                if ag.lower() == "user":
                    continue
                branch, wt_path = self.worktree_mgr.create_isolated_worktree(
                    task_id=plan.task_id,
                    agent_name=ag,
                    base_commit=base_commit,
                    dry_run=dry_run,
                )
                agent_worktrees[ag] = wt_path
                state.worktrees[f"{stage.name}_{ag}"] = wt_path
                log(f"  - Worktree for [{ag}]: branch={branch}, path={wt_path}")

            if dry_run and not execute:
                log(f"  [DRY-RUN] Simulating stage {stage.name} without running subprocesses.")
                stage.status = StageStatus.DONE.value
                state.stage_statuses[stage.name] = stage.status
                self.state_mgr.save_state(state)
                stage_idx += 1
                continue

            # 2. Execute Stage Agents (PARALLEL or PIPELINE)
            results: List[AgentExecutionResult] = []
            if stage.execution.upper() == ExecutionMode.PARALLEL.value:
                log(f"  Running {len(stage.agents)} agents in PARALLEL...")
                with concurrent.futures.ThreadPoolExecutor(max_workers=len(stage.agents)) as executor:
                    future_to_agent = {
                        executor.submit(
                            self._execute_single_agent,
                            plan=plan,
                            stage=stage,
                            agent_name=ag,
                            worktree_path=agent_worktrees.get(ag, str(self.repo_root)),
                            base_commit=base_commit,
                            user_request=user_request,
                            worker_checkpoints=worker_checkpoints,
                            dry_run=dry_run,
                        ): ag
                        for ag in stage.agents
                    }
                    for future in concurrent.futures.as_completed(future_to_agent):
                        res = future.result()
                        results.append(res)
            else:
                log(f"  Running {len(stage.agents)} agents in PIPELINE...")
                for ag in stage.agents:
                    res = self._execute_single_agent(
                        plan=plan,
                        stage=stage,
                        agent_name=ag,
                        worktree_path=agent_worktrees.get(ag, str(self.repo_root)),
                        base_commit=base_commit,
                        user_request=user_request,
                        worker_checkpoints=worker_checkpoints,
                        dry_run=dry_run,
                    )
                    results.append(res)

            # Record results to state
            state.agent_results[stage.name] = [r.to_dict() for r in results]
            for r in results:
                if r.checkpoint_commit:
                    worker_checkpoints[r.agent] = r.checkpoint_commit

            # 3. Required Agent Gate Check
            required_agents = set(stage.agents) if stage.required else set()
            failed_required = [r for r in results if r.agent in required_agents and not r.success]

            if failed_required:
                error_summary = ", ".join(f"{r.agent} (code {r.exit_code}): {r.error_message}" for r in failed_required)
                log(f"✖ [GATE BLOCKED] Required agents failed in stage [{stage.name}]: {error_summary}")
                stage.status = StageStatus.BLOCKED.value
                state.stage_statuses[stage.name] = StageStatus.BLOCKED.value
                state.status = "BLOCKED"
                self.state_mgr.save_state(state)
                break  # Halt immediately; do not proceed to subsequent stages

            stage.status = StageStatus.DONE.value
            state.stage_statuses[stage.name] = StageStatus.DONE.value
            log(f"✔ Stage [{stage.name}] PASSED Gate.")

            # 4. Review Verdict & FIX Loop Handling
            if stage.name.upper() == "REVIEW":
                review_res = results[0] if results else None
                verdict = review_res.review_verdict if review_res else "PASS"
                log(f"  Review Verdict: {verdict}")

                if verdict == ReviewVerdict.FIX_REQUIRED.value:
                    state.review_cycles += 1
                    if state.review_cycles > self.max_review_cycles:
                        log(f"✖ [BLOCKED] Max review cycles ({self.max_review_cycles}) exceeded!")
                        state.status = "BLOCKED"
                        self.state_mgr.save_state(state)
                        break

                    log(f"  ↺ [FIX LOOP] Review requested fixes (Cycle {state.review_cycles}/{self.max_review_cycles}). Inserting FIX stage.")
                    # Insert FIX stage and repeat REVIEW
                    fix_stage = StageConfig(name="FIX", execution="PIPELINE", agents=["claude"], required=True)
                    self._execute_single_agent(
                        plan=plan,
                        stage=fix_stage,
                        agent_name="claude",
                        worktree_path=agent_worktrees.get("claude", str(self.repo_root)),
                        base_commit=base_commit,
                        user_request=user_request,
                        worker_checkpoints=worker_checkpoints,
                        dry_run=dry_run,
                    )
                    # Re-run REVIEW stage in next iteration
                    continue

                elif verdict == ReviewVerdict.BLOCKED.value:
                    log(f"✖ [BLOCKED] Reviewer explicitly blocked the deliverable.")
                    state.status = "BLOCKED"
                    self.state_mgr.save_state(state)
                    break

            stage_idx += 1
            self.state_mgr.save_state(state)

        if state.status != "BLOCKED":
            state.status = "DONE" if execute else "DRY_RUN_COMPLETED"
        self.state_mgr.save_state(state)
        log(f"\n=== Task Execution Finished. Final Status: {state.status} ===")
        return state

    def _execute_single_agent(
        self,
        plan: TaskPlan,
        stage: StageConfig,
        agent_name: str,
        worktree_path: str,
        base_commit: str,
        user_request: str,
        worker_checkpoints: Dict[str, str],
        dry_run: bool,
    ) -> AgentExecutionResult:
        """Run an individual agent inside its isolated worktree."""
        adapter = get_adapter(
            agent_name,
            use_fake=self.use_fake,
            fake_options=self.fake_options,
        )

        prompt = build_stage_prompt(
            task_id=plan.task_id,
            user_request=user_request,
            stage_name=stage.name,
            agent_name=agent_name,
            execution_mode=stage.execution,
            base_commit=base_commit,
            worktree_path=worktree_path,
            output_artifact=plan.output_artifact,
            extra_context={"worker_checkpoints": worker_checkpoints},
        )

        # Run agent
        result = adapter.run(
            prompt=prompt,
            cwd=worktree_path,
            stage=stage.name,
            timeout_sec=300,
        )

        # Save log
        self.state_mgr.write_agent_log(
            task_id=plan.task_id,
            stage=stage.name,
            agent=agent_name,
            stdout=result.stdout,
            stderr=result.stderr,
        )

        # If execution succeeded, create local checkpoint commit
        if result.success and not dry_run:
            commit_msg = f"checkpoint({agent_name}): {stage.name} completed for {plan.task_id}"
            commit_hash = self.worktree_mgr.create_local_checkpoint_commit(
                worktree_path=worktree_path,
                message=commit_msg,
                dry_run=dry_run,
            )
            result.checkpoint_commit = commit_hash

        return result
