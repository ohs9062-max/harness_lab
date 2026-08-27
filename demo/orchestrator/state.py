"""Runtime State and Execution Log Manager."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from demo.orchestrator.models import RuntimeState

# Regex patterns to sanitize sensitive tokens/keys
SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password|bearer)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?"),
    re.compile(r"(sk-[a-zA-Z0-9]{20,})"),
    re.compile(r"(ghp_[a-zA-Z0-9]{20,})"),
]


def mask_sensitive_data(text: str) -> str:
    """Mask credentials and secrets from text before storing or displaying."""
    if not text:
        return ""
    sanitized = text
    for pattern in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(r"\1: [MASKED]", sanitized)
    return sanitized


class StateManager:
    """Manages .harness/runs/<TASK-ID>/state.json and log files."""

    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root).resolve()
        self.runs_root = self.repo_root / ".harness" / "runs"

    def get_task_dir(self, task_id: str) -> Path:
        task_dir = self.runs_root / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        return task_dir

    def save_state(self, state: RuntimeState) -> Path:
        task_dir = self.get_task_dir(state.task_id)
        state_file = task_dir / "state.json"
        state.updated_at = datetime.now().isoformat()
        if not state.created_at:
            state.created_at = state.updated_at

        # Serialize to dict and write
        data = state.to_dict()
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return state_file

    def load_state(self, task_id: str) -> Optional[RuntimeState]:
        state_file = self.runs_root / task_id / "state.json"
        if not state_file.exists():
            return None
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return RuntimeState(**data)

    def write_agent_log(
        self,
        task_id: str,
        stage: str,
        agent: str,
        stdout: str,
        stderr: str,
    ) -> Path:
        log_dir = self.get_task_dir(task_id) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{stage}_{agent}.log"

        content = f"""=== AGENT LOG ===
TASK-ID: {task_id}
STAGE: {stage}
AGENT: {agent}
TIMESTAMP: {datetime.now().isoformat()}

--- STDOUT ---
{mask_sensitive_data(stdout)}

--- STDERR ---
{mask_sensitive_data(stderr)}
"""
        log_file.write_text(content, encoding="utf-8")
        return log_file
