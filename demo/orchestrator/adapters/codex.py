"""Codex CLI Agent Adapter."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from demo.orchestrator.adapters.base import BaseAgentAdapter


class CodexAgentAdapter(BaseAgentAdapter):
    """Adapter for Codex CLI (codex exec)."""

    def __init__(self, binary_name: str = "codex"):
        super().__init__(name="codex")
        self.binary_name = binary_name

    def check_availability(self) -> Tuple[bool, str]:
        path = shutil.which(self.binary_name)
        if not path:
            return False, f"Binary '{self.binary_name}' not found in PATH"
        try:
            res = subprocess.run(
                [self.binary_name, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
            )
            if res.returncode == 0:
                return True, res.stdout.strip()
            return False, f"Version check failed: {res.stderr.strip()}"
        except Exception as e:
            return False, f"Execution failed: {str(e)}"

    def build_command(
        self,
        prompt: str,
        cwd: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        options = options or {}
        cmd = [
            self.binary_name,
            "exec",
            "-C",
            cwd,
            "--dangerously-bypass-approvals-and-sandbox",
        ]
        model = options.get("model")
        if model:
            cmd.extend(["-m", str(model)])

        # Prompt is passed as last positional argument
        cmd.append(prompt)
        return cmd
