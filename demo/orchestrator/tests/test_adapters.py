"""CLI permission, verdict, and log-sanitization tests."""

import unittest

from demo.orchestrator.adapters import ClaudeAgentAdapter, CodexAgentAdapter, GeminiAgentAdapter
from demo.orchestrator.adapters.base import BaseAgentAdapter
from demo.orchestrator.state import mask_sensitive_data


class TestAdapters(unittest.TestCase):
    def test_codex_access_is_sandboxed(self):
        adapter = CodexAgentAdapter()
        read = adapter.build_command("inspect", "/tmp/worktree", "READ_ONLY")
        write = adapter.build_command("implement", "/tmp/worktree", "WRITE")
        self.assertIn("read-only", read)
        self.assertIn("--approve-for-me", write)
        self.assertNotIn("--approve-for-me", read)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", read + write)

    def test_claude_access_is_role_scoped(self):
        adapter = ClaudeAgentAdapter()
        read = adapter.build_command("design", "/tmp/worktree", "READ_ONLY")
        write = adapter.build_command("fix", "/tmp/worktree", "WRITE")
        self.assertIn("plan", read)
        self.assertIn("acceptEdits", write)
        self.assertNotIn("bypassPermissions", read + write)

    def test_gemini_access_is_role_scoped(self):
        adapter = GeminiAgentAdapter()
        read = adapter.build_command("review", "/tmp/worktree", "READ_ONLY")
        write = adapter.build_command("edit", "/tmp/worktree", "WRITE")
        self.assertIn("plan", read)
        self.assertIn("auto_edit", write)
        self.assertNotIn("yolo", read + write)

    def test_review_verdict_is_explicit_and_unambiguous(self):
        self.assertEqual(BaseAgentAdapter._extract_review_verdict("finding\nVERDICT: PASS"), "PASS")
        self.assertIsNone(BaseAgentAdapter._extract_review_verdict("Looks fine"))
        self.assertEqual(BaseAgentAdapter._extract_review_verdict("Previous: VERDICT: FIX_REQUIRED\nVERDICT: PASS"), "PASS")
        self.assertIsNone(BaseAgentAdapter._extract_review_verdict("VERDICT: PASS\nwarning after verdict"))

    def test_sensitive_data_masking(self):
        raw = "api_key='sk-1234567890abcdefghijklmn' token: ghp_1234567890abcdefghij"
        masked = mask_sensitive_data(raw)
        self.assertNotIn("sk-1234567890abcdefghijklmn", masked)
        self.assertNotIn("ghp_1234567890abcdefghij", masked)
        self.assertIn("[MASKED]", masked)

    def test_authorization_bearer_masks_the_actual_token(self):
        masked = mask_sensitive_data("Authorization: Bearer mysecrettoken12345678")
        self.assertNotIn("mysecrettoken12345678", masked)
        self.assertIn("[MASKED]", masked)


if __name__ == "__main__":
    unittest.main()
