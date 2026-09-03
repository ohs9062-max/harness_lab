"""Validated data contracts for the Harness Lab runner."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskType(str, Enum):
    RESEARCH = "RESEARCH"
    DEVELOPMENT = "DEVELOPMENT"
    MIXED = "MIXED"


class ExecutionMode(str, Enum):
    PIPELINE = "PIPELINE"
    PARALLEL = "PARALLEL"


class AccessMode(str, Enum):
    READ_ONLY = "READ_ONLY"
    WRITE = "WRITE"
    SYSTEM = "SYSTEM"


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
    "DEFINE", "ANALYZE", "RESEARCH", "COMPARE", "VERIFY", "SYNTHESIZE",
    "DESIGN", "IMPLEMENT", "CHECK", "TEST", "REVIEW", "FIX", "FINAL",
}
VALID_AGENTS = {"claude", "codex", "gemini", "system", "user", "fake"}
WRITE_STAGES = {"IMPLEMENT", "SYNTHESIZE", "FIX"}


@dataclass
class StageConfig:
    name: str
    execution: str
    agents: List[str]
    role: str = "worker"
    access: str = AccessMode.READ_ONLY.value
    required: bool = True
    status: str = StageStatus.PENDING.value
    fallback_agents: List[str] = field(default_factory=list)
    min_success: int = 0

    def validate(self) -> None:
        name = self.name.upper()
        if name not in VALID_STAGE_NAMES:
            raise ValueError(f"Invalid stage name: {self.name}")
        if self.execution.upper() not in {e.value for e in ExecutionMode}:
            raise ValueError(f"Invalid execution mode: {self.execution}")
        if self.access.upper() not in {a.value for a in AccessMode}:
            raise ValueError(f"Invalid access mode: {self.access}")
        if not self.agents:
            raise ValueError(f"Stage '{self.name}' must have at least one agent")
        unknown = [agent for agent in self.agents if agent.lower() not in VALID_AGENTS]
        unknown.extend(agent for agent in self.fallback_agents if agent.lower() not in VALID_AGENTS)
        if unknown:
            raise ValueError(f"Invalid agents in stage '{self.name}': {unknown}")
        if self.execution.upper() == ExecutionMode.PARALLEL.value and self.access.upper() == AccessMode.WRITE.value:
            raise ValueError("Parallel write stages are unsafe; use MODE A worktrees instead")
        if self.execution.upper() == ExecutionMode.PARALLEL.value and self.fallback_agents:
            raise ValueError("Parallel stages do not support fallback agents")
        required_successes = self.min_success or (len(self.agents) if self.execution.upper() == ExecutionMode.PARALLEL.value else 1)
        if required_successes < 1 or required_successes > len(self.agents):
            raise ValueError(f"Invalid min_success for stage '{self.name}': {self.min_success}")
        if name in WRITE_STAGES and self.access.upper() != AccessMode.WRITE.value:
            raise ValueError(f"Stage '{name}' must use WRITE access")
        if name in {"CHECK", "TEST", "FINAL"} and self.access.upper() != AccessMode.SYSTEM.value:
            raise ValueError(f"Stage '{name}' must use SYSTEM access")
        if name == "REVIEW" and self.access.upper() != AccessMode.READ_ONLY.value:
            raise ValueError("REVIEW must be read-only")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StageConfig":
        name = str(data["name"]).upper()
        default_access = (
            AccessMode.WRITE.value if name in WRITE_STAGES else
            AccessMode.SYSTEM.value if name in {"CHECK", "TEST", "FINAL"} else
            AccessMode.READ_ONLY.value
        )
        return cls(
            name=name,
            execution=str(data.get("execution", ExecutionMode.PIPELINE.value)).upper(),
            agents=[str(agent).lower() for agent in data.get("agents", [])],
            fallback_agents=[str(agent).lower() for agent in data.get("fallback_agents", [])],
            role=str(data.get("role", "worker")),
            access=str(data.get("access", default_access)).upper(),
            required=bool(data.get("required", True)),
            status=str(data.get("status", StageStatus.PENDING.value)).upper(),
            min_success=int(data.get("min_success", 0)),
        )


@dataclass
class TaskPlan:
    task_id: str
    task_type: str
    mode: str
    output_artifact: str
    stages: List[StageConfig]
    input_artifact: Optional[str] = None
    goal: str = ""
    scope: str = ""
    completion_criteria: str = ""
    fix_agent: str = "codex"

    def validate(self) -> None:
        if not self.task_id:
            raise ValueError("task_id is required")
        if self.task_type.upper() not in {item.value for item in TaskType}:
            raise ValueError(f"Invalid task_type: {self.task_type}")
        if self.mode.upper() not in {"A", "B", "C"}:
            raise ValueError(f"Invalid mode: {self.mode}")
        if not self.stages:
            raise ValueError("At least one stage is required")
        for stage in self.stages:
            stage.validate()
        names = [stage.name.upper() for stage in self.stages]
        if names[-1] != "FINAL":
            raise ValueError("FINAL must be the last stage")
        if "REVIEW" in names:
            for review_index in (index for index, name in enumerate(names) if name == "REVIEW"):
                if review_index == 0 or names[review_index - 1] not in {"CHECK", "TEST"}:
                    raise ValueError("CHECK or TEST must be immediately before REVIEW")
            writers = {
                agent for stage in self.stages if stage.access == AccessMode.WRITE.value
                for agent in stage.agents + stage.fallback_agents
            }
            reviewers = {
                agent for stage in self.stages if stage.name == "REVIEW"
                for agent in stage.agents + stage.fallback_agents
            }
            overlap = writers & reviewers
            if overlap:
                raise ValueError(f"Implementers cannot review their own result: {sorted(overlap)}")
            if self.fix_agent in reviewers:
                raise ValueError(f"Reviewer cannot also be fix_agent: {self.fix_agent}")
        if self.fix_agent not in VALID_AGENTS - {"system", "user", "fake"}:
            raise ValueError(f"Invalid fix_agent: {self.fix_agent}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskPlan":
        return cls(
            task_id=str(data.get("task_id", "")),
            task_type=str(data.get("task_type", TaskType.DEVELOPMENT.value)).upper(),
            mode=str(data.get("mode", "C")).upper(),
            input_artifact=data.get("input_artifact"),
            output_artifact=str(data.get("output_artifact", "")),
            goal=str(data.get("goal", "")),
            scope=str(data.get("scope", "")),
            completion_criteria=str(data.get("completion_criteria", "")),
            fix_agent=str(data.get("fix_agent", "codex")).lower(),
            stages=[StageConfig.from_dict(stage) for stage in data.get("stages", [])],
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
    output_file: Optional[str] = None
    changed_files: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    review_verdict: Optional[str] = None
    duration_sec: float = 0.0
    output_truncated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RuntimeState:
    task_id: str
    status: str
    user_request: str
    base_commit: str = ""
    initial_dirty: bool = False
    current_stage: Optional[str] = None
    plan: Optional[Dict[str, Any]] = None
    stage_statuses: Dict[str, str] = field(default_factory=dict)
    agent_results: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    handoffs: List[Dict[str, Any]] = field(default_factory=list)
    checks: List[Dict[str, Any]] = field(default_factory=list)
    changed_files: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    review_cycles: int = 0
    final_artifact: Optional[str] = None
    blocker: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
