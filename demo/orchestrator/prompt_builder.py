"""Grounded, role-specific prompts with explicit handoff paths."""

from __future__ import annotations

from typing import Any, Dict, Optional

FRESHNESS_KEYWORDS = ("현재", "최신", "최근", "지금", "latest", "current")


def is_freshness_required(user_request: str) -> bool:
    lowered = user_request.lower()
    return any(keyword in lowered for keyword in FRESHNESS_KEYWORDS)


def build_stage_prompt(
    task_id: str,
    user_request: str,
    stage_name: str,
    agent_name: str,
    execution_mode: str,
    base_commit: str,
    worktree_path: str,
    output_artifact: str,
    extra_context: Optional[Dict[str, Any]] = None,
    role: str = "worker",
    access: str = "READ_ONLY",
) -> str:
    stage = stage_name.upper()
    context = extra_context or {}
    handoff_path = context.get("handoff_path", f".harness/runs/{task_id}/handoff.json")
    checks = context.get("checks_summary", "No deterministic checks recorded yet.")
    output_paths = context.get("output_paths", [])
    handoff_content = context.get("handoff_content", "No prior output content.")
    prior_outputs = "\n".join(f"- {path}" for path in output_paths) or "- none"
    access_rule = (
        "You may edit files inside the target repository, but only those required by the request."
        if access.upper() == "WRITE"
        else "Read-only role: do not create, edit, delete, commit, or stage repository files."
    )
    prompt = f"""# Harness Lab stage assignment

- TASK-ID: {task_id}
- STAGE: {stage}
- ROLE: {role}
- AGENT: {agent_name}
- ACCESS: {access}
- BASE-COMMIT: {base_commit}
- REPOSITORY: {worktree_path}
- HANDOFF: {handoff_path}

## User goal

{user_request}

## Safety and grounding

1. Read AGENTS.md and relevant repository instructions before acting.
2. Inspect actual files and Git state; never invent code, paths, commands, or test results.
3. Preserve existing user changes. Never commit, merge, push, reset, or delete branches; Runner-owned task checkpoints are handled outside your session.
4. {access_rule}
5. Keep the final response concise and evidence-based. The runner stores it for the next stage.

## Prior stage outputs

{prior_outputs}

Read `{handoff_path}` and the relevant outputs above before deciding. Current deterministic check summary:

{checks}

## Inline handoff excerpts

The runner injects these bounded excerpts because some AI CLIs hide gitignored `.harness` files:

{handoff_content}
"""

    if stage in {"ANALYZE", "DESIGN"}:
        prompt += """
## Deliverable

Return an implementation-ready design: current structure, exact files in scope, acceptance checks, risks, and non-goals. Do not modify files.
"""
    elif stage == "RESEARCH":
        freshness = "For time-sensitive claims, include source date and current applicability." if is_freshness_required(user_request) else ""
        prompt += f"""
## Deliverable

Independently investigate the goal. Separate verified facts, assumptions, conflicts, and actionable recommendations. {freshness}
Do not read other concurrently running agents' outputs.
"""
    elif stage in {"IMPLEMENT", "SYNTHESIZE", "FIX"}:
        target = output_artifact or "the requested repository code"
        prompt += f"""
## Deliverable

Implement the requested result in `{target}`. For FIX, address every actionable finding in the latest REVIEW output.
Run focused checks you can safely run, but leave the final independent verdict to the reviewer.
In your response list changed files, commands actually run, results, and any remaining issue.
"""
    elif stage == "REVIEW":
        prompt += """
## Deliverable

Act as an adversarial independent reviewer. Inspect the user goal, prior design, actual Git diff, changed files, and deterministic check results. Do not modify anything.
Report each finding as severity / file:line / evidence / required fix. A preference is not a defect.
Your final non-empty line MUST be exactly one of:
VERDICT: PASS
VERDICT: FIX_REQUIRED
VERDICT: BLOCKED
Use PASS only when the goal is met, checks are credible, and no required fix remains.
"""
    return prompt
