"""Agent Adapters Package."""

from demo.orchestrator.adapters.base import BaseAgentAdapter
from demo.orchestrator.adapters.codex import CodexAgentAdapter
from demo.orchestrator.adapters.claude import ClaudeAgentAdapter
from demo.orchestrator.adapters.gemini import GeminiAgentAdapter
from demo.orchestrator.adapters.fake import FakeAgentAdapter


def get_adapter(agent_name: str, use_fake: bool = False, fake_options: dict = None) -> BaseAgentAdapter:
    """Factory to get the appropriate adapter."""
    if use_fake or agent_name.lower() == "fake":
        options = fake_options or {}
        return FakeAgentAdapter(name=agent_name, **options)

    name = agent_name.lower()
    if name == "codex":
        return CodexAgentAdapter()
    elif name == "claude":
        return ClaudeAgentAdapter()
    elif name == "gemini":
        return GeminiAgentAdapter()
    else:
        raise ValueError(f"Unknown agent adapter: {agent_name}")
