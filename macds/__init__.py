from macds.core import (
    # Contracts
    ContractInput,
    ContractOutput,
    Violation,
    Verdict,
    # Memory
    MemoryStore,
    MemoryScope,
    # Artifacts
    ArtifactStore,
    ArtifactType,
    # Evaluation
    EvaluationSystem,
    ScoreCategory,
    # Orchestrator
    Orchestrator,
    WorkflowStage,
    WorkflowResult,
    # Schema
    get_schema_loader,
)

from macds.agents import (
    BaseAgent,
    AgentConfig,
    AgentRegistry,
    ArchitectAgent,
    ProductAgent,
    ImplementationAgent,
    ReviewerAgent,
    BuildTestAgent,
    IntegratorAgent,
    InfraAgent,
)


__version__ = "1.0.0"
__author__ = "MACDS"


__all__ = [
    # Version
    "__version__",
    "__author__",
    # Core
    "ContractInput",
    "ContractOutput",
    "Violation",
    "Verdict",
    "MemoryStore",
    "MemoryScope",
    "ArtifactStore",
    "ArtifactType",
    "EvaluationSystem",
    "ScoreCategory",
    "Orchestrator",
    "WorkflowStage",
    "WorkflowResult",
    "get_schema_loader",
    # Agents
    "BaseAgent",
    "AgentConfig",
    "AgentRegistry",
    "ArchitectAgent",
    "ProductAgent",
    "ImplementationAgent",
    "ReviewerAgent",
    "BuildTestAgent",
    "IntegratorAgent",
    "InfraAgent",
]
