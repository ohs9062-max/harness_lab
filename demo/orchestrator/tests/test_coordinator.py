"""Coordinator and plan contract tests."""

import unittest

from demo.orchestrator.coordinator import Coordinator
from demo.orchestrator.models import TaskPlan


class TestCoordinator(unittest.TestCase):
    def setUp(self):
        self.coordinator = Coordinator(".")

    def test_deterministic_development_pipeline(self):
        plan = self.coordinator.create_deterministic_plan("TASK-TEST-001", "코드를 구현해")
        self.assertEqual(plan.task_type, "DEVELOPMENT")
        self.assertEqual([stage.name for stage in plan.stages], ["DESIGN", "IMPLEMENT", "CHECK", "REVIEW", "FINAL"])
        self.assertEqual(plan.stages[1].access, "WRITE")
        self.assertNotEqual(plan.stages[1].agents, plan.stages[3].agents)

    def test_deterministic_mixed_pipeline(self):
        plan = self.coordinator.create_deterministic_plan("TASK-TEST-002", "분석해서 코드에 통합해")
        self.assertEqual(plan.task_type, "MIXED")
        self.assertEqual(plan.stages[0].execution, "PARALLEL")
        plan.validate()

    def test_code_fenced_json_extraction(self):
        parsed = self.coordinator._parse_json_safely('text\n```json\n{"task_type":"RESEARCH"}\n```')
        self.assertEqual(parsed["task_type"], "RESEARCH")

    def test_parallel_write_rejected(self):
        plan = TaskPlan.from_dict({
            "task_id": "TASK-X", "task_type": "DEVELOPMENT", "mode": "C", "output_artifact": "",
            "stages": [
                {"name": "IMPLEMENT", "execution": "PARALLEL", "agents": ["codex"], "access": "WRITE"},
                {"name": "FINAL", "execution": "PIPELINE", "agents": ["system"], "access": "SYSTEM"},
            ],
        })
        with self.assertRaises(ValueError):
            plan.validate()

    def test_self_review_rejected(self):
        plan = TaskPlan.from_dict({
            "task_id": "TASK-X", "task_type": "DEVELOPMENT", "mode": "C", "output_artifact": "",
            "stages": [
                {"name": "IMPLEMENT", "execution": "PIPELINE", "agents": ["codex"], "access": "WRITE"},
                {"name": "REVIEW", "execution": "PIPELINE", "agents": ["codex"], "access": "READ_ONLY"},
                {"name": "FINAL", "execution": "PIPELINE", "agents": ["system"], "access": "SYSTEM"},
            ],
        })
        with self.assertRaises(ValueError):
            plan.validate()

    def test_review_requires_immediately_preceding_check(self):
        plan = TaskPlan.from_dict({
            "task_id": "TASK-X", "task_type": "DEVELOPMENT", "mode": "C", "output_artifact": "",
            "stages": [
                {"name": "IMPLEMENT", "execution": "PIPELINE", "agents": ["codex"], "access": "WRITE"},
                {"name": "REVIEW", "execution": "PIPELINE", "agents": ["gemini"], "access": "READ_ONLY"},
                {"name": "FINAL", "execution": "PIPELINE", "agents": ["system"], "access": "SYSTEM"},
            ],
        })
        with self.assertRaisesRegex(ValueError, "immediately before REVIEW"):
            plan.validate()

    def test_reviewer_cannot_be_fix_agent(self):
        plan = self.coordinator.create_deterministic_plan("TASK-X", "코드를 구현해")
        plan.fix_agent = "gemini"
        with self.assertRaisesRegex(ValueError, "fix_agent"):
            plan.validate()


if __name__ == "__main__":
    unittest.main()
