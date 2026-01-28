import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import json
from unittest.mock import Mock, patch, AsyncMock


# ==================== Fixtures ====================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def memory_store(temp_dir):
    """Create a memory store for testing."""
    from macds.core.memory import MemoryStore
    return MemoryStore(storage_path=temp_dir / "memory")


@pytest.fixture
def evaluation_system(temp_dir):
    """Create an evaluation system for testing."""
    from macds.core.evaluation import EvaluationSystem
    return EvaluationSystem(storage_path=temp_dir / "evaluation")


@pytest.fixture
def artifact_store(temp_dir):
    """Create an artifact store for testing."""
    from macds.core.artifacts import ArtifactStore
    return ArtifactStore(project_root=temp_dir)


# ==================== Contract Tests ====================

class TestContracts:
    """Test contract system."""
    
    def test_requirements_output_validation(self):
        """Test requirements output validation."""
        from macds.core.contracts import RequirementsOutput
        
        # Valid output
        valid = RequirementsOutput(
            request_id="test-001",
            requirements=[{"id": "REQ-001", "description": "Test"}],
            acceptance_criteria=["AC-001"],
            constraints=[]
        )
        violations = valid.validate()
        assert len(violations) == 0
        
        # Invalid output - empty requirements
        invalid = RequirementsOutput(
            request_id="test-002",
            requirements=[],
            acceptance_criteria=[],
            constraints=[]
        )
        violations = invalid.validate()
        assert len(violations) > 0
        assert any(v.rule_id == "REQ-001" for v in violations)
    
    def test_architecture_output_validation(self):
        """Test architecture output validation."""
        from macds.core.contracts import ArchitectureOutput
        
        valid = ArchitectureOutput(
            request_id="test-001",
            components=[{"name": "core", "responsibility": "test"}],
            invariants=["No circular deps"],
            design_decisions=[],
            api_contracts=[]
        )
        violations = valid.validate()
        assert len(violations) == 0
    
    def test_violation_to_dict(self):
        """Test violation serialization."""
        from macds.core.contracts import Violation
        
        v = Violation(
            rule_id="TEST-001",
            severity="error",
            message="Test message",
            location="line 10",
            suggested_fix="Fix it"
        )
        
        d = v.to_dict()
        assert d["rule_id"] == "TEST-001"
        assert d["severity"] == "error"
        assert d["location"] == "line 10"


# ==================== Memory Tests ====================

class TestMemory:
    """Test memory system."""
    
    def test_store_and_retrieve(self, memory_store):
        """Test basic store and retrieve."""
        from macds.core.memory import MemoryScope
        
        entry_id = memory_store.store(
            content={"key": "value"},
            scope=MemoryScope.WORKING,
            source="TestAgent"
        )
        
        assert entry_id is not None
        
        results = memory_store.retrieve(entry_id=entry_id)
        assert len(results) == 1
        assert results[0].content == {"key": "value"}
    
    def test_memory_decay(self, memory_store):
        """Test memory decay calculation."""
        from macds.core.memory import MemoryEntry, MemoryScope, DecayPolicy
        
        # Fast decay entry
        entry = MemoryEntry(
            id="test",
            content="test",
            scope=MemoryScope.WORKING,
            source="test",
            decay_policy=DecayPolicy.FAST
        )
        
        initial_strength = entry.get_current_strength()
        assert initial_strength == 1.0
        
        # Simulate time passing
        entry.last_accessed = datetime.now() - timedelta(hours=2)
        decayed_strength = entry.get_current_strength()
        assert decayed_strength < initial_strength
    
    def test_memory_search(self, memory_store):
        """Test memory search."""
        from macds.core.memory import MemoryScope
        
        memory_store.store(
            content={"message": "hello world"},
            scope=MemoryScope.PROJECT,
            source="TestAgent"
        )
        
        results = memory_store.search("hello", scope=MemoryScope.PROJECT)
        assert len(results) >= 1
    
    def test_agent_memory_interface(self, memory_store):
        """Test agent memory interface."""
        from macds.core.memory import AgentMemory, MemoryScope
        
        agent_memory = AgentMemory("TestAgent", memory_store)
        
        # Remember something
        entry_id = agent_memory.remember(
            content={"test": "data"},
            scope=MemoryScope.SKILL
        )
        
        # Recall it
        results = agent_memory.recall(scope=MemoryScope.SKILL)
        assert len(results) >= 1


