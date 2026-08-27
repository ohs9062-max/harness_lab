"""Base Agent Adapter and execution abstraction."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from demo.orchestrator.models import AgentExecutionResult


class BaseAgentAdapter(ABC):
    """Abstract base class for all AI CLI adapters."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def check_availability(self) -> Tuple[bool, str]:
        """Check if the local CLI binary exists and is usable."""
        pass

    @abstractmethod
    def build_command(
        self,
        prompt: str,
        cwd: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Build the command line argument list for non-interactive execution."""
        pass

    def run(
        self,
        prompt: str,
        cwd: str,
        stage: str,
        timeout_sec: int = 600,
        options: Optional[Dict[str, Any]] = None,
    ) -> AgentExecutionResult:
        """Run the CLI tool safely via subprocess and capture output."""
        available, reason = self.check_availability()
        if not available:
            return AgentExecutionResult(
                agent=self.name,
                stage=stage,
                success=False,
                exit_code=-1,
                error_message=f"Agent '{self.name}' is unavailable: {reason}",
            )

        cmd = self.build_command(prompt=prompt, cwd=cwd, options=options)
        start_time = time.time()

        try:
            # We never use shell=True and pass cmd as a list of strings
            process = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                shell=False,
            )
            duration = time.time() - start_time
            success = (process.returncode == 0)

            # Review verdict extraction if stage is REVIEW
            verdict = None
            if stage.upper() == "REVIEW":
                verdict = self._extract_review_verdict(process.stdout + "\n" + process.stderr)

            return AgentExecutionResult(
                agent=self.name,
                stage=stage,
                success=success,
                exit_code=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
                error_message=None if success else f"Process exited with code {process.returncode}",
                review_verdict=verdict,
                duration_sec=duration,
            )

        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            return AgentExecutionResult(
                agent=self.name,
                stage=stage,
                success=False,
                exit_code=-2,
                stdout=e.stdout if isinstance(e.stdout, str) else "",
                stderr=e.stderr if isinstance(e.stderr, str) else "",
                error_message=f"Execution timed out after {timeout_sec} seconds",
                duration_sec=duration,
            )
        except Exception as e:
            duration = time.time() - start_time
            return AgentExecutionResult(
                agent=self.name,
                stage=stage,
                success=False,
                exit_code=-3,
                error_message=f"Subprocess execution failed: {str(e)}",
                duration_sec=duration,
            )

    def _extract_review_verdict(self, text: str) -> str:
        """Parse review verdict (PASS, FIX_REQUIRED, BLOCKED)."""
        upper = text.upper()
        if "VERDICT: PASS" in upper or "판정: PASS" in upper or "판정: 통과" in upper:
            return "PASS"
        if "VERDICT: FIX_REQUIRED" in upper or "판정: FIX_REQUIRED" in upper or "판정: 수정 필요" in upper:
            return "FIX_REQUIRED"
        if "VERDICT: BLOCKED" in upper or "판정: BLOCKED" in upper or "판정: 차단" in upper:
            return "BLOCKED"
        # Fallback keyword checks
        if "FIX_REQUIRED" in upper:
            return "FIX_REQUIRED"
        if "BLOCKED" in upper:
            return "BLOCKED"
        if "PASS" in upper and "FAIL" not in upper:
            return "PASS"
        return "PASS"  # Default assumption if successful review without explicit failure
