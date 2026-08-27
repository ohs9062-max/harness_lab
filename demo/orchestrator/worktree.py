"""Git Worktree Isolation Manager for Orchestrator V1."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple


class WorktreeManager:
    """Safely manages isolated git worktrees for parallel agents without destructive operations."""

    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root).resolve()

    def get_current_head(self) -> str:
        """Get current HEAD commit hash."""
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()

    def branch_exists(self, branch_name: str) -> bool:
        """Check if a local git branch exists."""
        res = subprocess.run(
            ["git", "show-ref", "--verify", f"refs/heads/{branch_name}"],
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
        )
        return res.returncode == 0

    def create_isolated_worktree(
        self,
        task_id: str,
        agent_name: str,
        base_commit: str,
        dry_run: bool = False,
    ) -> Tuple[str, str]:
        """
        Create a new git worktree branching from base_commit.
        Branch: task/<task_id>/<agent_name>
        Path: .harness/worktrees/<task_id>/<agent_name>
        Returns (branch_name, absolute_worktree_path).
        """
        branch_name = f"task/{task_id}/{agent_name.lower()}"
        worktree_dir = self.repo_root / ".harness" / "worktrees" / task_id / agent_name.lower()
        worktree_path = str(worktree_dir.resolve())

        if dry_run:
            return branch_name, worktree_path

        worktree_dir.parent.mkdir(parents=True, exist_ok=True)

        # If worktree already exists, return existing path
        if worktree_dir.exists():
            return branch_name, worktree_path

        # If branch already exists, attach to it; otherwise create with -b
        if self.branch_exists(branch_name):
            cmd = ["git", "worktree", "add", worktree_path, branch_name]
        else:
            cmd = ["git", "worktree", "add", "-b", branch_name, worktree_path, base_commit]

        subprocess.run(
            cmd,
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
        return branch_name, worktree_path

    def create_local_checkpoint_commit(
        self,
        worktree_path: str,
        message: str,
        dry_run: bool = False,
    ) -> Optional[str]:
        """
        Create a local checkpoint commit in the worktree.
        Strictly NO push and NO merge.
        """
        if dry_run:
            return "dry-run-checkpoint-hash"

        path = Path(worktree_path)
        if not path.exists():
            return None

        # Stage changes in worktree (ignoring nested .harness if any)
        # Stage shared/ and artifacts/ and any modified repo files
        subprocess.run(["git", "add", "-A", "--", ":!.harness"], cwd=str(path), capture_output=True, text=True)

        # Check if there are staged changes
        diff_res = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=str(path),
            capture_output=True,
        )
        # returncode == 1 means staged changes exist
        if diff_res.returncode == 0:
            # No changes to commit
            head_res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(path),
                capture_output=True,
                text=True,
                check=True,
            )
            return head_res.stdout.strip()

        # Commit locally
        subprocess.run(["git", "commit", "-m", message], cwd=str(path), check=True, capture_output=True)

        head_res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(path),
            capture_output=True,
            text=True,
            check=True,
        )
        return head_res.stdout.strip()
