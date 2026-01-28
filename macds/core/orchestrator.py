from dataclasses import dataclass, field
from typing import Any, Optional, Callable
from enum import Enum
from datetime import datetime
import asyncio
import uuid

from macds.core.memory import MemoryStore, MemoryScope
from macds.core.evaluation import EvaluationSystem
from macds.core.artifacts import ArtifactStore
from macds.core.contracts import (
    ContractInput, ContractOutput, Verdict, ConflictRecord,
    RequirementsInput, ArchitectureInput, ImplementationInput,
    CodeReviewInput, BuildTestInput, IntegrationInput
)
from macds.agents.base import BaseAgent, AgentRegistry


class WorkflowStage(str, Enum):
    """Stages in the development workflow."""
    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
    IMPLEMENTATION = "implementation"
    REVIEW = "review"
    BUILD_TEST = "build_test"
    INTEGRATION = "integration"
    FINAL_APPROVAL = "final_approval"


class TaskStatus(str, Enum):
    """Status of a workflow task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    ESCALATED = "escalated"


@dataclass
class WorkflowTask:
    """A task in the workflow DAG."""
    id: str
    stage: WorkflowStage
    agent_name: str
    input_data: Optional[ContractInput] = None
    output_data: Optional[ContractOutput] = None
    status: TaskStatus = TaskStatus.PENDING
    dependencies: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "stage": self.stage.value,
            "agent": self.agent_name,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "error": self.error,
            "retry_count": self.retry_count
        }


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    workflow_id: str
    success: bool
    stages_completed: list[WorkflowStage]
    stages_failed: list[WorkflowStage] = field(default_factory=list)
    outputs: dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0
    escalations: list[dict] = field(default_factory=list)
    
    def get_summary(self) -> str:
        status = "succeeded" if self.success else "failed"
        return f"""Workflow {self.workflow_id} {status}
