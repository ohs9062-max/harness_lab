"""Fake Agent Adapter for testing and mocking orchestrator workflows."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from demo.orchestrator.adapters.base import BaseAgentAdapter
from demo.orchestrator.models import AgentExecutionResult


class FakeAgentAdapter(BaseAgentAdapter):
    """Stub adapter that simulates AI execution without running actual LLMs."""

    def __init__(
        self,
        name: str = "fake",
        force_success: bool = True,
        exit_code: int = 0,
        mock_output: str = "Mock output from FakeAgent",
        review_verdict: str = "PASS",
        create_files: bool = True,
    ):
        super().__init__(name=name)
        self.force_success = force_success
        self.exit_code = exit_code
        self.mock_output = mock_output
        self.review_verdict = review_verdict
        self.create_files = create_files
        self.execution_history: List[Dict[str, Any]] = []

    def check_availability(self) -> Tuple[bool, str]:
        return True, "FakeAgent is always available"

    def build_command(
        self,
        prompt: str,
        cwd: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        return ["fake_agent_runner", "--agent", self.name]

    def run(
        self,
        prompt: str,
        cwd: str,
        stage: str,
        timeout_sec: int = 600,
        options: Optional[Dict[str, Any]] = None,
    ) -> AgentExecutionResult:
        options = options or {}
        self.execution_history.append({
            "stage": stage,
            "cwd": cwd,
            "prompt": prompt,
            "options": options,
        })

        if not self.force_success:
            return AgentExecutionResult(
                agent=self.name,
                stage=stage,
                success=False,
                exit_code=self.exit_code if self.exit_code != 0 else 1,
                stderr="Simulated failure in FakeAgentAdapter",
                error_message="Simulated failure",
                duration_sec=0.01,
            )

        output_files = []
        if self.create_files and os.path.exists(cwd):
            output_files = self._simulate_file_generation(cwd, stage)

        verdict = None
        if stage.upper() == "REVIEW":
            verdict = self.review_verdict

        return AgentExecutionResult(
            agent=self.name,
            stage=stage,
            success=True,
            exit_code=0,
            stdout=f"Stage {stage} completed successfully by {self.name}.\n{self.mock_output}\nVERDICT: {verdict or 'PASS'}",
            output_files=output_files,
            review_verdict=verdict,
            duration_sec=0.05,
        )

    def _simulate_file_generation(self, cwd: str, stage: str) -> List[str]:
        """Generate mock artifacts based on stage."""
        created = []
        cwd_path = Path(cwd)
        shared_dir = cwd_path / "shared"
        shared_dir.mkdir(parents=True, exist_ok=True)

        prefix = self.name.upper()

        if stage.upper() == "RESEARCH":
            research_file = shared_dir / "RESEARCH.md"
            content = f"""# Research Findings by {self.name}

## Claims
### {prefix}-C001
- 주장: 네이버 검색은 C-Rank와 D.I.A.+의 결합으로 작동한다.
- 근거: 공식 기술 발표
- SOURCE-ID: {prefix}-S001
- 출처 날짜: 2026-01-01
- CURRENT-APPLICABILITY: CURRENT
- CURRENTNESS-EVIDENCE: 2026년 검색 결과 확인
- 상태: CONFIRMED

## Sources
### {prefix}-S001
- 제목: 네이버 검색 공식 가이드
- URL: https://help.naver.com
"""
            research_file.write_text(content, encoding="utf-8")
            created.append("shared/RESEARCH.md")

        elif stage.upper() == "COMPARE":
            compare_file = shared_dir / "COMPARE.md"
            content = """# Normalized Claims Comparison
### N-C001
- 정규화 주장: C-Rank와 D.I.A.+ 결합 작동
- 원본 Claim: CLAUDE-C001, CODEX-C001, GEMINI-C001
- 상태: VERIFIED
"""
            compare_file.write_text(content, encoding="utf-8")
            created.append("shared/COMPARE.md")

        elif stage.upper() == "SYNTHESIZE":
            art_dir = cwd_path / "artifacts"
            art_dir.mkdir(parents=True, exist_ok=True)
            art_file = art_dir / "strategy.md"
            art_file.write_text("# Final Verified Strategy Document\nAll claims verified.", encoding="utf-8")
            created.append("artifacts/strategy.md")

        elif stage.upper() == "REVIEW":
            review_file = shared_dir / "REVIEW.md"
            review_file.write_text(f"# Independent Review\nVERDICT: {self.review_verdict}\nAll required checks passed.", encoding="utf-8")
            created.append("shared/REVIEW.md")

        return created
