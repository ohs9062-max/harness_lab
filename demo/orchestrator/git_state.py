"""Read-only Git preflight and change snapshots."""

from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class GitPreflight:
    root: str
    branch: str
    head: str
    dirty: bool
    status: List[str]
    worktrees: List[Dict[str, str]]


class GitInspector:
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root).resolve()

    def _git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args], cwd=self.repo_root, capture_output=True, text=True,
            check=check, shell=False,
        )

    def preflight(self) -> GitPreflight:
        root = self._git("rev-parse", "--show-toplevel").stdout.strip()
        if Path(root).resolve() != self.repo_root:
            raise ValueError(f"repo_root must be the Git root: {root}")
        branch = self._git("branch", "--show-current").stdout.strip() or "DETACHED"
        head = self._git("rev-parse", "HEAD").stdout.strip()
        lines = [line for line in self._git("status", "--porcelain=v1").stdout.splitlines() if line]
        return GitPreflight(
            root=root, branch=branch, head=head, dirty=bool(lines), status=lines,
            worktrees=self.list_worktrees(),
        )

    def list_worktrees(self) -> List[Dict[str, str]]:
        records: List[Dict[str, str]] = []
        current: Dict[str, str] = {}
        for line in self._git("worktree", "list", "--porcelain").stdout.splitlines():
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

    def snapshot(self) -> Dict[str, str]:
        """Hash tracked diffs and untracked file contents without mutating Git."""
        snapshot: Dict[str, str] = {}
        entries = self._git(
            "status", "--porcelain=v1", "-z", "--untracked-files=all"
        ).stdout.split("\0")
        index = 0
        paths: List[str] = []
        while index < len(entries):
            entry = entries[index]
            index += 1
            if not entry:
                continue
            status_code = entry[:2]
            path_text = entry[3:]
            paths.append(path_text)
            if ("R" in status_code or "C" in status_code) and index < len(entries):
                old_path = entries[index]
                index += 1
                if old_path:
                    paths.append(old_path)
        for path_text in paths:
            path = self.repo_root / path_text
            digest = hashlib.sha256()
            if path.is_symlink():
                try:
                    digest.update(os.readlink(path).encode("utf-8", errors="surrogateescape"))
                except OSError:
                    digest.update(b"UNREADABLE")
            elif path.is_file():
                try:
                    digest.update(path.read_bytes())
                except OSError:
                    digest.update(b"UNREADABLE")
            else:
                digest.update(b"MISSING")
            snapshot[path_text] = digest.hexdigest()
        return snapshot

    def changed_files(self) -> List[str]:
        return sorted(self.snapshot())

    def relay_evidence(self) -> Dict[str, object]:
        """Return the real Git facts a MODE B receiver must inspect."""
        preflight = self.preflight()
        return {
            "branch": preflight.branch,
            "head": preflight.head,
            "status": preflight.status,
            "recent_log": self._git("log", "--oneline", "-5").stdout.splitlines(),
            "diff_stat": self._git("diff", "--stat").stdout.splitlines(),
            "changed_files": self.changed_files(),
        }