# ==================== Evaluation Tests ====================

class TestEvaluation:
    """Test evaluation system."""
    
    def test_scorecard_creation(self, evaluation_system):
        """Test scorecard creation."""
        scorecard = evaluation_system.get_scorecard("TestAgent")
        assert scorecard.agent_name == "TestAgent"
        assert scorecard.total_tasks == 0
    
    def test_record_task_result(self, evaluation_system):
        """Test recording task results."""
        from macds.core.evaluation import ScoreCategory
        
        evaluation_system.record_task_result(
            agent_name="TestAgent",
            success=True,
            scores={ScoreCategory.CORRECTNESS: 90.0}
        )
        
        scorecard = evaluation_system.get_scorecard("TestAgent")
        assert scorecard.total_tasks == 1
        assert scorecard.successful_tasks == 1
    
    def test_autonomy_adjustment(self, evaluation_system):
        """Test autonomy adjustment based on performance."""
        from macds.core.evaluation import ScoreCategory
        
        # Record multiple successful tasks
        for _ in range(5):
            evaluation_system.record_task_result(
                agent_name="GoodAgent",
                success=True,
                scores={
                    ScoreCategory.CORRECTNESS: 95.0,
                    ScoreCategory.COMPLIANCE: 95.0
                }
            )
        
        scorecard = evaluation_system.get_scorecard("GoodAgent")
        # Autonomy should be high after good performance
        assert scorecard.autonomy_level >= 1.0


# ==================== Artifact Tests ====================

class TestArtifacts:
    """Test artifact store."""
    
    def test_create_artifact(self, artifact_store):
        """Test creating an artifact."""
        from macds.core.artifacts import ArtifactType
        
        artifact = artifact_store.create(
            name="test.md",
            content="# Test",
            artifact_type=ArtifactType.DOCUMENTATION,
            created_by="TestAgent"
        )
        
        assert artifact.name == "test.md"
        assert artifact.content == "# Test"
    
    def test_update_artifact(self, artifact_store):
        """Test updating an artifact."""
        from macds.core.artifacts import ArtifactType
        
        artifact_store.create(
            name="test.md",
            content="# Test v1",
            artifact_type=ArtifactType.DOCUMENTATION,
            created_by="TestAgent"
        )
        
        updated = artifact_store.update(
            name="test.md",
            content="# Test v2",
            updated_by="TestAgent"
        )
        
        assert updated.content == "# Test v2"
        assert len(updated.versions) == 2
    
    def test_ownership_enforcement(self, artifact_store):
        """Test artifact ownership enforcement."""
        from macds.core.artifacts import ArtifactType
        
        artifact_store.create(
            name="ARCHITECTURE.md",
            content="# Arch",
            artifact_type=ArtifactType.ARCHITECTURE,
            created_by="ArchitectAgent"
        )
        
        # Different agent should not be able to modify
        with pytest.raises(PermissionError):
            artifact_store.update(
                name="ARCHITECTURE.md",
                content="# Modified",
                updated_by="ImplementationAgent"
            )
    
    def test_init_mandatory_artifacts(self, artifact_store):
        """Test initializing mandatory artifacts."""
        created = artifact_store.init_mandatory_artifacts()
        assert len(created) > 0
        assert "REQUIREMENTS.md" in created


# ==================== Agent Tests ====================

