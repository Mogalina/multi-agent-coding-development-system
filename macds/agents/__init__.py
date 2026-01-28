"""
MACDS Agents.

This module exports all specialized agents for the Multi-Agent Coding Development System.
"""

from macds.agents.base import (
    BaseAgent,
    AgentConfig,
    AgentRegistry,
)

from macds.agents.architect import ArchitectAgent
from macds.agents.product import ProductAgent
from macds.agents.implementation import ImplementationAgent
from macds.agents.reviewer import ReviewerAgent
from macds.agents.build_test import BuildTestAgent
from macds.agents.integrator import IntegratorAgent
from macds.agents.infra import InfraAgent


# Register all agents
AgentRegistry.register(ArchitectAgent)
AgentRegistry.register(ProductAgent)
AgentRegistry.register(ImplementationAgent)
AgentRegistry.register(ReviewerAgent)
AgentRegistry.register(BuildTestAgent)
AgentRegistry.register(IntegratorAgent)
AgentRegistry.register(InfraAgent)


__all__ = [
    # Base
    "BaseAgent",
    "AgentConfig",
    "AgentRegistry",
    # Specialized Agents
    "ArchitectAgent",
    "ProductAgent",
    "ImplementationAgent",
    "ReviewerAgent",
    "BuildTestAgent",
    "IntegratorAgent",
    "InfraAgent",
]