Completed: {', '.join(s.value for s in self.stages_completed)}
Failed: {', '.join(s.value for s in self.stages_failed)}
Duration: {self.duration_seconds:.1f}s
Escalations: {len(self.escalations)}"""


# Default workflow DAG
DEFAULT_WORKFLOW = [
    (WorkflowStage.REQUIREMENTS, "ProductAgent", []),
    (WorkflowStage.ARCHITECTURE, "ArchitectAgent", [WorkflowStage.REQUIREMENTS]),
    (WorkflowStage.IMPLEMENTATION, "ImplementationAgent", [WorkflowStage.ARCHITECTURE]),
    (WorkflowStage.REVIEW, "ReviewerAgent", [WorkflowStage.IMPLEMENTATION]),
    (WorkflowStage.BUILD_TEST, "BuildTestAgent", [WorkflowStage.REVIEW]),
    (WorkflowStage.INTEGRATION, "IntegratorAgent", [WorkflowStage.BUILD_TEST]),
    (WorkflowStage.FINAL_APPROVAL, "ArchitectAgent", [WorkflowStage.INTEGRATION])
]

# Failure routing rules
FAILURE_ROUTING = {
    WorkflowStage.REVIEW: WorkflowStage.IMPLEMENTATION,
    WorkflowStage.BUILD_TEST: WorkflowStage.IMPLEMENTATION,
    WorkflowStage.INTEGRATION: WorkflowStage.IMPLEMENTATION,
    WorkflowStage.FINAL_APPROVAL: WorkflowStage.ARCHITECTURE
}


class Orchestrator:
    """
    Workflow orchestrator for MACDS.
    
    Features:
    - DAG-based workflow execution
    - Failure routing
    - Escalation handling
    - State persistence
    """
    
    def __init__(
        self,
        memory_store: Optional[MemoryStore] = None,
        evaluation: Optional[EvaluationSystem] = None,
        artifact_store: Optional[ArtifactStore] = None,
        verbose: bool = False
    ):
        self.memory_store = memory_store or MemoryStore()
        self.evaluation = evaluation or EvaluationSystem()
        self.artifact_store = artifact_store or ArtifactStore()
        self.verbose = verbose
        
        self._agents: dict[str, BaseAgent] = {}
        self._active_workflows: dict[str, list[WorkflowTask]] = {}
        self._escalations: list[ConflictRecord] = []
        
        # Initialize agents
        self._init_agents()
    
    def _init_agents(self) -> None:
        """Initialize all agent instances."""
        from macds.agents.architect import ArchitectAgent
        from macds.agents.product import ProductAgent
        from macds.agents.implementation import ImplementationAgent
        from macds.agents.reviewer import ReviewerAgent
        from macds.agents.build_test import BuildTestAgent
        from macds.agents.integrator import IntegratorAgent
        from macds.agents.infra import InfraAgent
        
        agent_classes = [
            ArchitectAgent, ProductAgent, ImplementationAgent,
            ReviewerAgent, BuildTestAgent, IntegratorAgent, InfraAgent
        ]
        
        for agent_class in agent_classes:
            agent = agent_class(
                memory_store=self.memory_store,
                evaluation=self.evaluation,
                verbose=self.verbose
            )
            self._agents[agent.name] = agent
    
    def _log(self, message: str) -> None:
        """Log if verbose mode enabled."""
        if self.verbose:
            print(f"[Orchestrator] {message}")
    
    async def run_workflow(
        self,
        user_request: str,
        workflow: Optional[list] = None
    ) -> WorkflowResult:
        """
        Execute a complete development workflow.
        
        Args:
            user_request: Natural language request from user
            workflow: Custom workflow DAG (or use default)
        """
        workflow_id = str(uuid.uuid4())[:8]
        workflow_def = workflow or DEFAULT_WORKFLOW
        start_time = datetime.now()
        
        self._log(f"Starting workflow {workflow_id}")
        
        # Create tasks from workflow definition
        tasks: dict[WorkflowStage, WorkflowTask] = {}
        for stage, agent_name, deps in workflow_def:
            task = WorkflowTask(
                id=f"{workflow_id}-{stage.value}",
                stage=stage,
                agent_name=agent_name,
                dependencies=[f"{workflow_id}-{d.value}" for d in deps]
            )
            tasks[stage] = task
        
        self._active_workflows[workflow_id] = list(tasks.values())
        
        # Execute workflow
        completed_stages = []
        failed_stages = []
        outputs = {}
        context = {"user_request": user_request}
        
        for stage, agent_name, _ in workflow_def:
            task = tasks[stage]
            
            # Check dependencies
            deps_met = all(
                tasks[s].status == TaskStatus.COMPLETED
                for s, _, _ in workflow_def
                if f"{workflow_id}-{s.value}" in task.dependencies
            )
            
            if not deps_met:
                task.status = TaskStatus.BLOCKED
                failed_stages.append(stage)
                continue
            
            # Prepare input
            task.input_data = self._prepare_input(stage, context, outputs)
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            
            self._log(f"Executing {stage.value} with {agent_name}")
            
            try:
                agent = self._agents.get(agent_name)
                if not agent:
                    raise ValueError(f"Agent not found: {agent_name}")
                
                output = await agent.execute(task.input_data)
                task.output_data = output
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                
                completed_stages.append(stage)
                outputs[stage] = output
                
                # Update context for next stages
                self._update_context(stage, output, context)
                
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now()
                
                self._log(f"Stage {stage.value} failed: {e}")
                
                # Handle failure routing
                if not await self._handle_failure(stage, task, tasks, context):
                    failed_stages.append(stage)
                    break  # Stop workflow on unrecoverable failure
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Store workflow result in memory
        self.memory_store.store(
            content={
                "workflow_id": workflow_id,
                "success": len(failed_stages) == 0,
                "completed": [s.value for s in completed_stages],
                "failed": [s.value for s in failed_stages]
            },
            scope=MemoryScope.PROJECT,
            source="Orchestrator",
            tags=["workflow", "execution"]
        )
        
        return WorkflowResult(
            workflow_id=workflow_id,
            success=len(failed_stages) == 0,
            stages_completed=completed_stages,
            stages_failed=failed_stages,
            outputs={s.value: o for s, o in outputs.items()},
            duration_seconds=duration,
            escalations=[e.to_dict() for e in self._escalations]
        )
    
    def _prepare_input(
        self,
        stage: WorkflowStage,
        context: dict,
        outputs: dict
    ) -> ContractInput:
        """Prepare input contract for a stage."""
        request_id = str(uuid.uuid4())[:8]
        
        if stage == WorkflowStage.REQUIREMENTS:
            return RequirementsInput(
                request_id=request_id,
                user_request=context.get("user_request", ""),
                context=context.get("context"),
                constraints=context.get("constraints", [])
            )
        
        elif stage == WorkflowStage.ARCHITECTURE:
            req_output = outputs.get(WorkflowStage.REQUIREMENTS)
            return ArchitectureInput(
                request_id=request_id,
                requirements=req_output.requirements if req_output else [],
                constraints=req_output.constraints if req_output else []
            )
        
        elif stage == WorkflowStage.IMPLEMENTATION:
            arch_output = outputs.get(WorkflowStage.ARCHITECTURE)
            return ImplementationInput(
                request_id=request_id,
                task_description=context.get("user_request", ""),
                architecture={"components": arch_output.components} if arch_output else {},
                api_contract=arch_output.api_contracts[0] if arch_output and arch_output.api_contracts else None,
                coding_standards=context.get("coding_standards")
            )
        
        elif stage == WorkflowStage.REVIEW:
            impl_output = outputs.get(WorkflowStage.IMPLEMENTATION)
            arch_output = outputs.get(WorkflowStage.ARCHITECTURE)
            
            # Generate diff from implementation
            diff = ""
            if impl_output:
                for f in impl_output.files_created:
                    diff += f"+++ {f['path']}\n{f['content'][:500]}\n"
            
            return CodeReviewInput(
                request_id=request_id,
                code_diff=diff,
                architecture_constraints=arch_output.invariants if arch_output else [],
                coding_standards=context.get("coding_standards", ""),
                files_to_review=[f["path"] for f in (impl_output.files_created if impl_output else [])]
            )
        
        elif stage == WorkflowStage.BUILD_TEST:
            impl_output = outputs.get(WorkflowStage.IMPLEMENTATION)
            return BuildTestInput(
                request_id=request_id,
                source_files=[f["path"] for f in (impl_output.files_created if impl_output else [])],
                test_files=[]
            )
        
        elif stage == WorkflowStage.INTEGRATION:
            impl_output = outputs.get(WorkflowStage.IMPLEMENTATION)
            review_output = outputs.get(WorkflowStage.REVIEW)
            build_output = outputs.get(WorkflowStage.BUILD_TEST)
            
            return IntegrationInput(
                request_id=request_id,
                changes=impl_output.files_created if impl_output else [],
                review_approval=review_output.verdict == Verdict.PASS if review_output else False,
                build_approval=build_output.build_success if build_output else False
            )
        
        elif stage == WorkflowStage.FINAL_APPROVAL:
            return ArchitectureInput(
                request_id=request_id,
                requirements=context.get("requirements", []),
                existing_architecture=context.get("architecture_summary")
            )
        
        else:
            raise ValueError(f"Unknown stage: {stage}")
    
    def _update_context(self, stage: WorkflowStage, output: ContractOutput, context: dict) -> None:
        """Update context with stage output."""
        if stage == WorkflowStage.REQUIREMENTS:
            context["requirements"] = output.requirements
            context["constraints"] = output.constraints
        
        elif stage == WorkflowStage.ARCHITECTURE:
            context["architecture"] = output.components
            context["invariants"] = output.invariants
    
    async def _handle_failure(
        self,
        stage: WorkflowStage,
        task: WorkflowTask,
        tasks: dict,
        context: dict
    ) -> bool:
        """
        Handle stage failure with routing.
        
        Returns True if failure was handled, False if workflow should stop.
        """
        # Check retry limit
        if task.retry_count >= task.max_retries:
            self._log(f"Max retries exceeded for {stage.value}")
            return False
        
        # Get failure routing target
        target_stage = FAILURE_ROUTING.get(stage)
        if not target_stage:
            self._log(f"No failure routing for {stage.value}")
            return False
        
        self._log(f"Routing failure from {stage.value} to {target_stage.value}")
        
        # Reset target stage for re-execution
        if target_stage in tasks:
            target_task = tasks[target_stage]
            target_task.status = TaskStatus.PENDING
            target_task.retry_count += 1
            
            # Add failure context
            context["failure_context"] = {
                "failed_stage": stage.value,
                "error": task.error,
                "retry_count": target_task.retry_count
            }
            
            return True
        
        return False
    
    async def escalate_conflict(
        self,
        topic: str,
        agents_involved: list[str],
        evidence: list[dict]
    ) -> ConflictRecord:
        """Escalate a conflict for resolution."""
        # Determine decision owner based on authority
        max_authority = 0
        decision_owner = "ArchitectAgent"  # Default to highest
        
        for agent_name in agents_involved:
            agent = self._agents.get(agent_name)
            if agent and agent.authority_level > max_authority:
                max_authority = agent.authority_level
        
        # Decision owner should be higher authority than involved agents
        if max_authority < 10:
            decision_owner = "ArchitectAgent"
        
        conflict = ConflictRecord(
            conflict_id=str(uuid.uuid4())[:8],
            topic=topic,
            agents_involved=agents_involved,
            evidence=evidence,
            decision_owner=decision_owner
        )
        
        self._escalations.append(conflict)
        
        self._log(f"Conflict escalated to {decision_owner}: {topic}")
        
        return conflict
    
    async def resolve_conflict(self, conflict_id: str, resolution: dict) -> bool:
        """Resolve an escalated conflict."""
        for conflict in self._escalations:
            if conflict.conflict_id == conflict_id:
                conflict.resolution = resolution
                conflict.resolved_at = datetime.now()
                self._log(f"Conflict {conflict_id} resolved")
                return True
        return False
    
    def get_workflow_status(self, workflow_id: str) -> Optional[dict]:
        """Get status of a workflow."""
        tasks = self._active_workflows.get(workflow_id)
        if not tasks:
            return None
        
        return {
            "workflow_id": workflow_id,
            "tasks": [t.to_dict() for t in tasks],
            "progress": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED) / len(tasks)
        }
    
    def get_agent_scorecards(self) -> dict:
        """Get performance scorecards for all agents."""
        return self.evaluation.get_all_scores()
