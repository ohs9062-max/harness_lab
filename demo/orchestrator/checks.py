"""Deterministic checks executed before an LLM review."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Sequence


@dataclass
class CheckResult:
    command: List[str]
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_sec: float
    timed_out: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class CheckRunner:
    """Discovers conservative project checks and runs argv without a shell."""

    def __init__(self, repo_root: str, timeout_sec: int = 300, max_output_chars: int = 80_000):
        self.repo_root = Path(repo_root).resolve()
        self.timeout_sec = timeout_sec
        self.max_output_chars = max_output_chars

    def discover(self) -> List[List[str]]:
        commands: List[List[str]] = []
        package_json = self.repo_root / "package.json"
        if package_json.exists():
            try:
                scripts = json.loads(package_json.read_text(encoding="utf-8")).get("scripts", {})
            except (OSError, json.JSONDecodeError, AttributeError):
                scripts = {}
            for script in ("lint", "typecheck", "test", "build"):
                if script in scripts:
                    commands.append(["npm", "run", script])

        test_roots = sorted({path.parent for path in self.repo_root.glob("**/tests/test_*.py")})
        for test_root in test_roots:
            commands.append([
                sys.executable, "-m", "unittest", "discover",
                "-s", str(test_root.relative_to(self.repo_root)), "-p", "test_*.py", "-v",
            ])
        if not test_roots and (self.repo_root / "pyproject.toml").exists():
            commands.append([sys.executable, "-m", "pytest", "-q"])
        return commands

    def parse_user_command(self, value: str) -> List[str]:
        command = shlex.split(value)
        if not command:
            raise ValueError("Empty check command")
        forbidden = {";", "&&", "||", "|", ">", ">>", "<"}
        if any(token in forbidden for token in command):
            raise ValueError("Shell control operators are not supported in check commands")
        return command

    def run_all(self, commands: Sequence[Sequence[str]]) -> List[CheckResult]:
        return [self.run(list(command)) for command in commands]

    def run(self, command: List[str]) -> CheckResult:
        started = time.monotonic()
        try:
            result = subprocess.run(
                command, cwd=self.repo_root, capture_output=True, text=True,
                timeout=self.timeout_sec, shell=False,
            )
            return CheckResult(
                command=command,
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout[: self.max_output_chars],
                stderr=result.stderr[: self.max_output_chars],
                duration_sec=time.monotonic() - started,
            )
        except subprocess.TimeoutExpired as error:
            return CheckResult(
                command=command,
                success=False,
                exit_code=-2,
                stdout=(error.stdout or "")[: self.max_output_chars] if isinstance(error.stdout, str) else "",
                stderr=(error.stderr or "")[: self.max_output_chars] if isinstance(error.stderr, str) else "",
                duration_sec=time.monotonic() - started,
                timed_out=True,
            )
        except OSError as error:
            return CheckResult(
                command=command, success=False, exit_code=-3, stdout="", stderr=str(error),
                duration_sec=time.monotonic() - started,
            )
