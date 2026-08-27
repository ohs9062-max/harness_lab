"""Prompt Builder for Stage-specific Agent Execution."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

FRESHNESS_KEYWORDS = ["현재", "최신", "2026", "지금", "최근", "최신 알고리즘", "현재 정책", "latest", "current"]


def is_freshness_required(user_request: str) -> bool:
    """Check if the user request demands temporal freshness / current accuracy."""
    req_lower = user_request.lower()
    return any(k.lower() in req_lower for k in FRESHNESS_KEYWORDS)


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
) -> str:
    """Generate structured, actionable prompt for the agent for a given stage."""
    agent_upper = agent_name.upper()
    stage_upper = stage_name.upper()
    freshness_req = is_freshness_required(user_request)

    base_instructions = f"""# TASK EXECUTION INSTRUCTION

## Task Context
- TASK-ID: {task_id}
- CURRENT-STAGE: {stage_upper}
- AGENT: {agent_upper}
- EXECUTION-MODE: {execution_mode}
- BASE-COMMIT: {base_commit}
- WORKTREE-PATH: {worktree_path}
- TARGET-ARTIFACT: {output_artifact}

## Original User Request
\"\"\"{user_request}\"\"\"

## Global Rules & Constraints
1. Work ONLY within the current working directory / worktree ({worktree_path}).
2. Do NOT run git push, merge, reset --hard, or remote operations.
3. Preserve existing harness documentation policies.
4. Do NOT read other workers' ongoing worktrees before COMPARE.
"""

    if stage_upper == "RESEARCH":
        freshness_block = ""
        if freshness_req:
            freshness_block = f"""
### [CRITICAL] Freshness Gate Required
The user request explicitly asks for CURRENT / 2026 accuracy.
For EVERY claim, you MUST classify and record:
- SOURCE-DATE: YYYY-MM-DD
- CURRENT-APPLICABILITY: CURRENT | PARTIALLY_CURRENT | HISTORICAL | UNKNOWN
- CURRENTNESS-EVIDENCE: Specific proof that this rule/algorithm is active in 2026.
* If real-time web verification is unavailable, explicitly state: `WEB_VERIFICATION_UNAVAILABLE` and do NOT mark historical data as CURRENT without proof.
"""

        prompt = f"""{base_instructions}
## Stage Objective: RESEARCH
Conduct rigorous, independent research on the user request.

## Instructions:
1. Record your findings in `shared/RESEARCH.md`.
2. Follow strict Namespace ID rules:
   - Claims: `{agent_upper}-C001`, `{agent_upper}-C002`, ...
   - Sources: `{agent_upper}-S001`, `{agent_upper}-S002`, ...
3. Separate official confirmed facts (Grade A) from unverified rumors/myths.
4. Do NOT assume claims without evidence.{freshness_block}
5. Mark tentative conclusions and what needs cross-validation.
"""

    elif stage_upper == "COMPARE":
        extra = extra_context or {}
        checkpoints_info = extra.get("worker_checkpoints", {})
        prompt = f"""{base_instructions}
## Stage Objective: COMPARE
Compare independent research results from all parallel workers.

## Worker Checkpoints:
{chr(10).join(f"- {k}: {v}" for k, v in checkpoints_info.items())}

## Instructions:
1. Read `shared/RESEARCH.md` from each worker.
2. Group matching claims into Normalized Claims (`N-C001`, `N-C002`, ...).
3. Document common claims, conflicting claims, and unique findings in `shared/COMPARE.md`.
4. Do NOT treat the same source cited by multiple AI as multiple independent evidence.
"""

    elif stage_upper == "VERIFY":
        prompt = f"""{base_instructions}
## Stage Objective: VERIFY
Verify all Normalized Claims and establish the Verified Set.

## Instructions:
1. Inspect `shared/COMPARE.md` and check the source validity and current applicability for each N-Cxxx.
2. Filter out UNKNOWN / HISTORICAL claims from the core strategy.
3. Update the `Verified Set` table in `shared/COMPARE.md` with final verdicts.
"""

    elif stage_upper == "SYNTHESIZE":
        prompt = f"""{base_instructions}
## Stage Objective: SYNTHESIZE
Create the final deliverable artifact based on the Verified Set.

## Instructions:
1. Write the final synthesis to `artifacts/{task_id}/{output_artifact}` (or `artifacts/{output_artifact}`).
2. Structure the document clearly:
   - Verified Core Facts
   - Strong but Qualified Claims
   - Known Limitations & Disproved Myths
   - Concrete Actionable Operational Guide
3. Do NOT simply concatenate all AI opinions; ground every recommendation in the Verified Set.
"""

    elif stage_upper == "REVIEW":
        prompt = f"""{base_instructions}
## Stage Objective: INDEPENDENT REVIEW
Perform an objective, adversarial review of the synthesized artifact and research records.

## Instructions:
1. Verify whether all claims in `artifacts/{output_artifact}` are backed by the Verified Set in `shared/COMPARE.md`.
2. Check if any disproved myths or unverified rumors leaked into the final strategy.
3. Record your review in `shared/REVIEW.md`.
4. End your review with an explicit verdict on a single line:
   `VERDICT: PASS` or `VERDICT: FIX_REQUIRED` or `VERDICT: BLOCKED`
"""

    elif stage_upper == "FIX":
        prompt = f"""{base_instructions}
## Stage Objective: FIX DEFECTS
Address issues identified in `shared/REVIEW.md`.

## Instructions:
1. Read findings and required fixes in `shared/REVIEW.md`.
2. Correct the synthesized artifact in `artifacts/{output_artifact}` and related shared docs.
3. Record the fix log in `shared/context.md`.
"""

    elif stage_upper == "FINAL":
        prompt = f"""{base_instructions}
## Stage Objective: FINAL ACCEPTANCE
Prepare final summary for user acceptance.
"""

    else:
        prompt = f"""{base_instructions}
## Stage Objective: {stage_upper}
Execute requirements for stage {stage_upper}.
"""

    return prompt
