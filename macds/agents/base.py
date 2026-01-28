from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, TypeVar, Generic
from datetime import datetime
import asyncio
import os
import sys

# Add parent path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from macds.core.contracts import (
    ContractInput, ContractOutput, ContractViolationError,
    Violation, Verdict, ContractRegistry
)
from macds.core.memory import MemoryStore, AgentMemory, MemoryScope
from macds.core.evaluation import EvaluationSystem, ScoreCategory


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    name: str
    authority_level: int  # 1-10, higher = more authority
    model: str = "anthropic/claude-3.5-sonnet"
    temperature: float = 0.7
    max_tokens: int = 4096
    requires_approval_above: int = 0  # Authority threshold for auto-approval
    owned_artifacts: list[str] = field(default_factory=list)


T_Input = TypeVar("T_Input", bound=ContractInput)
T_Output = TypeVar("T_Output", bound=ContractOutput)


class BaseAgent(ABC, Generic[T_Input, T_Output]):
    """
    Base class for MACDS agents.
    
    Features:
    - Authority-based permissions
    - Contract-driven I/O
    - Memory integration
    - Evaluation feedback
    """
    
    # Class-level defaults (override in subclasses)
    name: str = "base"
    authority_level: int = 1
    description: str = "Base agent"
    owned_artifacts: list[str] = []
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        memory_store: Optional[MemoryStore] = None,
        evaluation: Optional[EvaluationSystem] = None,
        verbose: bool = False
    ):
        self.config = config or AgentConfig(
            name=self.name,
            authority_level=self.authority_level,
            owned_artifacts=self.owned_artifacts
        )
        
        self._memory_store = memory_store or MemoryStore()
        self._memory = AgentMemory(self.config.name, self._memory_store)
        self._evaluation = evaluation or EvaluationSystem()
        self._verbose = verbose
        
        # Track current task
        self._current_task_id: Optional[str] = None
        self._task_start_time: Optional[datetime] = None
    
    @property
    def memory(self) -> AgentMemory:
        """Get agent's memory interface."""
        return self._memory
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass
    
    @property
    @abstractmethod
    def input_contract(self) -> type:
        """Get the input contract type."""
        pass
    
    @property
    @abstractmethod
    def output_contract(self) -> type:
        """Get the output contract type."""
        pass
    
    def can_override(self, other_authority: int) -> bool:
        """Check if this agent can override another's decision."""
        return self.config.authority_level > other_authority
    
    def requires_approval_from(self, decision_authority: int) -> bool:
        """Check if this agent needs approval for a decision level."""
        return decision_authority > self.config.authority_level
    
    def validate_input(self, input_data: T_Input) -> list[Violation]:
        """Validate input contract."""
        violations = input_data.validate()
        if violations:
            self._log(f"Input validation found {len(violations)} violations")
        return violations
    
    def validate_output(self, output_data: T_Output) -> list[Violation]:
        """Validate output contract."""
        violations = output_data.validate()
        if violations:
            self._log(f"Output validation found {len(violations)} violations")
        return violations
    
    async def execute(self, input_data: T_Input) -> T_Output:
        """
        Execute the agent's task.
        
        Validates contracts before and after execution.
        """
        self._current_task_id = input_data.request_id
        self._task_start_time = datetime.now()
        
        # Validate input
        input_violations = self.validate_input(input_data)
        if any(v.severity == "error" for v in input_violations):
            raise ContractViolationError(
                f"Input contract violation: {[v.message for v in input_violations]}"
            )
        
        # Store task in working memory
        self._memory.remember(
            content={"task_id": input_data.request_id, "input_type": type(input_data).__name__},
            scope=MemoryScope.WORKING,
            tags=["task", "current"]
        )
        
        try:
            # Execute the actual work
            self._log(f"Executing task {input_data.request_id}")
            output = await self._execute_impl(input_data)
            
            # Validate output
            output_violations = self.validate_output(output)
            if any(v.severity == "error" for v in output_violations):
                self._record_failure("output_validation_failed")
                raise ContractViolationError(
                    f"Output contract violation: {[v.message for v in output_violations]}"
                )
            
            # Record success
            self._record_success()
            
            return output
            
        except Exception as e:
            self._record_failure(str(e))
            raise
    
    @abstractmethod
    async def _execute_impl(self, input_data: T_Input) -> T_Output:
        """
        Implementation of the agent's task.
        
        Override this in subclasses.
        """
        pass
    
    def _record_success(self) -> None:
        """Record successful task completion."""
        if self._task_start_time:
            duration = (datetime.now() - self._task_start_time).total_seconds()
            self._evaluation.record_task_result(
                agent_name=self.config.name,
                success=True,
                scores={
                    ScoreCategory.CORRECTNESS: 100.0,
                    ScoreCategory.EFFICIENCY: min(100, 100 - (duration / 60) * 10)
                },
                task_id=self._current_task_id
            )
    
    def _record_failure(self, reason: str) -> None:
        """Record task failure."""
        self._evaluation.record_task_result(
            agent_name=self.config.name,
            success=False,
            scores={ScoreCategory.CORRECTNESS: 0.0},
            task_id=self._current_task_id
        )
        
        # Store failure in memory for learning
        self._memory.learn_from_failure({
            "task_id": self._current_task_id,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
    
    def _log(self, message: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self._verbose:
            print(f"[{self.config.name}] {message}")
    
    async def escalate(
        self,
        issue: str,
        target_authority: int,
        evidence: list[dict]
    ) -> dict:
        """
        Escalate an issue to a higher authority.
        
        Returns escalation record for handling by orchestrator.
        """
        from macds.core.contracts import ConflictRecord
        import uuid
        
        conflict = ConflictRecord(
            conflict_id=str(uuid.uuid4()),
            topic=issue,
            agents_involved=[self.config.name],
            evidence=evidence,
            decision_owner=f"authority_{target_authority}"
        )
        
        self._memory.remember(
            content=conflict.to_dict(),
            scope=MemoryScope.PROJECT,
            tags=["escalation", "conflict"]
        )
        
        scorecard = self._evaluation.get_scorecard(self.config.name)
        scorecard.record_escalation()
        
        return conflict.to_dict()
    
    def recall_relevant_memories(
        self,
        query: str,
        scope: Optional[MemoryScope] = None,
        limit: int = 10
    ) -> list[dict]:
        """Recall memories relevant to a query."""
        entries = self._memory.store.search(query, scope=scope, limit=limit)
        return [e.to_dict() for e in entries]
    
    def get_scorecard(self) -> dict:
        """Get this agent's performance scorecard."""
        return self._evaluation.get_scorecard(self.config.name).to_dict()


# ==================== Agent Registry ====================

class AgentRegistry:
    """Registry for agent types and instances."""
    
    _agent_types: dict[str, type] = {}
    _instances: dict[str, BaseAgent] = {}
    
    @classmethod
    def register(cls, agent_class: type) -> None:
        """Register an agent class."""
        cls._agent_types[agent_class.name] = agent_class
    
    @classmethod
    def get_type(cls, name: str) -> Optional[type]:
        """Get an agent class by name."""
        return cls._agent_types.get(name)
    
    @classmethod
    def create(
        cls,
        name: str,
        memory_store: Optional[MemoryStore] = None,
        evaluation: Optional[EvaluationSystem] = None,
        **kwargs
    ) -> Optional[BaseAgent]:
        """Create an agent instance."""
        agent_class = cls._agent_types.get(name)
        if agent_class:
            instance = agent_class(
                memory_store=memory_store,
                evaluation=evaluation,
                **kwargs
            )
            cls._instances[name] = instance
            return instance
        return None
    
    @classmethod
    def get_instance(cls, name: str) -> Optional[BaseAgent]:
        """Get an existing agent instance."""
        return cls._instances.get(name)
    
    @classmethod
    def list_agents(cls) -> list[dict]:
        """List all registered agent types."""
        return [
            {
                "name": name,
                "authority_level": agent_class.authority_level,
                "description": agent_class.description
            }
            for name, agent_class in cls._agent_types.items()
        ]
    
    @classmethod
    def get_by_authority(cls, min_authority: int) -> list[str]:
        """Get agents with at least the specified authority."""
        return [
            name for name, agent_class in cls._agent_types.items()
            if agent_class.authority_level >= min_authority
        ]
