"""Command-line entry point for the automatic Harness Lab runner."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from demo.orchestrator.adapters import get_adapter
from demo.orchestrator.checks import CheckRunner
from demo.orchestrator.coordinator import Coordinator
from demo.orchestrator.engine import OrchestratorEngine
from demo.orchestrator.git_state import GitInspector


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m demo.orchestrator",
        description="Plan, delegate, implement, check, review, and fix one user goal with local AI CLIs.",
    )
    parser.add_argument("request", nargs="?", help="Natural-language task goal")
    execution = parser.add_mutually_exclusive_group()
    execution.add_argument("--dry-run", action="store_true", help="Print and persist a plan without starting agents")
    execution.add_argument("--execute", action="store_true", help="Run the generated plan with real or fake agents")
    parser.add_argument("--repo", default=".", help="Target Git repository root (default: current directory)")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--deterministic-plan", action="store_true", help="Skip the coordinator model and use policy routing")
    parser.add_argument("--fake-agents", action="store_true", help="Use deterministic fake agents")
    parser.add_argument("--check", action="append", default=[], metavar="COMMAND", help="Additional deterministic check; repeatable")
    parser.add_argument("--no-auto-checks", action="store_true", help="Do not discover package/Python checks")
    parser.add_argument("--max-review-cycles", type=int, default=2)
    parser.add_argument("--agent-timeout", type=int, default=600)
    parser.add_argument("--check-timeout", type=int, default=300)
    parser.add_argument("--doctor", action="store_true", help="Check Git and AI CLI availability, then exit")
    return parser


def _doctor(repo_root: Path) -> int:
    try:
        preflight = GitInspector(str(repo_root)).preflight()
        print(f"git: OK root={preflight.root} branch={preflight.branch} head={preflight.head[:8]} dirty={preflight.dirty}")
    except Exception as error:
        print(f"git: ERROR {error}")
        return 2
    failed = False
    for name in ("claude", "codex", "gemini"):
        available, detail = get_adapter(name).check_availability()
        print(f"{name}: {'OK' if available else 'ERROR'} {detail}")
        failed = failed or not available
    return 2 if failed else 0


def main(args: list[str] | None = None) -> int:
    options = create_parser().parse_args(args)
    repo_root = Path(options.repo).resolve()
    if options.doctor:
        return _doctor(repo_root)
    if not options.request:
        print("ERROR: request is required unless --doctor is used", file=sys.stderr)
        return 2
    if options.max_review_cycles < 0 or options.agent_timeout <= 0 or options.check_timeout <= 0:
        print("ERROR: cycle counts and timeouts must be positive", file=sys.stderr)
        return 2

    try:
        preflight = GitInspector(str(repo_root)).preflight()
    except Exception as error:
        print(f"ERROR: Git Preflight failed: {error}", file=sys.stderr)
        return 2

    try:
        check_runner = CheckRunner(str(repo_root), timeout_sec=options.check_timeout)
        checks = [check_runner.parse_user_command(value) for value in options.check]
        plan = Coordinator(str(repo_root)).generate_plan(
            user_request=options.request,
            task_id=options.task_id,
            use_fake=options.fake_agents,
            use_deterministic=options.deterministic_plan or not options.execute,
        )
    except Exception as error:
        print(f"ERROR: could not create plan: {error}", file=sys.stderr)
        return 1

    print(json.dumps(plan.to_dict(), indent=2, ensure_ascii=False))
    if not options.execute:
        print("DRY-RUN: pass --execute to start agents and checks.")

    engine = OrchestratorEngine(
        repo_root=str(repo_root),
        use_fake_agents=options.fake_agents,
        max_review_cycles=options.max_review_cycles,
        agent_timeout_sec=options.agent_timeout,
        check_timeout_sec=options.check_timeout,
        check_commands=checks,
        auto_discover_checks=not options.no_auto_checks,
    )
    state = engine.run_plan(
        plan=plan,
        user_request=options.request,
        dry_run=not options.execute,
        execute=options.execute,
    )
    print(f"status={state.status}")
    print(f"state={repo_root / '.harness' / 'runs' / state.task_id / 'state.json'}")
    if state.blocker:
        print(f"blocker={state.blocker}")
    return 0 if state.status in {"DONE", "DRY_RUN_COMPLETED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
