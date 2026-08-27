"""Tests for Coordinator Stage Plan JSON parsing and validation."""

import json
import unittest
from demo.orchestrator.coordinator import Coordinator
from demo.orchestrator.models import TaskPlan, StageConfig, TaskType, ExecutionMode


class TestCoordinator(unittest.TestCase):

    def setUp(self):
        self.coordinator = Coordinator(repo_root=".")

    def test_valid_json_parsing(self):
        sample_json = """{
            "task_id": "TASK-2026-08-27-001",
            "task_type": "RESEARCH",
            "execution": "PARALLEL",
            "output_artifact": "naver_blog_strategy.md",
            "goal": "Test goal",
            "scope": "Test scope",
            "completion_criteria": "Test criteria",
            "stages": [
                {
                    "name": "RESEARCH",
                    "execution": "PARALLEL",
                    "agents": ["claude", "codex", "gemini"],
                    "required": true
                },
                {
                    "name": "COMPARE",
                    "execution": "PIPELINE",
                    "agents": ["gemini"],
                    "required": true
                },
                {
                    "name": "FINAL",
                    "execution": "PIPELINE",
                    "agents": ["user"],
                    "required": true
                }
            ]
        }"""
        plan_dict = self.coordinator._parse_json_safely(sample_json)
        plan = TaskPlan.from_dict(plan_dict)
        plan.validate()
        self.assertEqual(plan.task_id, "TASK-2026-08-27-001")
        self.assertEqual(len(plan.stages), 3)
        self.assertEqual(plan.stages[0].name, "RESEARCH")
        self.assertEqual(plan.stages[0].agents, ["claude", "codex", "gemini"])

    def test_invalid_json_missing_stages(self):
        invalid_json = """{
            "task_id": "TASK-1",
            "task_type": "RESEARCH",
            "execution": "PARALLEL",
            "output_artifact": "art.md",
            "stages": []
        }"""
        plan_dict = self.coordinator._parse_json_safely(invalid_json)
        plan = TaskPlan.from_dict(plan_dict)
        with self.assertRaises(ValueError):
            plan.validate()

    def test_invalid_stage_name_rejected(self):
        invalid_json = """{
            "task_id": "TASK-1",
            "task_type": "RESEARCH",
            "execution": "PARALLEL",
            "output_artifact": "art.md",
            "stages": [
                {
                    "name": "INVALID_STAGE_NAME_XYZ",
                    "execution": "PIPELINE",
                    "agents": ["codex"],
                    "required": true
                }
            ]
        }"""
        plan_dict = self.coordinator._parse_json_safely(invalid_json)
        plan = TaskPlan.from_dict(plan_dict)
        with self.assertRaises(ValueError):
            plan.validate()

    def test_invalid_agent_name_rejected(self):
        invalid_json = """{
            "task_id": "TASK-1",
            "task_type": "RESEARCH",
            "execution": "PARALLEL",
            "output_artifact": "art.md",
            "stages": [
                {
                    "name": "RESEARCH",
                    "execution": "PIPELINE",
                    "agents": ["unknown_bot"],
                    "required": true
                }
            ]
        }"""
        plan_dict = self.coordinator._parse_json_safely(invalid_json)
        plan = TaskPlan.from_dict(plan_dict)
        with self.assertRaises(ValueError):
            plan.validate()

    def test_code_fenced_json_extraction(self):
        fenced_output = """Here is the plan:
```json
{
  "task_type": "RESEARCH",
  "execution": "PARALLEL",
  "output_artifact": "result.md",
  "stages": [
    {"name": "RESEARCH", "execution": "PARALLEL", "agents": ["codex"], "required": true}
  ]
}
```
Done."""
        plan_dict = self.coordinator._parse_json_safely(fenced_output)
        self.assertEqual(plan_dict["task_type"], "RESEARCH")


if __name__ == "__main__":
    unittest.main()
