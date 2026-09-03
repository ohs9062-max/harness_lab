"""Codex CLI adapter with workspace sandboxing and auto-reviewed approvals."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from demo.orchestrator.adapters.base import BaseAgentAdapter


class CodexAgentAdapter(BaseAgentAdapter):
    def __init__(self, binary_name: str = "codex"):
        super().__init__("codex")
        self.binary_name = binary_name

    def check_availability(self) -> Tuple[bool, str]:
        if not shutil.which(self.binary_name):
            return False, f"Binary '{self.binary_name}' not found in PATH"
        try:
            result = subprocess.run([self.binary_name, "--version"], capture_output=True, text=True, timeout=10)
            return (result.returncode == 0, (result.stdout or result.stderr).strip())
        except OSError as error:
            return False, str(error)

    def build_command(
        self, prompt: str, cwd: str, access: str = "READ_ONLY",
        options: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        options = options or {}
        command = [self.binary_name, "exec", "-C", cwd]
        if access.upper() == "WRITE":
            # --approve-for-me supplies Codex's auto-reviewed workspace-write policy
            # and is mutually exclusive with an explicit --sandbox flag.
            command.append("--approve-for-me")
        else:
            command.extend(["-s", "read-only"])
        command.extend(["--ephemeral", "--color", "never"])
        if options.get("model"):
            command.extend(["-m", str(options["model"])])
        command.append(prompt)
        return command
