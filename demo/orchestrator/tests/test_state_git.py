"""Persistence safety and Git snapshot tests."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from demo.orchestrator.git_state import GitInspector
from demo.orchestrator.checks import CheckRunner
from demo.orchestrator.models import RuntimeState
from demo.orchestrator.state import StateManager


class TestStateAndGit(unittest.TestCase):
    def test_check_discovery_ignores_runtime_worktrees(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tests").mkdir()
            (root / "tests/test_real.py").write_text("pass\n")
            (root / ".harness/worktrees/T/tests").mkdir(parents=True)
            (root / ".harness/worktrees/T/tests/test_duplicate.py").write_text("pass\n")
            commands = CheckRunner(str(root)).discover()
            starts = [command[command.index("-s") + 1] for command in commands if "-s" in command]
            self.assertEqual(starts, ["tests"])

    def test_runtime_directory_does_not_make_repository_dirty(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / "README.md").write_text("tracked\n")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "-q", "-m", "initial"], cwd=root, check=True,
            )
            (root / ".harness/runs/TASK-X").mkdir(parents=True)
            (root / ".harness/runs/TASK-X/state.json").write_text("{}")
            self.assertFalse(GitInspector(str(root)).preflight().dirty)

    def test_event_json_remains_valid_when_secret_keys_are_masked(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = StateManager(directory)
            path = manager.append_event("TASK-X", "test", payload={"api_key": "secret123456"})
            event = json.loads(path.read_text())
            self.assertEqual(event["payload"]["api_key"], "[MASKED]")

    def test_state_masks_agent_stdout_and_stderr(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = StateManager(directory)
            state = RuntimeState(
                task_id="TASK-X", status="RUNNING", user_request="safe",
                agent_results={"001": [{"stdout": "Bearer abcdefghijklmnop", "stderr": "token=secret12345"}]},
            )
            path = manager.save_state(state)
            stored = path.read_text()
            self.assertNotIn("abcdefghijklmnop", stored)
            self.assertNotIn("secret12345", stored)
            json.loads(stored)

    def test_handoff_masks_nested_check_output(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = StateManager(directory)
            state = RuntimeState(
                task_id="TASK-X", status="RUNNING", user_request="safe",
                checks=[{"stdout": "Authorization: Bearer abcdefghijklmnop"}],
            )
            path = manager.write_handoff(state.task_id, state)
            stored = path.read_text()
            self.assertNotIn("abcdefghijklmnop", stored)
            json.loads(stored)

    def test_snapshot_handles_nul_delimited_rename(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
            (root / "old_name.txt").write_text("data")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=root, check=True)
            subprocess.run(["git", "mv", "old_name.txt", "new_name.txt"], cwd=root, check=True)
            snapshot = GitInspector(str(root)).snapshot()
            self.assertIn("new_name.txt", snapshot)
            self.assertIn("old_name.txt", snapshot)

    def test_snapshot_expands_untracked_directories_and_does_not_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / "target.txt").write_text("first")
            subprocess.run(["git", "add", "target.txt"], cwd=root, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "-q", "-m", "initial"],
                cwd=root, check=True,
            )
            (root / "nested").mkdir()
            (root / "nested" / "item.txt").write_text("item")
            (root / "link.txt").symlink_to("target.txt")
            before = GitInspector(str(root)).snapshot()
            self.assertIn("nested/item.txt", before)
            link_digest = before["link.txt"]

            (root / "target.txt").write_text("second")
            after = GitInspector(str(root)).snapshot()
            self.assertEqual(after["link.txt"], link_digest)


if __name__ == "__main__":
    unittest.main()
