# MACDS Agents

## Overview

MACDS employs seven specialized agents organized in an authority hierarchy. Higher authority agents can override decisions of lower authority agents and resolve conflicts.

## Authority Hierarchy

| Level | Agent | Primary Responsibility |
|-------|-------|----------------------|
| 10 | ArchitectAgent | System design, invariants |
| 9 | ProductAgent | Requirements, acceptance |
| 8 | BuildTestAgent | Build, test execution |
| 8 | IntegratorAgent | Change integration |
| 7 | ReviewerAgent | Code review |
| 6 | InfraAgent | CI/CD, infrastructure |
| 5 | ImplementationAgent | Code generation |

## Agent Specifications

### ArchitectAgent

**Authority Level:** 10 (Highest)

**Responsibilities:**
- Define and maintain system architecture
- Establish and enforce architectural invariants
- Make design decisions with documented rationale
- Define API contracts between components
- Resolve design conflicts between agents
- Approve or reject final integration

**Owned Artifacts:**
- `ARCHITECTURE.md`
- `DESIGN_DECISIONS.log`
- `API_CONTRACTS.yaml`
- `CODING_STANDARDS.md`

**Input Contract:** ArchitectureInput
- Requirements list
- Existing architecture (optional)
- Constraints

**Output Contract:** ArchitectureOutput
- Components
- Invariants
- Design decisions
- API contracts

### ProductAgent

**Authority Level:** 9

**Responsibilities:**
- Define and refine requirements
- Maintain acceptance criteria
- Prioritize features
- Identify and track risks
- Validate deliverables against requirements

**Owned Artifacts:**
- `REQUIREMENTS.md`
- `RISK_REGISTER.md`

**Input Contract:** RequirementsInput
- User request
- Context
- Constraints

**Output Contract:** RequirementsOutput
- Requirements
- Acceptance criteria
- Constraints
- Risks

### BuildTestAgent

**Authority Level:** 8

**Responsibilities:**
- Execute build processes
- Run test suites
- Collect coverage metrics
- Perform security scans
- Report build/test results

**Input Contract:** BuildTestInput
- Source files
- Test files
- Build command
- Test command

**Output Contract:** BuildTestOutput
- Build success
- Test success
- Test results (passed, failed, skipped)
- Coverage metrics
- Security scan results

### IntegratorAgent

**Authority Level:** 8

**Responsibilities:**
- Merge approved changes
- Resolve merge conflicts
- Maintain branch hygiene
- Enforce integration policies

**Input Contract:** IntegrationInput
- Changes to merge
- Review approval status
- Build approval status
- Target branch

**Output Contract:** IntegrationOutput
- Success status
- Merged files
- Conflicts encountered
- Commit SHA

### ReviewerAgent

**Authority Level:** 7

**Responsibilities:**
- Review code for quality
- Check architecture compliance
- Enforce coding standards
- Identify security concerns
- Provide actionable feedback

**Input Contract:** CodeReviewInput
- Code diff
- Architecture constraints
- Coding standards
- Files to review

**Output Contract:** CodeReviewOutput
- Verdict (pass/fail/needs_revision)
- Violations
- Suggested patches
- Security concerns
- Quality score

### InfraAgent

**Authority Level:** 6

**Responsibilities:**
- Manage CI/CD pipelines
- Apply infrastructure as code
- Configure environments
- Orchestrate deployments

**Input Contract:** InfrastructureInput
- Operation type
- Target environment
- Configuration

**Output Contract:** InfrastructureOutput
- Success status
- Changes applied
- Logs
- Next steps

### ImplementationAgent

**Authority Level:** 5 (Lowest)

**Responsibilities:**
- Write code following API contracts
- Follow coding standards
- Implement features
- Fix bugs
- Apply review feedback

**Input Contract:** ImplementationInput
- Task description
- Architecture context
- API contract
- Coding standards
- Target files

**Output Contract:** ImplementationOutput
- Files created
- Files modified
- Files deleted
- Implementation notes
- API compliance status

## Agent Communication

### Direct Communication

Agents communicate through the orchestrator using typed contracts:

```
Agent A ---> Contract Output ---> Orchestrator ---> Contract Input ---> Agent B
```

### Escalation

When an agent encounters a conflict it cannot resolve:

1. Agent creates escalation request
2. Orchestrator routes to higher authority agent
3. Higher authority agent resolves conflict
4. Resolution propagated back

### Authority Override

Higher authority agents can override lower authority decisions:

```python
if agent_a.can_override(agent_b):
    # Agent A can override Agent B's decisions
    pass
```

## Extending Agents

### Creating a Custom Agent

```python
from macds.agents.base import BaseAgent, AgentConfig

class CustomAgent(BaseAgent):
    authority_level = 6
    
    @property
    def system_prompt(self):
        return "You are a custom agent..."
    
    @property
    def input_contract(self):
        return CustomInput
    
    @property
    def output_contract(self):
        return CustomOutput
    
    async def _execute_impl(self, input_data):
        # Implementation
        return output
```

### Registering the Agent

```python
from macds.agents.base import AgentRegistry

AgentRegistry.register(CustomAgent)
```
