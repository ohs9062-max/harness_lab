"""Tests for AI Agent CLI Adapters and Subprocess Safety."""

import unittest
from demo.orchestrator.adapters import (
    get_adapter,
    CodexAgentAdapter,
    ClaudeAgentAdapter,
    GeminiAgentAdapter,
    FakeAgentAdapter,
)
from demo.orchestrator.state import mask_sensitive_data


class TestAdapters(unittest.TestCase):

    def test_codex_command_structure(self):
        adapter = CodexAgentAdapter()
        cmd = adapter.build_command(prompt="Test prompt", cwd="/tmp/worktree")
        self.assertEqual(cmd[0], "codex")
        self.assertEqual(cmd[1], "exec")
        self.assertIn("-C", cmd)
        self.assertIn("/tmp/worktree", cmd)
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", cmd)
        self.assertEqual(cmd[-1], "Test prompt")

    def test_claude_command_structure(self):
        adapter = ClaudeAgentAdapter()
        cmd = adapter.build_command(prompt="Analyze code", cwd="/tmp/worktree")
        self.assertEqual(cmd[0], "claude")
        self.assertIn("-p", cmd)
        self.assertIn("Analyze code", cmd)
        self.assertIn("--permission-mode", cmd)
        self.assertIn("bypassPermissions", cmd)

    def test_gemini_command_structure(self):
        adapter = GeminiAgentAdapter()
        cmd = adapter.build_command(prompt="Review doc", cwd="/tmp/worktree")
        self.assertEqual(cmd[0], "gemini")
        self.assertIn("-p", cmd)
        self.assertIn("Review doc", cmd)
        self.assertIn("-y", cmd)
        self.assertIn("--approval-mode", cmd)
        self.assertIn("yolo", cmd)

    def test_fake_adapter_success_and_verdict(self):
        adapter = FakeAgentAdapter(name="fake_reviewer", force_success=True, review_verdict="PASS", create_files=False)
        res = adapter.run(prompt="Review plan", cwd=".", stage="REVIEW")
        self.assertTrue(res.success)
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(res.review_verdict, "PASS")

    def test_fake_adapter_failure(self):
        adapter = FakeAgentAdapter(name="fake_worker", force_success=False, exit_code=1, create_files=False)
        res = adapter.run(prompt="Do work", cwd=".", stage="RESEARCH")
        self.assertFalse(res.success)
        self.assertEqual(res.exit_code, 1)

    def test_sensitive_data_masking(self):
        raw_text = "Here is my api_key='sk-1234567890abcdefghijklmn' and token: ghp_1234567890abcdefghij"
        masked = mask_sensitive_data(raw_text)
        self.assertNotIn("sk-1234567890abcdefghijklmn", masked)
        self.assertNotIn("ghp_1234567890abcdefghij", masked)
        self.assertIn("[MASKED]", masked)


if __name__ == "__main__":
    unittest.main()
