"""Atomic runtime state, handoff, event, and masked log persistence."""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from demo.orchestrator.models import AgentExecutionResult, RuntimeState

SENSITIVE_PATTERNS = [
    re.compile(r"(?i)\b(authorization\s*[:=]\s*['\"]?(?:bearer\s+)?)([^\s'\"]{6,})"),
    re.compile(r"(?i)\b(bearer\s+)([A-Za-z0-9._~+/-]{8,})"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?([^\s'\"]{6,})"),
    re.compile(r"\b(sk-[A-Za-z0-9_-]{12,}|ghp_[A-Za-z0-9]{12,}|xox[baprs]-[A-Za-z0-9-]{10,})\b"),
]
SENSITIVE_KEY = re.compile(r"(?i)(api[_-]?key|secret|token|password|authorization)")
SAFE_TASK_ID = re.compile(r"^[A-Za-z0-9._-]+$")


def mask_sensitive_data(text: str) -> str:
    sanitized = text or ""
    for pattern in SENSITIVE_PATTERNS:
        if pattern.groups >= 2:
            sanitized = pattern.sub(r"\1[MASKED]", sanitized)
        else:
            sanitized = pattern.sub("[MASKED]", sanitized)
    return sanitized


def mask_sensitive_value(value: Any, key: str = "") -> Any:
    """Mask values recursively before JSON serialization, preserving JSON structure."""
    if key and SENSITIVE_KEY.search(key):
        return "[MASKED]"
    if isinstance(value, dict):
        return {item_key: mask_sensitive_value(item_value, str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [mask_sensitive_value(item) for item in value]
    if isinstance(value, tuple):
        return [mask_sensitive_value(item) for item in value]
    if isinstance(value, str):
        return mask_sensitive_data(value)
    return value


class StateManager:
    def __init__(self, repo_root: str, max_log_chars: int = 200_000):
        self.repo_root = Path(repo_root).resolve()
        self.runs_root = self.repo_root / ".harness" / "runs"
        self.max_log_chars = max_log_chars

    def get_task_dir(self, task_id: str) -> Path:
        if not SAFE_TASK_ID.fullmatch(task_id):
            raise ValueError(f"Unsafe TASK-ID for runtime path: {task_id}")
        task_dir = (self.runs_root / task_id).resolve()
        task_dir.relative_to(self.runs_root.resolve())
        task_dir.mkdir(parents=True, exist_ok=True)
        return task_dir

    @staticmethod
    def _atomic_json(path: Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
            os.replace(temp_name, path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def save_state(self, state: RuntimeState) -> Path:
        now = datetime.now(timezone.utc).astimezone().isoformat()
        state.updated_at = now
        state.created_at = state.created_at or now
        path = self.get_task_dir(state.task_id) / "state.json"
        self._atomic_json(path, mask_sensitive_value(state.to_dict()))
        return path

    def load_state(self, task_id: str) -> Optional[RuntimeState]:
        path = self.runs_root / task_id / "state.json"
        if not path.exists():
            return None
        return RuntimeState(**json.loads(path.read_text(encoding="utf-8")))

    def append_event(self, task_id: str, event_type: str, **payload: Any) -> Path:
        path = self.get_task_dir(task_id) / "events.jsonl"
        event = {
            "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
            "type": event_type,
            **payload,
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(mask_sensitive_value(event), ensure_ascii=False) + "\n")
        return path

    def write_result(self, task_id: str, stage_key: str, result: AgentExecutionResult) -> Path:
        output_dir = self.get_task_dir(task_id) / "outputs" / stage_key
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{result.agent}.md"
        stdout = mask_sensitive_data(result.stdout)
        stderr = mask_sensitive_data(result.stderr)
        content = (
            f"# {result.stage} — {result.agent}\n\n"
            f"- success: {result.success}\n- exit_code: {result.exit_code}\n"
            f"- duration_sec: {result.duration_sec:.3f}\n"
            f"- review_verdict: {result.review_verdict or 'N/A'}\n\n"
            f"## Output\n\n{stdout}\n"
        )
        if stderr:
            content += f"\n## Stderr\n\n```text\n{stderr}\n```\n"
        if len(content) > self.max_log_chars:
            content = content[: self.max_log_chars] + "\n\n[OUTPUT TRUNCATED]\n"
            result.output_truncated = True
        path.write_text(content, encoding="utf-8")
        result.output_file = str(path.relative_to(self.repo_root))
        return path

    def write_handoff(self, task_id: str, state: RuntimeState) -> Path:
        path = self.get_task_dir(task_id) / "handoff.json"
        data = {
            "task_id": task_id,
            "current_stage": state.current_stage,
            "status": state.status,
            "outputs": [item for item in state.handoffs],
            "checks": state.checks,
            "changed_files": state.changed_files,
            "review_cycles": state.review_cycles,
            "blocker": state.blocker,
            "mode": state.mode,
            "worktrees": state.worktrees,
            "worker_branches": state.worker_branches,
            "checkpoints": state.checkpoints,
            "worker_status": state.worker_status,
            "cross_reviews": state.cross_reviews,
            "responses": state.responses,
            "compare_path": state.compare_path,
            "user_selection": state.user_selection,
            "merge_status": state.merge_status,
            "active_worktree": state.active_worktree,
            "active_branch": state.active_branch,
            "relay": state.relay,
            "git_discrepancies": state.git_discrepancies,
        }
        self._atomic_json(path, mask_sensitive_value(data))
        return path

    def write_runtime_markdown(self, task_id: str, relative_path: str, content: str) -> Path:
        path = (self.get_task_dir(task_id) / relative_path).resolve()
        path.relative_to(self.get_task_dir(task_id).resolve())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(mask_sensitive_data(content), encoding="utf-8")
        return path

    def write_selection(self, task_id: str, selection: Dict[str, Any]) -> Path:
        path = self.get_task_dir(task_id) / "selection.json"
        self._atomic_json(path, mask_sensitive_value(selection))
        return path
