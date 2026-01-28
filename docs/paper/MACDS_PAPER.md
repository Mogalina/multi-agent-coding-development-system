# MACDS: A Hierarchical Multi-Agent System for Automated Software Engineering with Contract-Driven Interfaces and Execution-Grounded Feedback

## Abstract

This paper presents MACDS (Multi-Agent Coding Development System), a novel architecture for automated software engineering that addresses critical limitations in existing multi-agent approaches. MACDS introduces a hierarchical authority model enabling principled conflict resolution, contract-driven interfaces ensuring structured agent communication, memory systems with time-based decay for context management, and execution-grounded feedback loops for continuous agent improvement. We describe the system architecture comprising seven specialized agents with authority levels ranging from 5 to 10, a DAG-based workflow engine with automatic failure routing, and an evaluation system that adjusts agent autonomy based on measured performance. Our design ensures architectural invariants are maintained throughout the development lifecycle while supporting the complete software engineering pipeline from requirements through integration.

## 1. Introduction

The application of Large Language Models (LLMs) to software engineering automation has progressed from single-agent code completion to multi-agent systems capable of collaborative development. However, existing approaches exhibit significant limitations: lack of formal conflict resolution mechanisms, unstructured inter-agent communication, absence of execution-grounded feedback loops, and inability to maintain architectural invariants across development iterations.

This paper introduces MACDS, a multi-agent system designed to address these fundamental challenges. Our contributions are as follows:

1. A hierarchical authority model where agents possess numeric authority levels (1-10) enabling deterministic conflict resolution
2. Contract-driven interfaces with YAML-defined schemas ensuring validated, structured agent communication
3. A memory system with four scopes (Working, Project, Skill, Failure) and configurable decay policies
4. An evaluation system providing execution-grounded feedback that adjusts agent autonomy based on measured outcomes
5. A DAG-based workflow engine with automatic failure routing and escalation handling

The remainder of this paper is organized as follows: Section 2 reviews related work, Section 3 presents the system architecture, Section 4 describes the contract system, Section 5 covers the evaluation and memory subsystems, Section 6 discusses the workflow engine, and Section 7 presents conclusions and future work.

## 2. Related Work

### 2.1 Single-Agent Code Assistants

GitHub Copilot and similar systems employ single LLM agents for code completion. While effective for local code suggestions, these systems cannot maintain project-level context or perform architectural reasoning (Chen et al., 2021).

### 2.2 Multi-Agent Software Engineering

MetaGPT (Hong et al., 2023) introduced role-based multi-agent collaboration for software development, assigning agents to product manager, architect, and engineer roles. ChatDev (Qian et al., 2023) extended this with a software company simulation. However, both systems use linear pipelines without authority hierarchies or formal conflict resolution.

AutoGen (Wu et al., 2023) provides a framework for multi-agent conversations with flexible topologies but lacks software engineering-specific constructs such as contract enforcement or architectural invariant tracking.

### 2.3 Autonomous Software Engineering Agents

SWE-Agent (Yang et al., 2024) demonstrated effective repository-level reasoning with a custom agent-computer interface. Aider focuses on pair programming with Git integration. These systems typically employ single agents without the multi-agent collaboration required for complex projects.

### 2.4 Gaps in Existing Approaches

Our analysis identifies six critical gaps:

1. **Authority and Conflict Resolution**: No formal mechanism for resolving agent disagreements
2. **Structured Communication**: Untyped, unvalidated inter-agent messages
3. **Execution Feedback**: Limited integration of build and test results into agent improvement
4. **Architectural Enforcement**: No explicit invariant tracking or enforcement
5. **Context Management**: Static memory without decay or scope differentiation
6. **Failure Handling**: Linear pipelines without dynamic routing

## 3. System Architecture

### 3.1 Overview

MACDS comprises five core components:

