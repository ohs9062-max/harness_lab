"""CLI mode and resume tests without external AI calls."""

import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from demo.orchestrator.cli import create_parser, main


class TestCli(unittest.TestCase):
    def test_mode_is_machine_readable(self):
        options = create_parser().parse_args(["goal", "--mode", "A"])
        self.assertEqual(options.mode, "A")

    def test_mode_a_cli_stops_then_resumes_selection(self):
        directory = tempfile.mkdtemp(prefix="harness_cli_")
        root = Path(directory)
        try:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Harness Test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "harness@example.invalid"], cwd=root, check=True)
            (root / ".gitignore").write_text(".harness/\n")
            (root / "README.md").write_text("fixture\n")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=root, check=True)
            with contextlib.redirect_stdout(io.StringIO()):
                first = main([
                    "로그인 구현", "--repo", str(root), "--mode", "A", "--task-id", "TASK-CLI-A",
                    "--execute", "--fake-agents", "--no-auto-checks",
                ])
                second = main([
                    "--repo", str(root), "--mode", "A", "--resume", "TASK-CLI-A",
                    "--selection", "SELECT_GEMINI", "--execute", "--fake-agents", "--no-auto-checks",
                ])
            self.assertEqual((first, second), (0, 0))
            state = json.loads((root / ".harness/runs/TASK-CLI-A/state.json").read_text())
            self.assertEqual(state["status"], "DONE")
            self.assertEqual(state["user_selection"], "SELECT_GEMINI")
        finally:
            shutil.rmtree(directory, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
