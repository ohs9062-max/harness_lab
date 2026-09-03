"""Safe subprocess abstraction for non-interactive AI CLIs."""

from __future__ import annotations

import re
import subprocess
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from demo.orchestrator.models import AgentExecutionResult


class BaseAgentAdapter(ABC):
    def __init__(self, name: str, max_output_chars: int = 200_000):
        self.name = name
        self.max_output_chars = max_output_chars

    @abstractmethod
    def check_availability(self) -> Tuple[bool, str]:
        raise NotImplementedError

    @abstractmethod
    def build_command(
        self, prompt: str, cwd: str, access: str = "READ_ONLY",
        options: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        raise NotImplementedError

    def run(
        self, prompt: str, cwd: str, stage: str, timeout_sec: int = 600,
        access: str = "READ_ONLY", options: Optional[Dict[str, Any]] = None,
    ) -> AgentExecutionResult:
        available, reason = self.check_availability()
        if not available:
            return AgentExecutionResult(
                agent=self.name, stage=stage, success=False, exit_code=-1,
                error_message=f"Agent '{self.name}' is unavailable: {reason}",
            )
        command = self.build_command(prompt=prompt, cwd=cwd, access=access, options=options)
        started = time.monotonic()
        try:
            process = subprocess.run(
                command, cwd=cwd, capture_output=True, text=True,
                timeout=timeout_sec, shell=False,
            )
            stdout, stdout_cut = self._cap(process.stdout)
            stderr, stderr_cut = self._cap(process.stderr)
            verdict = None
            if stage.upper() == "REVIEW":
                verdict = self._extract_review_verdict(stdout) or self._extract_review_verdict(stderr)
            return AgentExecutionResult(
                agent=self.name,
                stage=stage,
                success=process.returncode == 0,
                exit_code=process.returncode,
                stdout=stdout,
                stderr=stderr,
                error_message=None if process.returncode == 0 else f"Process exited with code {process.returncode}",
                review_verdict=verdict,
                duration_sec=time.monotonic() - started,
                output_truncated=stdout_cut or stderr_cut,
            )
        except subprocess.TimeoutExpired as error:
            stdout = error.stdout if isinstance(error.stdout, str) else ""
            stderr = error.stderr if isinstance(error.stderr, str) else ""
            return AgentExecutionResult(
                agent=self.name, stage=stage, success=False, exit_code=-2,
                stdout=self._cap(stdout)[0], stderr=self._cap(stderr)[0],
                error_message=f"Execution timed out after {timeout_sec} seconds",
                duration_sec=time.monotonic() - started,
            )
        except OSError as error:
            return AgentExecutionResult(
                agent=self.name, stage=stage, success=False, exit_code=-3,
                error_message=f"Subprocess execution failed: {error}",
                duration_sec=time.monotonic() - started,
            )

    def _cap(self, text: str) -> Tuple[str, bool]:
        if len(text) <= self.max_output_chars:
            return text, False
        return text[: self.max_output_chars] + "\n[OUTPUT TRUNCATED]", True

    @staticmethod
    def _extract_review_verdict(text: str) -> Optional[str]:
        non_empty = [line.strip() for line in text.splitlines() if line.strip()]
        if not non_empty:
            return None
        match = re.fullmatch(r"(?i)(?:VERDICT|판정)\s*:\s*(PASS|FIX_REQUIRED|BLOCKED)", non_empty[-1])
        return match.group(1).upper() if match else None
