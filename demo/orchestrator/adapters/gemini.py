"""Gemini CLI adapter with plan/auto-edit permission separation."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from demo.orchestrator.adapters.base import BaseAgentAdapter


class GeminiAgentAdapter(BaseAgentAdapter):
    def __init__(self, binary_name: str = "gemini"):
        super().__init__("gemini")
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
        approval = "auto_edit" if access.upper() == "WRITE" else "plan"
        command = [
            self.binary_name, "-p", prompt, "--approval-mode", approval,
            "--skip-trust", "--output-format", "text",
        ]
        if options.get("model"):
            command.extend(["--model", str(options["model"])])
        return command
