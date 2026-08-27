"""Coordinator V1 (Codex-based Stage Planning & JSON Contract)."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, Optional

from demo.orchestrator.adapters import get_adapter
from demo.orchestrator.models import (
    ExecutionMode,
    StageConfig,
    StageStatus,
    TaskPlan,
    TaskType,
)
from demo.orchestrator.prompt_builder import is_freshness_required


class Coordinator:
    """
    Coordinator analyzes user input and outputs a machine-readable Stage Plan JSON.
    In V1, Coordinator is fixed to Codex (executed in an independent session).
    """

    COORDINATOR_SYSTEM_PROMPT = """You are the Harness Lab Coordinator (Codex).
Your job is to analyze the user request and return ONLY a valid, machine-readable JSON Stage Plan.
Do NOT include any conversational preamble, markdown code fence, or explanation. Output pure JSON only.

JSON SCHEMA:
{
  "task_type": "RESEARCH" | "DEVELOPMENT" | "MIXED",
  "execution": "PIPELINE" | "PARALLEL",
  "input_artifact": string | null,
  "output_artifact": string,
  "goal": string,
  "scope": string,
  "completion_criteria": string,
  "stages": [
    {
      "name": "DEFINE" | "RESEARCH" | "COMPARE" | "VERIFY" | "SYNTHESIZE" | "DESIGN" | "IMPLEMENT" | "REVIEW" | "FINAL",
      "execution": "PIPELINE" | "PARALLEL",
      "agents": ["claude" | "codex" | "gemini" | "user"],
      "required": boolean
    }
  ]
}

POLICY RULES:
1. For Research/Strategy tasks (requests containing 조사, 전략, 비교, 최신, 분석, 검증, etc.), ALWAYS configure:
   - task_type: "RESEARCH"
   - execution: "PARALLEL"
   - RESEARCH stage: execution "PARALLEL", agents ["claude", "codex", "gemini"], required: true
   - COMPARE stage: execution "PIPELINE", agents ["gemini"], required: true
   - VERIFY stage: execution "PIPELINE", agents ["codex"], required: true
   - SYNTHESIZE stage: execution "PIPELINE", agents ["claude"], required: true
   - REVIEW stage: execution "PIPELINE", agents ["gemini"], required: true
   - FINAL stage: execution "PIPELINE", agents ["user"], required: true
2. For Development tasks, configure DESIGN -> IMPLEMENT -> REVIEW -> FINAL.
"""

    def __init__(self, repo_root: str):
        self.repo_root = repo_root

    def create_deterministic_research_plan(
        self,
        task_id: str,
        user_request: str,
        output_artifact: str = "naver_blog_strategy.md",
    ) -> TaskPlan:
        """Fallback / Deterministic default plan for Research tasks."""
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
            input_artifact=None,
            output_artifact=output_artifact,
            goal=f"Execute research and synthesis for: {user_request}",
            scope="Comprehensive multi-agent investigation and verification",
            completion_criteria="Independent review PASS and artifact generation",
            stages=stages,
        )

    def generate_plan(
        self,
        user_request: str,
        task_id: Optional[str] = None,
        use_fake: bool = False,
        use_deterministic: bool = False,
    ) -> TaskPlan:
        """Generate and validate a TaskPlan from user request."""
        if not task_id:
            task_id = f"TASK-{datetime.now().strftime('%Y-%m-%d')}-{int(datetime.now().timestamp()) % 1000:03d}"

        if use_deterministic or use_fake:
            plan = self.create_deterministic_research_plan(task_id, user_request)
            plan.validate()
            return plan

        # Call real Coordinator (Codex)
        adapter = get_adapter("codex")
        prompt = f"{self.COORDINATOR_SYSTEM_PROMPT}\n\nUSER REQUEST:\n{user_request}"

        result = adapter.run(
            prompt=prompt,
            cwd=self.repo_root,
            stage="COORDINATOR",
            timeout_sec=120,
        )

        if not result.success:
            raise RuntimeError(f"Coordinator failed to generate plan: {result.error_message}")

        raw_output = result.stdout.strip()
        plan_dict = self._parse_json_safely(raw_output)
        plan_dict["task_id"] = task_id

        plan = TaskPlan.from_dict(plan_dict)
        plan.validate()
        return plan

    def _parse_json_safely(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON from model output."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try regex search for code block or first JSON object
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))

        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))

        raise ValueError(f"Failed to parse valid JSON from Coordinator output:\n{text}")
