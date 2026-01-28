# MACDS Architecture

## Overview

MACDS (Multi-Agent Coding Development System) is a distributed agent system designed for automated software engineering. The architecture follows a hierarchical authority model where specialized agents collaborate through contract-driven interfaces to complete development tasks.

## System Components

### Core Infrastructure

```
+------------------+     +------------------+     +------------------+
|   Orchestrator   |---->|   Agent Runtime  |---->|   Execution Env  |
+------------------+     +------------------+     +------------------+
        |                        |                        |
        v                        v                        v
+------------------+     +------------------+     +------------------+
|  Artifact Store  |     |  Memory System   |     |   Evaluation     |
+------------------+     +------------------+     +------------------+
```

### Component Descriptions

#### Orchestrator

The orchestrator manages workflow execution using a DAG (Directed Acyclic Graph) model.

Responsibilities:
- Parse user requests into workflow tasks
- Schedule agent execution based on dependencies
- Route failures to appropriate agents
- Handle escalations between agents
- Track workflow state and progress

Key Classes:
- `Orchestrator` - Main workflow engine
- `WorkflowTask` - Individual task in the DAG
- `WorkflowResult` - Execution result container

#### Agent Runtime

The agent runtime provides the execution environment for all agents.

Responsibilities:
- Load agent configurations
- Manage agent lifecycle
- Validate contract inputs and outputs
- Integrate with memory and evaluation systems

Key Classes:
- `BaseAgent` - Abstract base for all agents
- `AgentConfig` - Agent configuration
- `AgentRegistry` - Agent type registry

#### Memory System

The memory system provides persistent storage with time-based decay.

Memory Scopes:
| Scope | Purpose | Decay Rate |
|-------|---------|------------|
| Working | Current task context | Fast (1 hour) |
| Project | Project-specific knowledge | Slow (7 days) |
| Skill | Learned patterns | Very slow (30 days) |
| Failure | Past mistakes | Medium (24 hours) |

Key Classes:
- `MemoryStore` - Persistent storage
- `MemoryEntry` - Individual memory item
- `AgentMemory` - Per-agent memory interface

#### Artifact Store

Git-backed versioned storage for development artifacts.

Mandatory Artifacts:
- `REQUIREMENTS.md` - Product requirements
- `ARCHITECTURE.md` - System design
- `DESIGN_DECISIONS.log` - Decision record
- `API_CONTRACTS.yaml` - Interface contracts
- `CODING_STANDARDS.md` - Code standards
- `RISK_REGISTER.md` - Risk tracking

Key Classes:
- `ArtifactStore` - Storage manager
- `Artifact` - Artifact with versions
- `ArtifactVersion` - Single version

#### Evaluation System

Tracks agent performance and adjusts autonomy.

Score Categories:
- Correctness - Output quality
- Efficiency - Resource usage
- Compliance - Standard adherence
- Cost - API usage
- Stability - Consistency

Key Classes:
- `EvaluationSystem` - Score manager
- `AgentScorecard` - Per-agent scores
- `ExecutionFeedback` - Build/test results

#### Contract System

Enforces typed input/output for all agent communication.

Contract Types:
- RequirementsContract
- ArchitectureContract
- ImplementationContract
- CodeReviewContract
- BuildTestContract
- IntegrationContract

Key Classes:
- `ContractInput` - Base input type
- `ContractOutput` - Base output type
- `ContractRegistry` - Type registry

## Data Flow

### Standard Workflow

```
User Request
     |
     v
+-----------+
| Product   |---> Requirements
+-----------+
     |
     v
+-----------+
| Architect |---> Architecture, Invariants
+-----------+
     |
     v
+-----------+
| Implement |---> Source Code
+-----------+
     |
     v
+-----------+
| Reviewer  |---> Review, Violations
+-----------+
     |
     v
+-----------+
| BuildTest |---> Build Results, Metrics
+-----------+
     |
     v
+-----------+
| Integrator|---> Merged Changes
+-----------+
     |
     v
+-----------+
| Architect |---> Final Approval
+-----------+
```

### Failure Routing

When a stage fails, the workflow routes to the appropriate agent:

| Failed Stage | Routes To |
|-------------|-----------|
| Review | ImplementationAgent |
| Build/Test | ImplementationAgent |
| Integration | ImplementationAgent |
| Final Approval | ArchitectAgent |

## Storage Layout

```
.macds/
├── memory/
│   └── memories.json
├── artifacts/
│   ├── .git/
│   ├── REQUIREMENTS.md
│   ├── ARCHITECTURE.md
│   └── ...
└── evaluation/
    └── scorecards.json
```

## Extension Points

### Custom Agents

Extend `BaseAgent` and implement:
- `system_prompt` - Agent instructions
- `input_contract` - Input type
- `output_contract` - Output type
- `_execute_impl()` - Core logic

### Custom Workflows

Define workflow as list of tuples:
```python
workflow = [
    (WorkflowStage.REQUIREMENTS, "ProductAgent", []),
    (WorkflowStage.ARCHITECTURE, "ArchitectAgent", [WorkflowStage.REQUIREMENTS]),
    ...
]
```

### Schema Extensions

Add new schemas to:
- `schemas/contracts/` - New contract types
- `schemas/artifacts/` - New artifact types