1. **Orchestrator**: DAG-based workflow engine managing agent execution
2. **Agent Runtime**: Execution environment with contract validation
3. **Artifact Store**: Git-backed versioned storage with ownership enforcement
4. **Memory System**: Scoped storage with decay policies
5. **Evaluation System**: Performance tracking with autonomy adjustment

### 3.2 Agent Hierarchy

We define seven specialized agents with authority levels:

| Agent | Authority | Responsibility |
|-------|-----------|----------------|
| ArchitectAgent | 10 | System design, invariant enforcement |
| ProductAgent | 9 | Requirements, acceptance criteria |
| BuildTestAgent | 8 | Build execution, testing |
| IntegratorAgent | 8 | Change integration, merging |
| ReviewerAgent | 7 | Code review, standards enforcement |
| InfraAgent | 6 | CI/CD, infrastructure |
| ImplementationAgent | 5 | Code generation |

The authority level determines conflict resolution: when agents disagree, the higher authority agent's decision prevails. Agents at equivalent levels escalate to the next higher authority.

### 3.3 Component Interaction

Agent interaction follows a structured pattern:

```
Orchestrator -> Agent(n) -> ContractOutput -> Validation -> 
Memory -> Evaluation -> Orchestrator -> Agent(n+1)
```

Each agent receives validated ContractInput, produces ContractOutput validated against defined schemas, and has results recorded in both memory and evaluation systems.

## 4. Contract System

### 4.1 Design Principles

The contract system ensures structured, validated communication:

1. All agent inputs and outputs conform to typed contracts
2. Contracts are defined in YAML schemas with validation rules
3. Validation occurs at both input and output boundaries
4. Violations are captured with severity levels and suggested fixes

### 4.2 Contract Structure

Each contract defines:

```yaml
name: architecture
version: "1.0"
input:
  type: object
  required: [request_id, requirements]
  properties:
    request_id: {type: string}
    requirements: {type: array}
output:
  type: object
  required: [request_id, components, invariants]
  properties:
    components: {type: array, items: {...}}
    invariants: {type: array, items: {type: string}}
validation_rules:
  - id: ARCH-001
    severity: error
    condition: "len(components) > 0"
    message: "Must define at least one component"
```

### 4.3 Violation Handling

When validation fails, violations are captured:

```python
@dataclass
class Violation:
    rule_id: str      # Unique identifier
    severity: str     # error, warning, info
    message: str      # Human-readable description
    location: str     # Location in output
    suggested_fix: str
```

Violations with severity "error" prevent workflow progression; warnings are logged but allow continuation.

## 5. Evaluation and Memory Systems

### 5.1 Memory Architecture

The memory system provides four scopes with distinct decay policies:

| Scope | Purpose | Decay Half-Life |
|-------|---------|-----------------|
| Working | Current task context | 1 hour |
| Project | Project-specific knowledge | 7 days |
| Skill | Learned patterns | 30 days |
| Failure | Past mistakes | 24 hours |

Memory entries maintain strength scores calculated as:

```
strength = initial_confidence * exp(-decay_rate * hours_elapsed)
```

Entries below a threshold (default 0.1) are pruned during cleanup.

### 5.2 Evaluation System

Agent performance is tracked across categories:

1. **Correctness**: Output quality and accuracy
2. **Efficiency**: Resource utilization
3. **Compliance**: Standard adherence
4. **Cost**: API usage
5. **Stability**: Output consistency

### 5.3 Autonomy Adjustment

Agent autonomy is adjusted based on cumulative performance:

```python
autonomy_level = base_level * weighted_average(scores) / 100

if autonomy_level < threshold:
    # Require human approval for decisions
elif autonomy_level > high_threshold:
    # Grant expanded decision authority
```

This creates an execution-grounded feedback loop where measured outcomes directly influence agent behavior.

## 6. Workflow Engine

### 6.1 DAG-Based Execution

Workflows are defined as directed acyclic graphs:

