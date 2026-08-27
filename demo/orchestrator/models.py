"""Data models for Orchestrator V1."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskType(str, Enum):
    RESEARCH = "RESEARCH"
    DEVELOPMENT = "DEVELOPMENT"
    MIXED = "MIXED"


class ExecutionMode(str, Enum):
    PIPELINE = "PIPELINE"
    PARALLEL = "PARALLEL"


class StageStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    WAIVED = "WAIVED"


class ReviewVerdict(str, Enum):
    PASS = "PASS"
    FIX_REQUIRED = "FIX_REQUIRED"
    BLOCKED = "BLOCKED"
    PENDING = "PENDING"


VALID_STAGE_NAMES = {
    "DEFINE",
    "RESEARCH",
    "COMPARE",
    "VERIFY",
    "SYNTHESIZE",
    "DESIGN",
    "IMPLEMENT",
    "REVIEW",
    "FIX",
    "FINAL",
}

VALID_AGENTS = {"claude", "codex", "gemini", "user", "fake"}


@dataclass
class StageConfig:
    name: str
    execution: str  # "PIPELINE" or "PARALLEL"
    agents: List[str]
    required: bool = True
    status: str = StageStatus.PENDING.value

    def validate(self) -> None:
        if self.name.upper() not in VALID_STAGE_NAMES:
            raise ValueError(f"Invalid stage name: {self.name}. Allowed: {VALID_STAGE_NAMES}")
        if self.execution.upper() not in {ExecutionMode.PIPELINE.value, ExecutionMode.PARALLEL.value}:
            raise ValueError(f"Invalid execution mode: {self.execution}")
        if not self.agents:
            raise ValueError(f"Stage '{self.name}' must have at least one agent")
        for ag in self.agents:
            if ag.lower() not in VALID_AGENTS:
                raise ValueError(f"Invalid agent '{ag}' in stage '{self.name}'. Allowed: {VALID_AGENTS}")


@dataclass
class TaskPlan:
    task_id: str
    task_type: str  # "RESEARCH" | "DEVELOPMENT" | "MIXED"
    execution: str  # "PIPELINE" | "PARALLEL"
    output_artifact: str
    stages: List[StageConfig]
    input_artifact: Optional[str] = None
    goal: str = ""
    scope: str = ""
    completion_criteria: str = ""

    def validate(self) -> None:
        if not self.task_id:
            raise ValueError("task_id is required")
        if self.task_type.upper() not in {t.value for t in TaskType}:
            raise ValueError(f"Invalid task_type: {self.task_type}")
        if self.execution.upper() not in {e.value for e in ExecutionMode}:
            raise ValueError(f"Invalid execution: {self.execution}")
        if not self.output_artifact:
            raise ValueError("output_artifact is required")
        if not self.stages:
            raise ValueError("At least one stage is required in stages list")
        for s in self.stages:
            s.validate()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaskPlan:
        stages_data = data.get("stages", [])
        stages = [
            StageConfig(
                name=s["name"],
                execution=s.get("execution", "PIPELINE"),
                agents=s.get("agents", []),
                required=s.get("required", True),
                status=s.get("status", StageStatus.PENDING.value),
            )
            for s in stages_data
        ]
        return cls(
            task_id=data.get("task_id", ""),
            task_type=data.get("task_type", TaskType.RESEARCH.value),
            execution=data.get("execution", ExecutionMode.PARALLEL.value),
            input_artifact=data.get("input_artifact"),
            output_artifact=data.get("output_artifact", "result.md"),
            goal=data.get("goal", ""),
            scope=data.get("scope", ""),
            completion_criteria=data.get("completion_criteria", ""),
            stages=stages,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentExecutionResult:
    agent: str
    stage: str
    success: bool
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    checkpoint_commit: Optional[str] = None
    output_files: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    review_verdict: Optional[str] = None
    duration_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RuntimeState:
    task_id: str
    status: str
    user_request: str
    current_stage: Optional[str] = None
    plan: Optional[Dict[str, Any]] = None
    stage_statuses: Dict[str, str] = field(default_factory=dict)
    agent_results: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    worktrees: Dict[str, str] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    review_cycles: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