class TestAgents:
    """Test agent implementations."""
    
    @pytest.mark.asyncio
    async def test_architect_agent(self, memory_store, evaluation_system):
        """Test ArchitectAgent execution."""
        from macds.agents.architect import ArchitectAgent
        from macds.core.contracts import ArchitectureInput
        
        agent = ArchitectAgent(
            memory_store=memory_store,
            evaluation=evaluation_system
        )
        
        input_data = ArchitectureInput(
            request_id="test-001",
            requirements=[{"id": "REQ-001", "description": "Build an API"}]
        )
        
        output = await agent.execute(input_data)
        
        assert output is not None
        assert len(output.components) > 0
        assert len(output.invariants) > 0
    
    @pytest.mark.asyncio
    async def test_product_agent(self, memory_store, evaluation_system):
        """Test ProductAgent execution."""
        from macds.agents.product import ProductAgent
        from macds.core.contracts import RequirementsInput
        
        agent = ProductAgent(
            memory_store=memory_store,
            evaluation=evaluation_system
        )
        
        input_data = RequirementsInput(
            request_id="test-001",
            user_request="Create a user authentication system"
        )
        
        output = await agent.execute(input_data)
        
        assert output is not None
        assert len(output.requirements) > 0
        assert len(output.acceptance_criteria) > 0
    
    @pytest.mark.asyncio
    async def test_reviewer_agent(self, memory_store, evaluation_system):
        """Test ReviewerAgent execution."""
        from macds.agents.reviewer import ReviewerAgent
        from macds.core.contracts import CodeReviewInput, Verdict
        
        agent = ReviewerAgent(
            memory_store=memory_store,
            evaluation=evaluation_system
        )
        
        input_data = CodeReviewInput(
            request_id="test-001",
            code_diff="+def hello():\n+    print('hello')",
            architecture_constraints=[],
            coding_standards="Use logging instead of print"
        )
        
        output = await agent.execute(input_data)
        
        assert output is not None
        assert output.verdict in [Verdict.PASS, Verdict.FAIL, Verdict.NEEDS_REVISION]
    
    def test_authority_levels(self):
        """Test agent authority levels are correct."""
        from macds.agents.architect import ArchitectAgent
        from macds.agents.product import ProductAgent
        from macds.agents.implementation import ImplementationAgent
        from macds.agents.reviewer import ReviewerAgent
        
        assert ArchitectAgent.authority_level == 10
        assert ProductAgent.authority_level == 9
        assert ReviewerAgent.authority_level == 7
        assert ImplementationAgent.authority_level == 5


# ==================== Orchestrator Tests ====================

class TestOrchestrator:
    """Test orchestrator and workflows."""
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self, temp_dir):
        """Test basic workflow execution."""
        from macds.core.orchestrator import Orchestrator, WorkflowStage
        from macds.core.memory import MemoryStore
        from macds.core.evaluation import EvaluationSystem
        from macds.core.artifacts import ArtifactStore
        
        orchestrator = Orchestrator(
            memory_store=MemoryStore(temp_dir / "memory"),
            evaluation=EvaluationSystem(temp_dir / "evaluation"),
            artifact_store=ArtifactStore(temp_dir),
            verbose=False
        )
        
        # Run minimal workflow
        result = await orchestrator.run_workflow(
            "Create a simple calculator",
            workflow=[
                (WorkflowStage.REQUIREMENTS, "ProductAgent", []),
                (WorkflowStage.ARCHITECTURE, "ArchitectAgent", [WorkflowStage.REQUIREMENTS])
            ]
        )
        
        assert result is not None
        assert len(result.stages_completed) > 0
    
    @pytest.mark.asyncio
    async def test_escalation(self, temp_dir):
        """Test conflict escalation."""
        from macds.core.orchestrator import Orchestrator
        from macds.core.memory import MemoryStore
        from macds.core.evaluation import EvaluationSystem
        from macds.core.artifacts import ArtifactStore
        
        orchestrator = Orchestrator(
            memory_store=MemoryStore(temp_dir / "memory"),
            evaluation=EvaluationSystem(temp_dir / "evaluation"),
            artifact_store=ArtifactStore(temp_dir),
            verbose=False
        )
        
        conflict = await orchestrator.escalate_conflict(
            topic="Design disagreement",
            agents_involved=["ProductAgent", "ImplementationAgent"],
            evidence=[{"detail": "Test"}]
        )
        
        assert conflict is not None
        assert conflict.decision_owner == "ArchitectAgent"


# ==================== Integration Tests ====================

class TestIntegration:
    """Integration tests for the complete system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_quick_workflow(self, temp_dir):
        """Test end-to-end workflow execution."""
        from macds.core.orchestrator import Orchestrator, WorkflowStage
        from macds.core.memory import MemoryStore
        from macds.core.evaluation import EvaluationSystem
        from macds.core.artifacts import ArtifactStore
        
        orchestrator = Orchestrator(
            memory_store=MemoryStore(temp_dir / "memory"),
            evaluation=EvaluationSystem(temp_dir / "evaluation"),
            artifact_store=ArtifactStore(temp_dir),
            verbose=False
        )
        
        result = await orchestrator.run_workflow(
            "Create a hello world function",
            workflow=[
                (WorkflowStage.REQUIREMENTS, "ProductAgent", []),
            ]
        )
        
        assert result.success
        assert WorkflowStage.REQUIREMENTS in result.stages_completed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
