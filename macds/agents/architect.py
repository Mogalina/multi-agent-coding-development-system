from typing import Optional
from datetime import datetime
import uuid

from macds.agents.base import BaseAgent, AgentConfig, AgentRegistry
from macds.core.contracts import (
    ArchitectureInput, ArchitectureOutput, Violation
)
from macds.core.artifacts import ArtifactType


class ArchitectAgent(BaseAgent[ArchitectureInput, ArchitectureOutput]):
    """
    Architect Agent - Highest authority for design decisions.
    
    Responsibilities:
    - Define system architecture
    - Enforce architectural invariants
    - Resolve design conflicts
    - Own ARCHITECTURE.md, DESIGN_DECISIONS.log
    """
    
    name = "ArchitectAgent"
    authority_level = 10
    description = "Defines architecture, enforces invariants, resolves conflicts"
    owned_artifacts = ["ARCHITECTURE.md", "DESIGN_DECISIONS.log", "API_CONTRACTS.yaml", "CODING_STANDARDS.md"]
    
    @property
    def system_prompt(self) -> str:
        return """You are the Architect Agent, the highest authority in the MACDS system.

Your responsibilities:
1. Define and maintain system architecture
2. Create and enforce architectural invariants
3. Resolve design conflicts between agents
4. Approve or reject proposed changes that affect architecture

Key principles:
- Architecture decisions are final unless you revise them
- All components must align with defined invariants
- Design for extensibility, maintainability, and testability
- Document ALL decisions in DESIGN_DECISIONS.log

When reviewing proposals:
- Check alignment with existing architecture
- Verify invariants are not violated
- Consider long-term implications
- Provide clear rationale for decisions

Output format: Always use structured contract output.
Never output unstructured text outside the contract schema."""
    
    @property
    def input_contract(self) -> type:
        return ArchitectureInput
    
    @property
    def output_contract(self) -> type:
        return ArchitectureOutput
    
    async def _execute_impl(self, input_data: ArchitectureInput) -> ArchitectureOutput:
        """Design or review architecture."""
        
        # Recall relevant architectural decisions
        memories = self.recall_relevant_memories(
            "architecture design pattern",
            limit=5
        )
        
        # Build architecture components from requirements
        components = self._design_components(input_data.requirements)
        invariants = self._define_invariants(components)
        decisions = self._make_design_decisions(input_data)
        api_contracts = self._define_api_contracts(components)
        
        # Store architecture in memory
        self.memory.remember(
            content={
                "components": [c["name"] for c in components],
                "invariants": invariants,
                "decision_count": len(decisions)
            },
            tags=["architecture", "design"]
        )
        
        return ArchitectureOutput(
            request_id=input_data.request_id,
            processing_agent=self.name,
            components=components,
            invariants=invariants,
            design_decisions=decisions,
            api_contracts=api_contracts,
            risks=self._identify_risks(components)
        )
    
    def _design_components(self, requirements: list[dict]) -> list[dict]:
        """Design system components based on requirements."""
        # Extract component needs from requirements
        components = []
        
        # Always include core components
        components.append({
            "name": "core",
            "responsibility": "Core infrastructure and shared utilities",
            "interfaces": ["logging", "configuration", "events"]
        })
        
        # Add components based on requirements
        for req in requirements:
            desc = req.get("description", "").lower()
            
            if "api" in desc or "endpoint" in desc:
                if not any(c["name"] == "api" for c in components):
                    components.append({
                        "name": "api",
                        "responsibility": "External API layer",
                        "interfaces": ["rest", "validation", "auth"]
                    })
            
            if "data" in desc or "storage" in desc or "persist" in desc:
                if not any(c["name"] == "storage" for c in components):
                    components.append({
                        "name": "storage",
                        "responsibility": "Data persistence layer",
                        "interfaces": ["crud", "query", "migration"]
                    })
            
            if "auth" in desc or "user" in desc or "permission" in desc:
                if not any(c["name"] == "auth" for c in components):
                    components.append({
                        "name": "auth",
                        "responsibility": "Authentication and authorization",
                        "interfaces": ["login", "verify", "permissions"]
                    })
        
        return components
    
    def _define_invariants(self, components: list[dict]) -> list[str]:
        """Define architectural invariants."""
        invariants = [
            "All inter-component communication must use defined interfaces",
            "No circular dependencies between components",
            "All public APIs must be versioned",
            "All operations must be idempotent where possible",
            "Error handling must be explicit and logged"
        ]
        
        # Add component-specific invariants
        for component in components:
            if component["name"] == "storage":
                invariants.append("All data modifications must be transactional")
            if component["name"] == "auth":
                invariants.append("Authentication tokens must expire within 24 hours")
            if component["name"] == "api":
                invariants.append("All API endpoints must validate input before processing")
        
        return invariants
    
    def _make_design_decisions(self, input_data: ArchitectureInput) -> list[dict]:
        """Make and document design decisions."""
        decisions = []
        
        # Decision on architecture style
        decisions.append({
            "id": f"DD-{datetime.now().strftime('%Y%m%d')}-001",
            "decision": "Use layered architecture with dependency injection",
            "rationale": "Promotes testability and loose coupling",
            "alternatives": ["Monolithic", "Microservices", "Event-driven"],
            "status": "accepted"
        })
        
        return decisions
    
    def _define_api_contracts(self, components: list[dict]) -> list[dict]:
        """Define API contracts for components."""
        contracts = []
        
        for component in components:
            for interface in component.get("interfaces", []):
                contracts.append({
                    "component": component["name"],
                    "interface": interface,
                    "version": "1.0",
                    "methods": []  # Would be filled with actual methods
                })
        
        return contracts
    
    def _identify_risks(self, components: list[dict]) -> list[str]:
        """Identify architectural risks."""
        risks = []
        
        if len(components) > 5:
            risks.append("Complex component graph may increase integration challenges")
        
        if any(c["name"] == "auth" for c in components):
            risks.append("Security-critical authentication component requires thorough review")
        
        return risks
    
    async def review_architecture_change(
        self,
        proposed_change: dict,
        current_architecture: dict
    ) -> dict:
        """Review a proposed architecture change."""
        violations = []
        approved = True
        
        # Check if change violates invariants
        invariants = current_architecture.get("invariants", [])
        for invariant in invariants:
            if self._change_violates_invariant(proposed_change, invariant):
                violations.append({
                    "type": "invariant_violation",
                    "invariant": invariant,
                    "change": proposed_change
                })
                approved = False
        
        return {
            "approved": approved,
            "violations": violations,
            "required_modifications": [] if approved else ["Revise to comply with invariants"],
            "reviewed_by": self.name,
            "reviewed_at": datetime.now().isoformat()
        }
    
    def _change_violates_invariant(self, change: dict, invariant: str) -> bool:
        """Check if a change violates an invariant."""
        # Simplified check - in production, use semantic analysis
        return False


# Register the agent
AgentRegistry.register(ArchitectAgent)