```python
workflow = [
    (Stage.REQUIREMENTS, "ProductAgent", []),
    (Stage.ARCHITECTURE, "ArchitectAgent", [Stage.REQUIREMENTS]),
    (Stage.IMPLEMENTATION, "ImplementationAgent", [Stage.ARCHITECTURE]),
    # ...
]
```

Dependencies determine execution order; independent stages may execute in parallel.

### 6.2 Failure Routing

When a stage fails, the workflow routes to an appropriate agent for remediation:

| Failed Stage | Routes To |
|-------------|-----------|
| Review | ImplementationAgent |
| Build/Test | ImplementationAgent |
| Integration | ImplementationAgent |
| Final Approval | ArchitectAgent |

Routing preserves failure context, enabling targeted remediation.

### 6.3 Escalation Handling

Conflicts trigger escalation:

```python
conflict = orchestrator.escalate_conflict(
    topic="Design disagreement",
    agents_involved=["ProductAgent", "ImplementationAgent"],
    evidence=[{...}]
)
# Routes to higher authority (ArchitectAgent)
```

The highest-authority agent not involved in the conflict makes the final decision.

## 7. Artifact Management

### 7.1 Mandatory Artifacts

MACDS maintains six mandatory artifacts:

1. REQUIREMENTS.md - Product requirements
2. ARCHITECTURE.md - System design
3. DESIGN_DECISIONS.log - Decision record
4. API_CONTRACTS.yaml - Interface definitions
5. CODING_STANDARDS.md - Code standards
6. RISK_REGISTER.md - Risk tracking

### 7.2 Ownership Enforcement

Each artifact has a designated owner agent:

| Artifact | Owner |
|----------|-------|
| REQUIREMENTS.md | ProductAgent |
| ARCHITECTURE.md | ArchitectAgent |
| RISK_REGISTER.md | ProductAgent |

Only the owner agent may modify an artifact, preventing inconsistent updates.

### 7.3 Versioning

Artifacts are stored in a Git-backed system providing:

- Full version history
- Diff between versions
- Rollback capability
- Audit trail

## 8. Implementation Details

### 8.1 Technology Stack

MACDS is implemented in Python 3.10+ with the following dependencies:

- Typer for CLI interface
- Rich for terminal output
- PyYAML for schema processing
- httpx for async HTTP
- pytest for testing

### 8.2 Deployment

The system supports multiple deployment modes:

- Local installation via pip
- Docker container
- Docker Compose for development

### 8.3 LLM Integration

The architecture is model-agnostic, supporting:

- OpenAI models
- Anthropic Claude
- OpenRouter aggregation

Each agent may use a different model based on task requirements.

## 9. Conclusions and Future Work

### 9.1 Summary

MACDS addresses fundamental limitations in existing multi-agent software engineering systems through:

1. Hierarchical authority enabling deterministic conflict resolution
2. Contract-driven interfaces ensuring structured communication
3. Scoped memory with decay for context management
4. Execution-grounded feedback adjusting agent autonomy
5. DAG workflows with automatic failure routing

### 9.2 Limitations

Current limitations include:

- Simulated LLM integration (requires API keys for production use)
- Limited evaluation on large-scale projects
- No formal verification of generated code

### 9.3 Future Work

Planned extensions include:

1. Self-improvement capabilities for prompt refinement
2. Integration with formal verification tools
3. Cross-repository learning
4. Human-in-the-loop optimization interfaces

## References

Chen, M., et al. (2021). Evaluating Large Language Models Trained on Code. arXiv:2107.03374.

Hong, S., et al. (2023). MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework. arXiv:2308.00352.

Qian, C., et al. (2023). ChatDev: Communicative Agents for Software Development. arXiv:2307.07924.

Wang, L., et al. (2023). A Survey on Large Language Model based Autonomous Agents. arXiv:2308.11432.

Wu, Q., et al. (2023). AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation. arXiv:2308.08155.

Yang, J., et al. (2024). SWE-Agent: Agent-Computer Interfaces Enable Automated Software Engineering. arXiv:2405.15793.
