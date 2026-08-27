"""CLI interface for Harness Lab Orchestrator V1."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from demo.orchestrator.coordinator import Coordinator
from demo.orchestrator.engine import OrchestratorEngine


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m demo.orchestrator",
        description="Harness Lab Orchestrator V1 - Multi-Agent Automated Stage Runner",
    )
    parser.add_argument(
        "request",
        type=str,
        help="Natural language user request / task goal",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Simulate the Stage Plan and commands without running AI subprocesses (default: True)",
    )
    group.add_argument(
        "--execute",
        action="store_true",
        default=False,
        help="Actually run AI worker CLI subprocesses and create local checkpoint commits",
    )
    parser.add_argument(
        "--task-id",
        type=str,
        default=None,
        help="Optional custom TASK-ID (e.g. TASK-2026-08-27-001)",
    )
    parser.add_argument(
        "--output-artifact",
        type=str,
        default="naver_blog_strategy.md",
        help="Deliverable filename (default: naver_blog_strategy.md)",
    )
    parser.add_argument(
        "--fake-agents",
        action="store_true",
        default=False,
        help="Use stub/fake agents for deterministic testing without calling real LLM APIs",
    )
    parser.add_argument(
        "--deterministic-plan",
        action="store_true",
        default=False,
        help="Use default deterministic Stage Plan instead of invoking Coordinator Codex",
    )
    parser.add_argument(
        "--max-review-cycles",
        type=int,
        default=2,
        help="Maximum review & fix loop iterations (default: 2)",
    )
    return parser


def main(args: list[str] | None = None) -> int:
    parser = create_parser()
    opts = parser.parse_args(args)

    repo_root = Path.cwd()

    print("=" * 70)
    print("🚀 HARNESS LAB ORCHESTRATOR V1")
    print("=" * 70)
    print(f"User Request: {opts.request}")
    print(f"Execution Mode: {'EXECUTE (LIVE CLI)' if opts.execute else 'DRY-RUN (SIMULATION)'}")
    print(f"Agent Provider: {'FAKE/STUB AGENTS' if opts.fake_agents else 'REAL LOCAL CLIs'}")
    print("-" * 70)

    # 1. Coordinate & Generate Stage Plan
    print("\n[Step 1] Coordinating Task and Generating Stage Plan...")
    coordinator = Coordinator(str(repo_root))
    try:
        plan = coordinator.generate_plan(
            user_request=opts.request,
            task_id=opts.task_id,
            use_fake=opts.fake_agents,
            use_deterministic=opts.deterministic_plan or opts.dry_run and not opts.execute,
        )
    except Exception as e:
        print(f"❌ Coordinator Error: {e}", file=sys.stderr)
        return 1

    print(f"✔ Stage Plan Created (TASK-ID: {plan.task_id}, Type: {plan.task_type}, Mode: {plan.execution})")
    print(f"  Target Artifact: artifacts/{plan.output_artifact}")
    print(f"  Stages ({len(plan.stages)}):")
    for s in plan.stages:
        print(f"    - [{s.name:10s}] mode={s.execution:8s} agents={s.agents} required={s.required}")

    # 2. Run Engine
    print("\n[Step 2] Executing Stage Plan...")
    engine = OrchestratorEngine(
        repo_root=str(repo_root),
        use_fake_agents=opts.fake_agents,
        max_review_cycles=opts.max_review_cycles,
    )

    state = engine.run_plan(
        plan=plan,
        user_request=opts.request,
        dry_run=not opts.execute,
        execute=opts.execute,
    )

    print("-" * 70)
    print(f"Execution Completed: Status = {state.status}")
    print(f"State saved to: .harness/runs/{state.task_id}/state.json")
    print("=" * 70)
    return 0 if state.status in {"DONE", "DRY_RUN_COMPLETED"} else 2


if __name__ == "__main__":
    sys.exit(main())
