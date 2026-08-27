"""Gemini CLI Agent Adapter."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from demo.orchestrator.adapters.base import BaseAgentAdapter


class GeminiAgentAdapter(BaseAgentAdapter):
    """Adapter for Gemini CLI (gemini -p)."""

    def __init__(self, binary_name: str = "gemini"):
        super().__init__(name="gemini")
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
            "-y",
            "--approval-mode",
            "yolo",
            "-o",
            "text",
        ]
        model = options.get("model")
        if model:
            cmd.extend(["-m", str(model)])
        return cmd
