"""Deterministic fake adapter used by unit and integration tests."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

from demo.orchestrator.adapters.base import BaseAgentAdapter
from demo.orchestrator.models import AgentExecutionResult


class FakeAgentAdapter(BaseAgentAdapter):
    def __init__(
        self, name: str = "fake", force_success: bool = True, exit_code: int = 1,
        review_verdict: Optional[str] = "PASS", review_sequence: Optional[List[str]] = None,
        create_files: bool = True, mock_output: str = "",
    ):
        super().__init__(name)
        self.force_success = force_success
        self.exit_code = exit_code
        self.review_verdict = review_verdict
        self.review_sequence = list(review_sequence or [])
        self.create_files = create_files
        self.mock_output = mock_output
        self.prompts: List[Dict[str, str]] = []

    def check_availability(self) -> Tuple[bool, str]:
        return True, "fake adapter"

    def build_command(
        self, prompt: str, cwd: str, access: str = "READ_ONLY",
        options: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        return ["fake", self.name, access]

    def run(
        self, prompt: str, cwd: str, stage: str, timeout_sec: int = 600,
        access: str = "READ_ONLY", options: Optional[Dict[str, Any]] = None,
    ) -> AgentExecutionResult:
        self.prompts.append({"prompt": prompt, "cwd": cwd, "stage": stage, "access": access})
        if not self.force_success:
            return AgentExecutionResult(
                agent=self.name, stage=stage, success=False, exit_code=self.exit_code,
                error_message="Simulated failure",
            )
        changed: List[str] = []
        if self.create_files and access.upper() == "WRITE":
            artifact_match = re.search(r"Implement the requested result in `([^`]+)`", prompt)
            relative_target = artifact_match.group(1) if stage.upper() == "SYNTHESIZE" and artifact_match else f"fake-{stage.lower()}.txt"
            target = Path(cwd) / relative_target
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"{self.name} completed {stage}\n", encoding="utf-8")
            changed.append(relative_target)
        verdict = None
        if stage.upper() == "REVIEW":
            verdict = self.review_sequence.pop(0) if self.review_sequence else self.review_verdict
        verdict_line = f"\nVERDICT: {verdict}" if verdict else ""
        response = "ACCEPT" if stage.upper() == "RESPONSE" else ""
        return AgentExecutionResult(
            agent=self.name, stage=stage, success=True, exit_code=0,
            stdout=f"{self.name} completed {stage}. {self.mock_output}{response}{verdict_line}",
            review_verdict=verdict, changed_files=changed, duration_sec=0.01,
        )
