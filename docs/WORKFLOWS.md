# MACDS Workflows

## Overview

MACDS uses a DAG (Directed Acyclic Graph) based workflow engine to orchestrate agent execution. Workflows define the sequence of agent operations, their dependencies, and failure handling.

## Default Workflow

The default workflow implements a complete software development lifecycle:

```
Stage 1: Requirements (ProductAgent)
    |
    v
Stage 2: Architecture (ArchitectAgent)
    |
    v
Stage 3: Implementation (ImplementationAgent)
    |
    v
Stage 4: Review (ReviewerAgent)
    |
    v
Stage 5: Build/Test (BuildTestAgent)
    |
    v
Stage 6: Integration (IntegratorAgent)
    |
    v
Stage 7: Final Approval (ArchitectAgent)
```

## Workflow Stages

### Stage 1: Requirements

**Agent:** ProductAgent (Authority: 9)

**Input:**
- User request (natural language)
- Optional context
- Known constraints

**Output:**
- Structured requirements list
- Acceptance criteria
- Identified risks

### Stage 2: Architecture

**Agent:** ArchitectAgent (Authority: 10)

**Input:**
- Requirements from Stage 1
- Existing architecture (if any)

**Output:**
- Component definitions
- System invariants
- Design decisions
- API contracts

### Stage 3: Implementation

**Agent:** ImplementationAgent (Authority: 5)

**Input:**
- Task description
- Architecture from Stage 2
- API contracts
- Coding standards

**Output:**
- Created files
- Modified files
- Implementation notes

### Stage 4: Review

**Agent:** ReviewerAgent (Authority: 7)

**Input:**
- Code diff from Stage 3
- Architecture constraints
- Coding standards

**Output:**
- Review verdict (pass/fail/needs_revision)
- Violations list
- Security concerns
- Quality score

### Stage 5: Build/Test

**Agent:** BuildTestAgent (Authority: 8)

**Input:**
- Source files
- Test files
- Build/test commands

**Output:**
- Build success status
- Test results
- Coverage metrics
- Security scan results

### Stage 6: Integration

**Agent:** IntegratorAgent (Authority: 8)

**Input:**
- Changes to integrate
- Review approval
- Build approval

**Output:**
- Merged files
- Conflicts (if any)
- Commit SHA

### Stage 7: Final Approval

**Agent:** ArchitectAgent (Authority: 10)

**Input:**
- All previous outputs
- Architecture compliance check

**Output:**
- Final approval status
- Any remaining concerns

## Failure Routing

When a stage fails, the workflow automatically routes to an appropriate agent for remediation:

| Failed Stage | Routed To | Reason |
|--------------|-----------|--------|
| Review | ImplementationAgent | Fix code issues |
| Build/Test | ImplementationAgent | Fix build errors |
| Integration | ImplementationAgent | Resolve conflicts |
| Final Approval | ArchitectAgent | Revise architecture |

### Retry Logic

- Maximum retries: 3 per stage
- Context preserved between retries
- Failure information passed to receiving agent

## Custom Workflows

### Quick Workflow

Skips review and testing for rapid prototyping:

```python
quick_workflow = [
    (WorkflowStage.REQUIREMENTS, "ProductAgent", []),
    (WorkflowStage.ARCHITECTURE, "ArchitectAgent", [WorkflowStage.REQUIREMENTS]),
    (WorkflowStage.IMPLEMENTATION, "ImplementationAgent", [WorkflowStage.ARCHITECTURE]),
]
```

### Review-Only Workflow

For code review without full implementation:

```python
review_workflow = [
    (WorkflowStage.REVIEW, "ReviewerAgent", []),
]
```

### Test-Only Workflow

For running tests on existing code:

```python
test_workflow = [
    (WorkflowStage.BUILD_TEST, "BuildTestAgent", []),
]
```

## Workflow Configuration

### Defining a Custom Workflow

```python
from macds.core.orchestrator import Orchestrator, WorkflowStage

custom_workflow = [
    (WorkflowStage.REQUIREMENTS, "ProductAgent", []),
    (WorkflowStage.IMPLEMENTATION, "ImplementationAgent", [WorkflowStage.REQUIREMENTS]),
    (WorkflowStage.BUILD_TEST, "BuildTestAgent", [WorkflowStage.IMPLEMENTATION]),
]

orchestrator = Orchestrator()
result = await orchestrator.run_workflow(
    "Build a calculator",
    workflow=custom_workflow
)
```

## Parallel Execution

Stages with independent dependencies can execute in parallel:

```
Requirements ----+
                 |
                 v
            Architecture
                 |
        +-------+-------+
        |               |
        v               v
   Implementation    Infra Setup
        |               |
        +-------+-------+
                |
                v
             Review
```

## Workflow Result

Each workflow execution returns a `WorkflowResult`:

```python
@dataclass
class WorkflowResult:
    workflow_id: str
    success: bool
    stages_completed: list[WorkflowStage]
    stages_failed: list[WorkflowStage]
    outputs: dict[str, Any]
    duration_seconds: float
    escalations: list[dict]
```

## Monitoring

### Workflow Status

```bash
# Check running workflow
macds status

# View workflow history
macds history
```

### Progress Tracking

The orchestrator provides real-time progress:
- Current stage
- Completion percentage
- Estimated time remaining
- Agent scorecard updates
