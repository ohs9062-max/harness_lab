"""Turn one natural-language goal into a validated role pipeline."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, Optional

from demo.orchestrator.adapters import get_adapter
from demo.orchestrator.models import AccessMode, ExecutionMode, StageConfig, TaskPlan, TaskType


class Coordinator:
    COORDINATOR_PROMPT = """You are the Harness Lab coordinator. Return only one JSON object.
Build the smallest safe plan for the REQUIRED TOP-LEVEL MODE supplied below.
Never change MODE A/B/C. PIPELINE and PARALLEL are only stage execution strategies.
Separate creators from reviewers. Deterministic CHECK must occur immediately before REVIEW.
Allowed stage names: ANALYZE, RESEARCH, DESIGN, IMPLEMENT, SYNTHESIZE, TEST, CHECK, REVIEW, FINAL.
Allowed agents: claude, codex, gemini, system. Parallel stages MUST be READ_ONLY.
IMPLEMENT and SYNTHESIZE use WRITE. TEST uses READ_ONLY. CHECK and FINAL use SYSTEM. REVIEW uses READ_ONLY.
Use Claude primarily for analysis/design/synthesis, Codex for implementation/testing, Gemini for adversarial review.
Do not include shell commands. For code work output_artifact may be an empty string; code changes are the result.

Schema:
{
  "task_type": "RESEARCH|DEVELOPMENT|MIXED",
  "mode": "A|C",
  "output_artifact": "relative/path/or/empty",
  "goal": "string",
  "scope": "string",
  "completion_criteria": "string",
  "fix_agent": "claude|codex|gemini",
  "stages": [{
    "name": "allowed stage",
    "execution": "PIPELINE|PARALLEL",
    "agents": ["allowed agent"],
    "fallback_agents": ["optional fallback agent"],
    "min_success": 1,
    "role": "short role name",
    "access": "READ_ONLY|WRITE|SYSTEM",
    "required": true
  }]
}
"""

    def __init__(self, repo_root: str):
        self.repo_root = repo_root

    @staticmethod
    def _stage(
        name: str, agents: list[str], access: str, role: str,
        execution: str = "PIPELINE", fallback_agents: Optional[list[str]] = None,
        min_success: int = 0,
    ) -> StageConfig:
        return StageConfig(
            name=name, execution=execution, agents=agents,
            fallback_agents=fallback_agents or [], access=access, role=role, required=True,
            min_success=min_success,
        )

    def create_deterministic_plan(
        self, task_id: str, user_request: str, mode: str = "C",
    ) -> TaskPlan:
        mode = mode.upper()
        if mode == "B":
            raise ValueError("MODE B resumes an existing TASK-ID and cannot create a new plan")
        if mode not in {"A", "C"}:
            raise ValueError(f"Invalid mode: {mode}")
        lowered = user_request.lower()
        research = any(word in lowered for word in ("조사", "분석", "비교", "리서치", "research", "analyze", "compare"))
        development = any(word in lowered for word in (
            "구현", "코드", "수정", "통합", "개발", "만들", "build", "implement", "fix", "refactor",
        ))
        task_type = TaskType.MIXED if research and development else TaskType.RESEARCH if research else TaskType.DEVELOPMENT
        read = AccessMode.READ_ONLY.value
        write = AccessMode.WRITE.value
        system = AccessMode.SYSTEM.value

        if mode == "A":
            output = ""
            stages = [
                self._stage("IMPLEMENT", ["codex"], write, "independent worker"),
                self._stage("CHECK", ["system"], system, "worker gate"),
                self._stage("FINAL", ["system"], system, "selection completion gate"),
            ]
        elif task_type == TaskType.RESEARCH:
            output = f"artifacts/{task_id}/result.md"
            stages = [
                self._stage("RESEARCH", ["claude", "codex", "gemini"], read, "independent researcher", "PARALLEL", min_success=2),
                self._stage("SYNTHESIZE", ["claude"], write, "evidence synthesizer", fallback_agents=["codex"]),
                self._stage("CHECK", ["system"], system, "deterministic verifier"),
                self._stage("REVIEW", ["gemini"], read, "independent reviewer"),
                self._stage("FINAL", ["system"], system, "completion gate"),
            ]
        else:
            output = ""
            first_name = "ANALYZE" if task_type == TaskType.MIXED else "DESIGN"
            first_agents = ["claude", "gemini"] if task_type == TaskType.MIXED else ["claude"]
            first_execution = "PARALLEL" if len(first_agents) > 1 else "PIPELINE"
            stages = [
                self._stage(first_name, first_agents, read, "planner", first_execution, min_success=1),
                self._stage("DESIGN", ["claude"], read, "architect", fallback_agents=["gemini"]) if first_name != "DESIGN" else None,
                self._stage("IMPLEMENT", ["codex"], write, "implementer", fallback_agents=["claude"]),
                self._stage("TEST", ["codex"], read, "implementation tester"),
                self._stage("CHECK", ["system"], system, "deterministic verifier"),
                self._stage("REVIEW", ["gemini"], read, "independent reviewer"),
                self._stage("FINAL", ["system"], system, "completion gate"),
            ]
            stages = [stage for stage in stages if stage is not None]
            if first_name == "DESIGN":
                stages[0].fallback_agents = ["gemini"]

        plan = TaskPlan(
            task_id=task_id,
            task_type=task_type.value,
            mode=mode,
            output_artifact=output,
            goal=user_request,
            scope="Only the requested repository and goal",
            completion_criteria="Deterministic checks succeed and independent review returns PASS",
            fix_agent="codex",
            stages=stages,
        )
        plan.validate()
        return plan

    # Kept for callers of the V1 public method.
    def create_deterministic_research_plan(
        self, task_id: str, user_request: str, output_artifact: str = "result.md",
    ) -> TaskPlan:
        plan = self.create_deterministic_plan(task_id, "research: " + user_request)
        plan.output_artifact = f"artifacts/{task_id}/{output_artifact}"
        return plan

    def generate_plan(
        self, user_request: str, task_id: Optional[str] = None,
        use_fake: bool = False, use_deterministic: bool = False, mode: str = "C",
    ) -> TaskPlan:
        task_id = task_id or f"TASK-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"
        mode = mode.upper()
        if mode == "B":
            raise ValueError("MODE B requires --resume with an existing TASK-ID")
        if use_fake or use_deterministic or mode == "A":
            return self.create_deterministic_plan(task_id, user_request, mode=mode)

        result = get_adapter("codex").run(
            prompt=f"{self.COORDINATOR_PROMPT}\n\nREQUIRED TOP-LEVEL MODE: {mode}\n\nUSER REQUEST:\n{user_request}",
            cwd=self.repo_root,
            stage="COORDINATOR",
            timeout_sec=180,
            access=AccessMode.READ_ONLY.value,
        )
        if not result.success:
            raise RuntimeError(f"Coordinator failed: {result.error_message}")
        data = self._parse_json_safely(result.stdout)
        data["task_id"] = task_id
        data["mode"] = mode
        plan = TaskPlan.from_dict(data)
        plan.validate()
        return plan

    @staticmethod
    def _parse_json_safely(text: str) -> Dict[str, Any]:
        try:
            value = json.loads(text)
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        candidate = fenced.group(1) if fenced else None
        if candidate is None:
            first, last = text.find("{"), text.rfind("}")
            candidate = text[first:last + 1] if first >= 0 and last > first else ""
        value = json.loads(candidate)
        if not isinstance(value, dict):
            raise ValueError("Coordinator output must be a JSON object")
        return value
