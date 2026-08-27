"""Claude Code CLI Agent Adapter."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from demo.orchestrator.adapters.base import BaseAgentAdapter


class ClaudeAgentAdapter(BaseAgentAdapter):
    """Adapter for Claude CLI (claude -p)."""

    def __init__(self, binary_name: str = "claude"):
        super().__init__(name="claude")
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
            "-p",
            prompt,
            "--permission-mode",
            "bypassPermissions",
            "--output-format",
            "text",
        ]
        model = options.get("model")
        if model:
            cmd.extend(["--model", str(model)])
        return cmd
