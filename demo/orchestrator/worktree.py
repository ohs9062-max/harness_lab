"""Git worktree and local checkpoint operations for MODE A/B/C."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List


SAFE_TASK_ID = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass(frozen=True)
class WorktreeRef:
    label: str
    branch: str
    path: str
    base_commit: str


class WorktreeManager:
    """Create task worktrees and checkpoints without removing or publishing refs."""

    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root).resolve()
        self.worktrees_root = self.repo_root / ".harness" / "worktrees"

    def _git(self, args: List[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args], cwd=cwd or self.repo_root, capture_output=True,
            text=True, check=True, shell=False,
        )

    @staticmethod
    def _validate_task_id(task_id: str) -> None:
        if not SAFE_TASK_ID.fullmatch(task_id):
            raise ValueError(f"Unsafe TASK-ID for Git ref/path: {task_id}")

    def create(self, task_id: str, label: str, base_commit: str) -> WorktreeRef:
        self._validate_task_id(task_id)
        if label not in {"codex", "gemini", "pipeline"}:
            raise ValueError(f"Unsupported worktree label: {label}")
        branch = f"task/{task_id}/{label}"
        path = (self.worktrees_root / task_id / label).resolve()
        path.relative_to(self.worktrees_root.resolve())
        if path.exists():
            raise FileExistsError(f"Worktree path already exists: {path}")
        self._git(["check-ref-format", "--branch", branch])
        self._git(["cat-file", "-e", f"{base_commit}^{{commit}}"])
        path.parent.mkdir(parents=True, exist_ok=True)
        self._git(["worktree", "add", "-b", branch, str(path), base_commit])
        return WorktreeRef(label=label, branch=branch, path=str(path), base_commit=base_commit)

    def checkpoint(self, worktree_path: str, task_id: str, label: str) -> str:
        self._validate_task_id(task_id)
        worktree = Path(worktree_path).resolve()
        registered = {
            Path(item["worktree"]).resolve()
            for item in self._worktree_records()
            if item.get("worktree")
        }
        if worktree not in registered:
            raise ValueError(f"Checkpoint target is not a registered worktree: {worktree}")
        self._git(["add", "-A"], cwd=worktree)
        staged = self._git(["diff", "--cached", "--name-only"], cwd=worktree).stdout.strip()
        if not staged:
            raise RuntimeError(f"No changes available for {label} checkpoint")
        self._git(["commit", "-m", f"checkpoint({label}): {task_id}"], cwd=worktree)
        return self._git(["rev-parse", "HEAD"], cwd=worktree).stdout.strip()

    def _worktree_records(self) -> List[dict[str, str]]:
        records: List[dict[str, str]] = []
        current: dict[str, str] = {}
        for line in self._git(["worktree", "list", "--porcelain"]).stdout.splitlines():
            if not line:
                if current:
                    records.append(current)
                    current = {}
                continue
            key, _, value = line.partition(" ")
            current[key] = value
        if current:
            records.append(current)
        return records

    def diff(self, base_commit: str, checkpoint: str, worktree_path: str) -> str:
        result = self._git(
            ["diff", "--no-ext-diff", "--binary", f"{base_commit}...{checkpoint}"],
            cwd=Path(worktree_path).resolve(),
        )
        return result.stdout

    def changed_files(self, base_commit: str, checkpoint: str, worktree_path: str) -> List[str]:
        output = self._git(
            ["diff", "--name-only", f"{base_commit}...{checkpoint}"],
            cwd=Path(worktree_path).resolve(),
        ).stdout
        return [line for line in output.splitlines() if line]
